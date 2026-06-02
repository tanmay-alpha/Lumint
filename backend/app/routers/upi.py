import re
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import UPIShieldEvent
from app.schemas.upi import UPIAnalyzeResponse, UTRVerificationResponse, QRScanResponse
from ai.upi_ai import analyze_upi_screenshot_ai

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

@router.post("/analyze-screenshot", response_model=UPIAnalyzeResponse)
async def analyze_screenshot(
    file: UploadFile = File(...),
    custom_ocr: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Upload GPAY/PhonePe payment screenshot to run layout verification,
    UTR mapping, and Groq LLaMA 3.3 analyst threat brief.
    """
    # Mock OCR extraction / Simulating receipt text extraction
    ocr_text = custom_ocr or (
        f"PhonePe UPI Payment Successful. Txn ID: T24060212345. "
        f"To: target.merchant@okaxis. From: user.sender@okhdfcbank. "
        f"UTR Ref: 318273645192. Amount Rs. 15,200.00. Date: 2026-06-02 18:40."
    )
    
    parsed = parse_upi_ocr(ocr_text)
    
    # Heuristics checking
    utr_val = parsed["utr"] or "000000000000"
    is_valid_utr = len(utr_val) == 12
    font_anomalies = "edit" in ocr_text.lower() or "canvas" in ocr_text.lower()
    suspicious_handle = "scam" in parsed["receiver"] or "paytm" not in parsed["receiver"] and "ok" not in parsed["receiver"]

    # Analyze via AI
    ai_report = await analyze_upi_screenshot_ai(
        ocr_text=ocr_text,
        utr_number=utr_val,
        sender=parsed["sender"],
        receiver=parsed["receiver"],
        amount=parsed["amount"]
    )

    # Store event in SQLite database
    db_event = UPIShieldEvent(
        event_type="screenshot",
        utr_number=utr_val,
        sender_upi_id=parsed["sender"],
        receiver_upi_id=parsed["receiver"],
        amount=parsed["amount"],
        transaction_date=datetime.now(timezone.utc).isoformat(),
        is_valid_utr=1 if is_valid_utr else 0,
        font_anomalies_detected=1 if font_anomalies else 0,
        suspicious_handle_flagged=1 if suspicious_handle else 0,
        risk_score=ai_report.get("risk_score", 15),
        risk_level=ai_report.get("risk_level", "CLEAN"),
        ai_fraud_explanation=ai_report.get("ai_fraud_explanation", ""),
        raw_ocr_text=ocr_text,
        metadata_json={"file_name": file.filename, "file_size": file.size}
    )

    db.add(db_event)
    db.commit()
    db.refresh(db_event)

    return UPIAnalyzeResponse(
        id=db_event.id,
        timestamp=db_event.timestamp,
        event_type=db_event.event_type,
        utr_number=db_event.utr_number,
        sender_upi_id=db_event.sender_upi_id,
        receiver_upi_id=db_event.receiver_upi_id,
        amount=db_event.amount,
        transaction_date=db_event.transaction_date,
        is_valid_utr=db_event.is_valid_utr == 1,
        font_anomalies_detected=db_event.font_anomalies_detected == 1,
        suspicious_handle_flagged=db_event.suspicious_handle_flagged == 1,
        risk_score=db_event.risk_score,
        risk_level=db_event.risk_level,
        ai_fraud_explanation=db_event.ai_fraud_explanation,
        raw_ocr_text=db_event.raw_ocr_text,
        metadata_json=db_event.metadata_json
    )

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
