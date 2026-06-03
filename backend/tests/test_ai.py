import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_document_ai_endpoint_success():
    payload = {
        "original_filename": "invoice_forgery_test.pdf",
        "risk_score": 85,
        "risk_level": "HIGH",
        "indicators": [
            {"rule": "Metadata Spoofing", "score": 45, "detail": "Modified creator"},
            {"rule": "ELA Anomaly", "score": 40, "detail": "High frequency ELA"},
        ],
        "metadata": {"author": "Spoofed Author", "file_size": 20480},
    }

    # Test the API endpoint. We mock the actual LLM call to guarantee returns
    mock_llm_response = {
        "verdict": "FRAUDULENT",
        "confidence": 92,
        "anomalies": ["EXIF metadata mismatch", "ELA pixel anomalies"],
        "attack_type": "Invoice spoofing with active metadata override",
        "analyst_note": "A highly sophisticated invoice fraud attempt.",
        "recommended_action": "Reject invoice and flag recipient account.",
        "model_used": "llama-3.3-70b-versatile",
        "latency_ms": 120,
    }

    with patch("app.routers.ai.analyze_document_ai", return_value=mock_llm_response):
        r = client.post("/api/ai/document", json=payload)
        assert r.status_code == 200
        data = r.json()
        assert data["verdict"] == "FRAUDULENT"
        assert data["confidence"] == 92
        assert data["recommended_action"] == "Reject invoice and flag recipient account."
        assert "model_used" in data


def test_phishing_ai_endpoint_success():
    payload = {
        "url": "http://secure-chase-auth-login.com/signin",
        "normalized_url": "secure-chase-auth-login.com/signin",
        "domain": "secure-chase-auth-login.com",
        "risk_score": 90,
        "risk_level": "HIGH",
        "triggered_rules": [
            {"rule": "Keywords in path", "score": 30, "detail": "Contains 'signin'"}
        ],
        "domain_similarity_matches": [
            {"bank": "Chase Bank", "similarity": 0.85}
        ],
    }

    mock_llm_response = {
        "verdict": "PHISHING",
        "target_brand": "Chase Bank",
        "attack_vector": "credential_harvest",
        "confidence": 95,
        "analyst_note": "Domain typosquatting Chase Bank.",
        "ioc_summary": ["secure-chase-auth-login.com"],
        "model_used": "llama-3.3-70b-versatile",
        "latency_ms": 80,
    }

    with patch("app.routers.ai.analyze_phishing_ai", return_value=mock_llm_response):
        r = client.post("/api/ai/phishing", json=payload)
        assert r.status_code == 200
        data = r.json()
        assert data["verdict"] == "PHISHING"
        assert data["target_brand"] == "Chase Bank"
        assert data["attack_vector"] == "credential_harvest"


def test_campaign_ai_endpoint_success():
    payload = {
        "campaign_id": "cmp-test-123",
        "event_count": 3,
        "risk_level": "HIGH",
        "avg_risk_score": 84.5,
        "common_indicators": ["Metadata Modification", "ELA anomaly"],
        "common_keywords": ["invoice", "bank transfer"],
        "events": [
            {
                "event_id": "evt-1",
                "doc_id": "doc-1",
                "source_type": "DOCUMENT",
                "label": "invoice1.pdf",
                "risk_score": 85,
                "risk_level": "HIGH",
                "document_type_hint": "invoice",
                "created_at": "2026-06-02T12:00:00Z",
            }
        ],
    }

    mock_llm_response = {
        "campaign_name": "Coordinated Invoice Spoofing Campaign",
        "threat_level": "HIGH",
        "pattern_summary": "Campaign targets accounting personnel using spoofed invoice metadata.",
        "estimated_scale": "Medium (3 event clusters)",
        "analyst_brief": "Coordinated invoice spoofing campaign utilizing identical PDF creator signatures.",
        "recommended_actions": ["Block domain", "Alert accounting staff"],
        "ttps": ["T1036 (Masquerading)", "T1566 (Phishing)"],
        "model_used": "llama-3.3-70b-versatile",
        "latency_ms": 250,
    }

    with patch("app.routers.ai.analyze_campaign_ai", return_value=mock_llm_response):
        r = client.post("/api/ai/campaign", json=payload)
        assert r.status_code == 200
        data = r.json()
        assert data["campaign_name"] == "Coordinated Invoice Spoofing Campaign"
        assert data["threat_level"] == "HIGH"
        assert "estimated_scale" in data


def test_ai_fallback_live():
    # If the LLM module fails or is not patched, the endpoint should trigger its fallback automatically
    payload = {
        "original_filename": "invoice.pdf",
        "risk_score": 90,
        "risk_level": "HIGH",
        "indicators": [],
    }
    r = client.post("/api/ai/document", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert "verdict" in data
    assert "confidence" in data
    assert "model_used" in data
