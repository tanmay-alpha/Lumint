from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime

class UPIAnalyzeResponse(BaseModel):
    id: Optional[int] = None
    timestamp: datetime
    event_type: str
    utr_number: Optional[str] = None
    sender_upi_id: Optional[str] = None
    receiver_upi_id: Optional[str] = None
    amount: Optional[float] = None
    transaction_date: Optional[str] = None
    is_valid_utr: bool
    font_anomalies_detected: bool
    suspicious_handle_flagged: bool
    risk_score: int
    risk_level: str
    ai_fraud_explanation: Optional[str] = None
    raw_ocr_text: Optional[str] = None
    metadata_json: Optional[Any] = None

class UTRVerificationRequest(BaseModel):
    utr_number: str

class UTRVerificationResponse(BaseModel):
    utr_number: str
    is_valid: bool
    risk_score: int
    risk_level: str
    known_fraud_match: bool
    checks_passed: List[str]
    checks_failed: List[str]
    message: str

class QRScanResponse(BaseModel):
    raw_uri: str
    pa: Optional[str] = None  # Payee Address (UPI ID)
    pn: Optional[str] = None  # Payee Name
    am: Optional[str] = None  # Transaction Amount
    cu: Optional[str] = None  # Currency
    risk_score: int
    risk_level: str
    is_suspicious_handle: bool
    message: str
