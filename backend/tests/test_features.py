import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import get_db, Base

# Set up test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_temp.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Re-create database schemas for testing
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

def test_upi_analyze_screenshot():
    # Test valid screenshot analysis - use a minimal valid PNG (24x1px)
    # We cannot use fake_png_data as the new validator catches invalid PNGs
    png_header = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x18\x00\x00\x00\x01\x08\x02\x00\x00\x00K\xcc\xf9\xfc\x00\x00\x00\x0fIDATx\x9cc\xfc\xff\xff?\x035\x00\x00\xd4\xbd\x02\xff\xcf\x15|\x0c\x00\x00\x00\x00IEND\xaeB`\x82'
    response = client.post(
        "/api/upi/analyze-screenshot",
        files={"file": ("screenshot.png", png_header)},
        data={"custom_ocr": "Google Pay Payment successful To merchant@upi From sender@upi UTR: 398273645192 Amount Rs 5,000.00"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["utr_number"] == "398273645192"
    assert data["amount"] == 5000.0
    assert data["is_valid_utr"] is True

def test_upi_verify_utr_valid():
    response = client.get("/api/upi/verify-utr/987654321012")
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] is True
    assert data["risk_score"] < 50

def test_upi_verify_utr_invalid():
    response = client.get("/api/upi/verify-utr/123")
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] is False
    assert data["risk_score"] > 50

def test_upi_decode_qr():
    response = client.post(
        "/api/upi/decode-qr",
        data={"qr_url": "upi://pay?pa=scam.handle@okaxis&pn=SuspiciousMerchant&am=50000.00"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["pa"] == "scam.handle@okaxis"
    assert data["is_suspicious_handle"] is True
    assert data["risk_level"] == "HIGH"

def test_case_management():
    # 1. Create a case
    create_resp = client.post(
        "/api/cases",
        json={
            "title": "Suspected UPI Receipt Spoofing campaign",
            "description": "Investigating several fake PhonePe receipts pointing to target.merchant@okaxis",
            "status": "OPEN",
            "severity": "CRITICAL",
            "assigned_analyst": "Dr. Sarah Connor"
        }
    )
    assert create_resp.status_code == 200
    case_data = create_resp.json()
    case_id = case_data["id"]
    assert case_id is not None
    assert case_data["title"] == "Suspected UPI Receipt Spoofing campaign"

    # 2. Get case
    get_resp = client.get(f"/api/cases/{case_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["assigned_analyst"] == "Dr. Sarah Connor"

    # 3. Update case (analyst notes)
    update_resp = client.put(
        f"/api/cases/{case_id}",
        json={"analyst_notes": "Identified digitally-modified fonts in OCR layer of evidence."}
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["analyst_notes"] == "Identified digitally-modified fonts in OCR layer of evidence."

    # 4. Attach evidence
    evidence_resp = client.post(
        f"/api/cases/{case_id}/evidence",
        json={"type": "upi_event", "utr": "398273645192", "risk": "HIGH"}
    )
    assert evidence_resp.status_code == 200
    assert len(evidence_resp.json()["saved_evidence"]) == 1

def test_threat_feed():
    # 1. Create threat alert
    alert_resp = client.post(
        "/api/threats",
        json={
            "indicator_type": "vpa",
            "value": "hacker@okaxis",
            "source": "honeypot",
            "severity": "HIGH",
            "description": "UPI VPA linked to multiple rapid transaction queries",
            "mitigation_strategy": "Flag in receiver lookups"
        }
    )
    assert alert_resp.status_code == 200
    alert_data = alert_resp.json()
    assert alert_data["indicator_type"] == "vpa"
    assert alert_data["value"] == "hacker@okaxis"

    # 2. Retrieve alerts list
    list_resp = client.get("/api/threats")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 1
