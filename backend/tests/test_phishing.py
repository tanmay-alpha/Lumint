from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_clean_url():
    r = client.post("/api/phishing/check", json={"url": "https://hdfcbank.com"})
    assert r.status_code == 200
    data = r.json()
    assert data["risk_level"] == "CLEAN"
    assert data["risk_score"] <= 30


def test_phishing_url():
    r = client.post(
        "/api/phishing/check",
        json={"url": "http://hdfc-bank-verify-login.com/kyc-update"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["risk_level"] in ("SUSPICIOUS", "HIGH")
    assert data["risk_score"] > 30


def test_empty_url():
    r = client.post("/api/phishing/check", json={"url": ""})
    assert r.status_code == 400


def test_ip_domain():
    r = client.post("/api/phishing/check", json={"url": "http://192.168.1.1/login"})
    assert r.status_code == 200
    data = r.json()
    assert any(rule["rule"] == "ip_as_domain" for rule in data["triggered_rules"])