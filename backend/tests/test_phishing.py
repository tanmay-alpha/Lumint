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
    # Pydantic returns 422 for empty strings (min_length=1 violation),
    # which is more accurate than the old route-level 400.
    assert r.status_code in (400, 422)


def test_ip_domain():
    r = client.post("/api/phishing/check", json={"url": "http://192.168.1.1/login"})
    assert r.status_code == 200
    data = r.json()
    assert any(rule["rule"] == "ip_as_domain" for rule in data["triggered_rules"])


def test_oversized_url_rejected():
    """URLs longer than 2048 chars are rejected at the Pydantic layer."""
    r = client.post("/api/phishing/check", json={"url": "https://x.com/" + "a" * 3000})
    # Pydantic 422 (validation error) is the expected response
    assert r.status_code == 422


def test_ground_truth_must_be_binary():
    """ground_truth is constrained to 0 or 1."""
    r = client.post(
        "/api/phishing/check",
        json={"url": "https://hdfcbank.com", "ground_truth": 5},
    )
    assert r.status_code == 422


def test_response_includes_score_source():
    """Regression: PhishingCheckResponse must include score_source.

    The field tells clients whether the risk_score came from the
    trained ML model ("ml") or the rule-based heuristic fallback
    ("heuristic"). It's populated by the router based on
    ``registry.is_available("phish")``.
    """
    r = client.post("/api/phishing/check", json={"url": "https://hdfcbank.com"})
    assert r.status_code == 200
    data = r.json()

    # Field must be present in the response payload.
    assert "score_source" in data, (
        "PhishingCheckResponse is missing 'score_source' field. "
        "Clients rely on this to know whether the ML model or the "
        "heuristic produced the score."
    )
    # And it must be one of the documented literal values.
    assert data["score_source"] in ("ml", "heuristic"), (
        f"Unexpected score_source value: {data['score_source']!r}"
    )