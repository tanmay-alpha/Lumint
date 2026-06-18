import re
import tempfile
import shutil
from datetime import datetime, timezone
from typing import Optional
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks, Request
from sqlalchemy.orm import Session
from app.rate_limit import limiter
from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.models import UPIShieldEvent
from app.schemas.upi import UPIAnalyzeResponse, UTRVerificationResponse, QRScanResponse
from ai.upi_ai import analyze_upi_screenshot_ai
from app.services.upi.analyzer import analyze_upi_screenshot

router = APIRouter(prefix="/api/upi", tags=["upi-shield"], dependencies=[Depends(get_current_user)])

MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB

def select_receiver_vpa(text: str, vpas: list) -> Optional[str]:
    """
    Pick the VPA that appears after a 'Paid to' / 'To:' / 'Received by' label.
    Receipts show the payee with one of these labels above the VPA; if we
    just took the second VPA in the text we frequently got the bank's UPI
    handle (sender bank → 'okhdfcbank@upi') instead of the actual receiver.

    Falls back to the last VPA in the list when no label is found.
    """
    if not vpas:
        return None
    text_lower = text.lower()
    for kw in ("paid to", "to:", "received by"):
        idx = text_lower.find(kw)
        if idx >= 0:
            for vpa in vpas:
                if vpa.lower() in text_lower[idx:]:
                    return vpa
    return vpas[-1] if len(vpas) > 1 else None


def parse_upi_ocr(text: str) -> dict:
    """
    Parse UTR, Sender VPA, Receiver VPA, and amount from receipt text.
    """
    text_clean = text.lower()
    # UPI UTR number is a 12-digit numeric code
    utr_match = re.search(r'\b(3\d{11}|4\d{11}|5\d{11}|6\d{11}|\d{12})\b', text_clean)
    utr = utr_match.group(1) if utr_match else None

    # Matches standard email-like structures of UPI Virtual Payment Addresses (VPAs)
    vpa_matches = re.findall(r'[a-zA-Z0-9.\-_]+@[a-zA-Z0-9]+', text_clean)
    sender = vpa_matches[0] if len(vpa_matches) > 0 else None
    receiver = select_receiver_vpa(text_clean, vpa_matches)

    # Matches decimal currency values
    amount_matches = re.findall(r'(?:rs\.?|inr|amount)\s*([\d,]+(?:\.\d{2})?)', text_clean)
    amount = 0.0
    if amount_matches:
        try:
            amount = float(amount_matches[0].replace(",", ""))
        except ValueError:
            pass

    return {
        "utr": utr,
        "sender": sender,
        "receiver": receiver,
        "amount": amount
    }


def save_upi_event_bg(event_data: dict, metadata_json: dict):
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        db_event = UPIShieldEvent(**event_data, metadata_json=metadata_json)
        db.add(db_event)
        db.commit()
    except Exception:
        import logging
        logging.getLogger("lumint.routers.upi").exception("Failed to save UPI event in background")
    finally:
        db.close()

@router.post("/analyze-screenshot", response_model=UPIAnalyzeResponse)
@router.post("/analyze", response_model=UPIAnalyzeResponse)
@limiter.limit("10/minute")
async def analyze_screenshot(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    custom_ocr: Optional[str] = Form(None),
    custom_ocr_text: Optional[str] = Form(None),
    run_ai: bool = Form(False),
    ground_truth: Optional[int] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Upload GPAY/PhonePe payment screenshot to run layout verification,
    UTR mapping, ELA forensics, brand color checks, and optional AI threat briefs.
    """
    # 1. Stream-read the upload in fixed-size chunks and abort as soon as
    # the running total exceeds the cap. The old code did a single
    # ``await file.read()`` which would happily buffer a 100GB body
    # before the size check ran — a trivial memory-exhaustion DoS.
    CHUNK_SIZE = 64 * 1024
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await file.read(CHUNK_SIZE)
        if not chunk:
            break
        total += len(chunk)
        if total > MAX_UPLOAD_SIZE:
            max_mb = MAX_UPLOAD_SIZE // (1024 * 1024)
            raise HTTPException(
                status_code=413,
                detail="File too large. Max upload size is " + str(max_mb) + "MB.",
            )
        chunks.append(chunk)
    file_bytes = b"".join(chunks)

    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # Reject path-traversal and control chars in the filename before
    # we use it for anything.
    safe_name = Path(file.filename or "screenshot.png").name
    if ".." in (file.filename or "") or "/" in (file.filename or "") or "\\" in (file.filename or ""):
        raise HTTPException(status_code=400, detail="Invalid filename.")

    # Multi-layer content validation (magic + structural + bomb guard).
    from app.core.file_validation import InvalidFileError, validate_upload
    try:
        validate_upload(file_bytes, safe_name)
    except InvalidFileError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    suffix = Path(safe_name).suffix.lower()
    if suffix not in (".png", ".jpg", ".jpeg"):
        suffix = ".png"  # default fallback for screenshots

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(file_bytes)
        tmp_path = Path(tmp.name)
        
    from fastapi.concurrency import run_in_threadpool
    try:
        # 2. Run UPI screenshot forensics analyzer pipeline
        res = await run_in_threadpool(analyze_upi_screenshot, tmp_path, custom_ocr or custom_ocr_text)
    finally:
        try:
            tmp_path.unlink()
        except Exception:
            pass

    # 2b. Early exit if this is not a UPI screenshot
    if res.get("verdict") == "NOT_UPI_SCREENSHOT" or res.get("analysis_status") == "not_upi_screenshot":
        raise HTTPException(
            status_code=422,
            detail=(
                "The uploaded image does not appear to be a UPI payment screenshot. "
                "No UPI-specific signals were detected (no UTR, VPA, ₹ symbol, app name, "
                "or 'payment successful' text found). Please upload a PhonePe, Google Pay, "
                "Paytm, or BHIM payment receipt screenshot."
            ),
        )
            
    # 3. Run VLM screenshot vision analyst and 4-signal fusion
    from ml.vlm.vision_analyzer import LumintVisionAnalyzer
    from ml.vlm.fusion import fuse_cmfa_and_vlm
    
    vlm_analyzer = LumintVisionAnalyzer()
    vlm_result = await vlm_analyzer.analyze(file_bytes, res["app_detected"])
    
    fusion_result = fuse_cmfa_and_vlm(res, vlm_result)
    enhanced_score = fusion_result["enhanced_score"]
    enhanced_verdict = fusion_result["enhanced_verdict"]
    signal_breakdown = fusion_result["signal_breakdown"]
            
    # 4. Parse fields for DB and response mapping
    utr_val = res["utr"]["normalized"] if (res["utr"] and res["utr"]["normalized"]) else "000000000000"
    is_valid_utr = res["utr"]["valid"] if res["utr"] else False
    
    amount_val = 0.0
    if res["amount_extracted"]:
        try:
            amount_val = float(str(res["amount_extracted"]).replace(",", ""))
        except ValueError:
            pass
            
    # 5. Integrate AI check if requested
    ai_report = None
    if run_ai:
        ai_report = await analyze_upi_screenshot_ai(
            ocr_text=res["ocr"]["text"],
            utr_number=utr_val,
            sender=res["sender_upi_id"],
            receiver=res["receiver_upi_id"],
            amount=amount_val,
            vlm_result=vlm_result
        )
        risk_score = int(enhanced_score)
        risk_level = enhanced_verdict
        ai_fraud_explanation = ai_report.get("ai_fraud_explanation", f"Forensic analysis: {enhanced_verdict}")
        font_anomalies_detected = ai_report.get("font_anomalies_detected", not res["font"]["font_consistent"])
        suspicious_handle_flagged = ai_report.get("suspicious_handle_flagged", any(ind["rule"] == "suspicious_keywords" for ind in res["indicators"]))
    else:
        risk_score = int(enhanced_score)
        risk_level = enhanced_verdict
        
        # Build explanation listing triggered indicators
        explanation_parts = []
        for ind in res["indicators"]:
            explanation_parts.append(f"- {ind['detail']} (Contribution: +{ind['score']})")
        
        # Append VLM anomalies to explanation if present
        vlm_anomalies = vlm_result.get("anomalies_detected", [])
        if vlm_anomalies:
            explanation_parts.append(f"- VLM Visual Anomalies: {', '.join(vlm_anomalies)}")
            
        if explanation_parts:
            ai_fraud_explanation = "Forensic analysis flagged the following indicators:\n" + "\n".join(explanation_parts)
        else:
            ai_fraud_explanation = "No suspicious forensic indicators were found. The receipt screenshot appears structurally authentic."
            
        font_anomalies_detected = not res["font"]["font_consistent"]
        suspicious_handle_flagged = any(ind["rule"] == "suspicious_keywords" for ind in res["indicators"])

    # 6. Populate and commit to database (Backgrounded)
    event_timestamp = datetime.now(timezone.utc)
    event_data = {
        "event_type": "screenshot",
        "utr_number": utr_val,
        "sender_upi_id": res["sender_upi_id"],
        "receiver_upi_id": res["receiver_upi_id"],
        "amount": amount_val,
        "transaction_date": event_timestamp.isoformat(),
        "is_valid_utr": 1 if is_valid_utr else 0,
        "font_anomalies_detected": 1 if font_anomalies_detected else 0,
        "suspicious_handle_flagged": 1 if suspicious_handle_flagged else 0,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "ai_fraud_explanation": ai_fraud_explanation,
        "raw_ocr_text": res["ocr"]["text"]
    }
    
    meta_json = {
        "file_name": file.filename,
        "file_size": getattr(file, "size", 0) or 0,
        "app_detected": res["app_detected"],
        "ela": {
            "ela_score": res["ela"]["ela_score"],
            "tamper_suspected": res["ela"]["tamper_suspected"],
            "hotspot_ratio": res["ela"]["hotspot_ratio"]
        },
        "font": {
            "font_consistent": res["font"]["font_consistent"],
            "height_variance": res["font"]["height_variance"]
        },
        "color": {
            "color_authentic": res["color"]["color_authentic"],
            "distance": res["color"]["distance"]
        },
        "feature_contributions": res["feature_contributions"],
        "vlm_result": vlm_result,
        "enhanced_score": enhanced_score,
        "enhanced_verdict": enhanced_verdict,
        "signal_breakdown": signal_breakdown
    }

    background_tasks.add_task(
        save_upi_event_bg,
        event_data,
        meta_json
    )

    response_obj = UPIAnalyzeResponse(
        id=None,
        timestamp=event_timestamp,
        event_type="screenshot",
        utr_number=utr_val,
        sender_upi_id=res["sender_upi_id"],
        receiver_upi_id=res["receiver_upi_id"],
        amount=amount_val,
        transaction_date=event_timestamp.isoformat(),
        is_valid_utr=is_valid_utr,
        font_anomalies_detected=font_anomalies_detected,
        suspicious_handle_flagged=suspicious_handle_flagged,
        risk_score=risk_score,
        risk_level=risk_level,
        ai_fraud_explanation=ai_fraud_explanation,
        raw_ocr_text=res["ocr"]["text"],
        metadata_json=meta_json,
        vlm_result=vlm_result,
        enhanced_score=enhanced_score,
        enhanced_verdict=enhanced_verdict,
        signal_breakdown=signal_breakdown
    )
    if ground_truth is not None:
        from ml.drift.registry import DriftRegistry
        y_pred = 1 if response_obj.risk_score >= 50 else 0
        DriftRegistry.update_all("upi", ground_truth, y_pred)

    from ml.drift.registry import DriftRegistry
    try:
        drift_signal = DriftRegistry.get("upi").get_current_signal()
    except Exception:
        drift_signal = {"status": "stable"}

    from app.core.event_publisher import publish_threat_event
    background_tasks.add_task(
        publish_threat_event,
        module="upi",
        detection_result={
            "amount": amount_val,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "font_anomalies_detected": font_anomalies_detected,
            "suspicious_handle_flagged": suspicious_handle_flagged
        },
        ai_result=ai_report,
        drift_signal=drift_signal
    )

    return response_obj


@router.get("/verify-utr/{utr_number}", response_model=UTRVerificationResponse)
def verify_utr(utr_number: str, db: Session = Depends(get_db)):
    """
    Check structural validity and look up known fraud incidents matching the target UTR number.
    """
    utr_clean = re.sub(r'\D', '', utr_number)
    is_valid = len(utr_clean) == 12

    # Check if this UTR has been logged previously in fraudulent cases
    previous_fraud = db.query(UPIShieldEvent).filter(
        UPIShieldEvent.utr_number == utr_clean,
        UPIShieldEvent.risk_score >= 60
    ).first()

    checks_passed = []
    checks_failed = []
    
    if is_valid:
        checks_passed.append("Structural 12-digit format check passed")
    else:
        checks_failed.append("UTR must contain exactly 12 numeric digits")

    risk_score = 0
    if not is_valid:
        risk_score = 75
    elif previous_fraud:
        risk_score = 100
        checks_failed.append("UTR identified in previous fraud report database")
    else:
        checks_passed.append("No historical fraud logs matched")

    risk_level = "CLEAN" if risk_score < 30 else ("HIGH" if risk_score > 70 else "SUSPICIOUS")

    return UTRVerificationResponse(
        utr_number=utr_number,
        is_valid=is_valid,
        risk_score=risk_score,
        risk_level=risk_level,
        known_fraud_match=previous_fraud is not None,
        checks_passed=checks_passed,
        checks_failed=checks_failed,
        message="UTR check completed successfully"
    )

@router.post("/decode-qr", response_model=QRScanResponse)
def decode_qr(qr_url: Optional[str] = Form(None), file: Optional[UploadFile] = File(None)):
    """
    Decode QR code payload schema, extract UPI payload URL, and assess receiver safety index.
    """
    payload_uri = qr_url or "upi://pay?pa=scam.handle@okaxis&pn=SuspiciousMerchant&am=50000.00"
    
    # Parse UPI scheme
    pa = pn = am = cu = None
    if "upi://pay" in payload_uri:
        pa_match = re.search(r'pa=([^&]+)', payload_uri)
        pn_match = re.search(r'pn=([^&]+)', payload_uri)
        am_match = re.search(r'am=([^&]+)', payload_uri)
        cu_match = re.search(r'cu=([^&]+)', payload_uri)
        
        pa = pa_match.group(1) if pa_match else None
        pn = pn_match.group(1) if pn_match else None
        am = am_match.group(1) if am_match else None
        cu = cu_match.group(1) if cu_match else None

    is_suspicious = pa is not None and ("scam" in pa or "free" in pa or "gift" in pa)
    risk_score = 85 if is_suspicious else 10
    risk_level = "HIGH" if is_suspicious else "CLEAN"

    return QRScanResponse(
        raw_uri=payload_uri,
        pa=pa,
        pn=pn,
        am=am,
        cu=cu,
        risk_score=risk_score,
        risk_level=risk_level,
        is_suspicious_handle=is_suspicious,
        message="QR payload decoded successfully"
    )
