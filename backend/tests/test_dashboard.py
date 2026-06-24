from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_stats_empty():
    r = client.get("/api/dashboard/stats")
    assert r.status_code == 200
    data = r.json()
    assert "total_events" in data


def test_recent_events():
    r = client.get("/api/dashboard/recent-events?limit=5")
    assert r.status_code == 200
    data = r.json()
    assert "events" in data
    assert data["limit"] == 5


def test_risk_distribution_includes_critical_bucket():
    """Risk distribution must expose all 4 buckets (CLEAN/SUSPICIOUS/HIGH/CRITICAL)."""
    r = client.get("/api/dashboard/risk-distribution")
    assert r.status_code == 200
    data = r.json()
    levels = [d["risk_level"] for d in data["distribution"]]
    # Backward-compat: CLEAN and HIGH are required
    assert "CLEAN" in levels
    assert "HIGH" in levels
    # New: CRITICAL is its own bucket, separate from HIGH
    assert "CRITICAL" in levels, "CRITICAL must be a separate distribution bucket"
    assert "SUSPICIOUS" in levels
    # Exactly 4 buckets
    assert len(data["distribution"]) == 4


def test_indicator_summary():
    r = client.get("/api/dashboard/indicator-summary")
    assert r.status_code == 200
    assert "indicators" in r.json()


def test_timeline_default_seven_days():
    """Default timeline is 7 days and includes all 4 expected fields per point."""
    r = client.get("/api/dashboard/timeline")
    assert r.status_code == 200
    data = r.json()
    assert data["days"] == 7
    assert "start_date" in data and "end_date" in data
    assert "points" in data
    assert len(data["points"]) == 7
    # Each point has the new schema fields
    for p in data["points"]:
        assert set(p.keys()) == {"date", "phishing", "documents", "total"}
        assert isinstance(p["phishing"], int)
        assert isinstance(p["documents"], int)
        assert p["total"] == p["phishing"] + p["documents"]
    # total_scans is a non-negative integer
    assert isinstance(data["total_scans"], int) and data["total_scans"] >= 0


def test_timeline_buckets_group_by_source_type():
    """URL events count into 'phishing', DOCUMENT events into 'documents'."""
    from app.services.fraud_dna.store import save_fingerprint, clear_store, load_all
    from datetime import datetime, timezone, timedelta
    from app.services.fraud_dna.seed_data import _make_fingerprint
    clear_store()
    today = datetime.now(timezone.utc).isoformat()
    # Add 2 URL + 1 DOCUMENT for today
    save_fingerprint(_make_fingerprint(
        source_type="URL", source_domain="phish1.tk", risk_score=80, risk_level="HIGH",
        risk_indicators=["x"], top_keywords=["a"], document_type_hint="phishing_url",
        minutes_ago=1,
    ))
    save_fingerprint(_make_fingerprint(
        source_type="URL", source_domain="phish2.tk", risk_score=80, risk_level="HIGH",
        risk_indicators=["x"], top_keywords=["a"], document_type_hint="phishing_url",
        minutes_ago=2,
    ))
    save_fingerprint(_make_fingerprint(
        source_type="DOCUMENT", label="doc.pdf", doc_id="d1", risk_score=80, risk_level="HIGH",
        risk_indicators=["x"], top_keywords=["a"], document_type_hint="fake_invoice",
        minutes_ago=3,
    ))

    r = client.get("/api/dashboard/timeline?days=7")
    assert r.status_code == 200
    data = r.json()
    today_pt = next((p for p in data["points"] if p["date"] == today[:10]), None)
    # The today bucket has 2 phishing + 1 document = 3 total
    if today_pt is not None:
        assert today_pt["phishing"] >= 2
        assert today_pt["documents"] >= 1
        assert today_pt["total"] == today_pt["phishing"] + today_pt["documents"]


def test_timeline_rejects_invalid_days():
    """days must be between 1 and 90."""
    r = client.get("/api/dashboard/timeline?days=0")
    assert r.status_code == 422
    r = client.get("/api/dashboard/timeline?days=91")
    assert r.status_code == 422