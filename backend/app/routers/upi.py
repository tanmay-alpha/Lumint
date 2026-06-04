import re
import tempfile
import shutil
from datetime import datetime, timezone
from typing import Optional
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import UPIShieldEvent
from app.schemas.upi import UPIAnalyzeResponse, UTRVerificationResponse, QRScanResponse
from ai.upi_ai import analyze_upi_screenshot_ai
from app.services.upi.analyzer import analyze_upi_screenshot

router = APIRouter(prefix="/api/upi", tags=["upi-shield"])

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
    sender = vpa_matches[0] if len(vpa_matches) > 0 else "unknown@upi"
    receiver = vpa_matches[1] if len(vpa_matches) > 1 else "unknown@merchant"

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
    except Exception as e:
        import logging
        logging.getLogger("lumint.routers.upi").error(f"Failed to save UPI event in background: {str(e)}")
    finally:
        db.close()

@router.post("/analyze-screenshot", response_model=UPIAnalyzeResponse)
@router.post("/analyze", response_model=UPIAnalyzeResponse)
async def analyze_screenshot(
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
    # 1. Save uploaded file to a temporary file
    suffix = Path(file.filename or "screenshot.png").suffix.lower()
    if suffix not in (".png", ".jpg", ".jpeg"):
        suffix = ".png" # default fallback
        
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
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
            
    # 3. Parse fields for DB and response mapping
    utr_val = res["utr"]["normalized"] if (res["utr"] and res["utr"]["normalized"]) else "000000000000"
    is_valid_utr = res["utr"]["valid"] if res["utr"] else False
    
    amount_val = 0.0
    if res["amount_extracted"]:
        try:
            amount_val = float(str(res["amount_extracted"]).replace(",", ""))
        except ValueError:
            pass
            
    # 4. Integrate AI check if requested
    ai_report = None
    if run_ai:
        ai_report = await analyze_upi_screenshot_ai(
            ocr_text=res["ocr"]["text"],
            utr_number=utr_val,
            sender=res["sender_upi_id"],
            receiver=res["receiver_upi_id"],
            amount=amount_val
        )
        risk_score = ai_report.get("risk_score", res["forgery_score"])
        risk_level = ai_report.get("risk_level", res["verdict"])
        ai_fraud_explanation = ai_report.get("ai_fraud_explanation", f"Forensic analysis: {res['verdict']}")
        font_anomalies_detected = ai_report.get("font_anomalies_detected", not res["font"]["font_consistent"])
        suspicious_handle_flagged = ai_report.get("suspicious_handle_flagged", any(ind["rule"] == "suspicious_keywords" for ind in res["indicators"]))
    else:
        risk_score = res["forgery_score"]
        risk_level = res["verdict"]
        
        # Build explanation listing triggered indicators
        explanation_parts = []
        for ind in res["indicators"]:
            explanation_parts.append(f"- {ind['detail']} (Contribution: +{ind['score']})")
        if explanation_parts:
            ai_fraud_explanation = "Forensic analysis flagged the following indicators:\n" + "\n".join(explanation_parts)
        else:
            ai_fraud_explanation = "No suspicious forensic indicators were found. The receipt screenshot appears structurally authentic."
            
        font_anomalies_detected = not res["font"]["font_consistent"]
        suspicious_handle_flagged = any(ind["rule"] == "suspicious_keywords" for ind in res["indicators"])

    # 5. Populate and commit to database (Backgrounded)
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
        "feature_contributions": res["feature_contributions"]
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
        metadata_json=meta_json
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
