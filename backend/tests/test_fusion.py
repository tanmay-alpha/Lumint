from fastapi.testclient import TestClient
from app.main import app
from app.core.fusion import compute_lumint_score
from app.schemas.document import DocumentAnalysisResponse
from app.schemas.phishing import PhishingCheckResponse
from app.routers import documents, phishing

client = TestClient(app)

def test_fusion_all_modalities_weighted_score():
    doc_res = {"risk_score": 80}
    phish_res = {"risk_score": 60}
    upi_res = {"risk_score": 40}
    
    # Weights: doc=0.35, phish=0.35, upi=0.30
    # Expected: 80*0.35 + 60*0.35 + 40*0.30 = 28 + 21 + 12 = 61
    result = compute_lumint_score(doc_res, phish_res, upi_res)
    assert result["unified_score"] == 61
    assert result["risk_level"] == "SUSPICIOUS"
    assert result["dominant_signal"] == "document"
    assert result["scores"]["document"] == 80.0
    assert result["scores"]["phishing"] == 60.0
    assert result["scores"]["upi"] == 40.0

def test_fusion_partial_inputs_renormalizes_weights():
    doc_res = {"risk_score": 80}
    phish_res = {"risk_score": 40}
    
    # Active weights: doc=0.35, phish=0.35 -> Normalized: doc=0.5, phish=0.5
    # Expected: 80*0.5 + 40*0.5 = 60
    result = compute_lumint_score(doc_result=doc_res, phish_result=phish_res)
    assert result["unified_score"] == 60
    assert result["risk_level"] == "SUSPICIOUS"
    assert result["weights"]["document"] == 0.5
    assert result["weights"]["phishing"] == 0.5
    assert result["weights"]["upi"] == 0.0

def test_fusion_empty_request():
    result = compute_lumint_score()
    assert result["unified_score"] == 0
    assert result["risk_level"] == "CLEAN"
    assert result["dominant_signal"] is None

def test_fusion_correlation_shared_high_risk():
    doc_res = {"risk_score": 75}
    phish_res = {"risk_score": 85}
    
    result = compute_lumint_score(doc_result=doc_res, phish_result=phish_res)
    flags = result["correlation_flags"]
    
    assert any(f["flag"] == "shared_high_risk" for f in flags)

def test_fusion_correlation_doc_url_alignment():
    doc_res = {
        "risk_score": 60,
        "indicators": [
            {"rule": "embedded_suspicious_url", "score": 25, "detail": "Document has raw IP links"}
        ]
    }
    phish_res = {"risk_score": 55}
    
    result = compute_lumint_score(doc_result=doc_res, phish_result=phish_res)
    flags = result["correlation_flags"]
    assert any(f["flag"] == "doc_url_alignment" for f in flags)

def test_fusion_correlation_payment_fraud_alignment():
    upi_res = {"risk_score": 60}
    phish_res = {"risk_score": 70}
    
    result = compute_lumint_score(upi_result=upi_res, phish_result=phish_res)
    flags = result["correlation_flags"]
    assert any(f["flag"] == "payment_fraud_alignment" for f in flags)

def test_fusion_correlation_campaign_escalation():
    phish_res = {
        "risk_score": 65,
        "phishing_fingerprint": {"campaign_id": "camp-92", "campaign": "PhishGate"}
    }
    
    result = compute_lumint_score(phish_result=phish_res)
    flags = result["correlation_flags"]
    assert any(f["flag"] == "campaign_escalation" for f in flags)

def test_fusion_endpoint():
    payload = {
        "document_result": {"risk_score": 90},
        "phishing_result": {"risk_score": 80},
        "upi_result": {"risk_score": 50},
        "weights": {"document": 0.40, "phishing": 0.40, "upi": 0.20}
    }
    # Expected: 90*0.4 + 80*0.4 + 50*0.2 = 36 + 32 + 10 = 78
    response = client.post("/api/fusion/score", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["unified_score"] == 78
    assert data["risk_level"] == "HIGH"
    assert "scores" in data
    assert "weights" in data
    assert "correlation_flags" in data
    assert "explanation" in data

def test_existing_doc_endpoint_schema_still_imports():
    assert DocumentAnalysisResponse is not None
    assert documents.router is not None

def test_existing_phishing_endpoint_schema_still_imports():
    assert PhishingCheckResponse is not None
    assert phishing.router is not None
