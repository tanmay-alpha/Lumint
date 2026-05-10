"""
Integration tests: URL events flow through PhishShield → Fraud DNA → Dashboard.
"""
import pytest
from fastapi.testclient import TestClient
import app.services.fraud_dna.store as dna_store
from app.main import app

client = TestClient(app)

CLEAN_URL = "https://hdfcbank.com"
PHISHING_URL = "http://hdfc-bank-verify-kyc-login.com/otp-update"


@pytest.fixture(autouse=True)
def isolated_store(tmp_path, monkeypatch):
    """Each test gets a fresh empty store."""
    fake_store = tmp_path / "fraud_events.json"
    monkeypatch.setattr(dna_store, "STORE_PATH", fake_store)
    yield


def test_clean_url_stays_clean():
    r = client.post("/api/phishing/check", json={"url": CLEAN_URL})
    assert r.status_code == 200
    data = r.json()
    assert data["risk_level"] == "CLEAN"
    assert data["risk_score"] <= 30


def test_phishing_url_is_high_risk():
    r = client.post("/api/phishing/check", json={"url": PHISHING_URL})
    assert r.status_code == 200
    data = r.json()
    assert data["risk_level"] in ("SUSPICIOUS", "HIGH")
    assert data["risk_score"] > 30


def test_phishing_url_stored_as_fraud_dna_event():
    client.post("/api/phishing/check", json={"url": PHISHING_URL})
    r = client.get("/api/fraud-dna/fingerprints")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 1
    url_events = [e for e in data["fingerprints"] if e.get("source_type") == "URL"]
    assert len(url_events) >= 1


def test_clean_url_not_stored():
    client.post("/api/phishing/check", json={"url": CLEAN_URL})
    r = client.get("/api/fraud-dna/fingerprints")
    assert r.status_code == 200
    data = r.json()
    # CLEAN urls (score <= 30) must NOT be stored
    assert data["total"] == 0


def test_fraud_dna_graph_works_with_url_events():
    client.post("/api/phishing/check", json={"url": PHISHING_URL})
    r = client.get("/api/fraud-dna/graph")
    assert r.status_code == 200
    data = r.json()
    assert "nodes" in data
    assert "edges" in data
    # Nodes must have labels (not None/empty)
    for node in data["nodes"]:
        assert node["label"]  # not empty/None


def test_dashboard_stats_counts_url_events():
    client.post("/api/phishing/check", json={"url": PHISHING_URL})
    r = client.get("/api/dashboard/stats")
    assert r.status_code == 200
    data = r.json()
    assert data["url_events"] >= 1
    assert data["total_events"] >= 1


def test_dashboard_stats_empty_store():
    r = client.get("/api/dashboard/stats")
    assert r.status_code == 200
    data = r.json()
    assert data["total_events"] == 0
    assert data["url_events"] == 0
    assert data["document_events"] == 0


def test_fraud_dna_fingerprints_with_mixed_events(tmp_path, monkeypatch):
    """URL + document events coexist without crash."""
    # Store a fake doc event directly
    import uuid
    from datetime import datetime, timezone
    doc_event = {
        "event_id": str(uuid.uuid4()),
        "doc_id": str(uuid.uuid4()),
        "source_type": "DOCUMENT",
        "original_filename": "test.pdf",
        "saved_filename": "test.pdf",
        "risk_score": 40,
        "risk_level": "SUSPICIOUS",
        "risk_indicators": ["blank_author"],
        "top_keywords": ["salary"],
        "fingerprint_text": "salary blank_author",
        "document_type_hint": "salary_slip",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    dna_store.save_fingerprint(doc_event)

    # Add URL event via API
    client.post("/api/phishing/check", json={"url": PHISHING_URL})

    r = client.get("/api/fraud-dna/fingerprints")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 2

    r2 = client.get("/api/fraud-dna/graph")
    assert r2.status_code == 200
    nodes = r2.json()["nodes"]
    assert len(nodes) == 2
    for n in nodes:
        assert n["label"]  # no empty labels