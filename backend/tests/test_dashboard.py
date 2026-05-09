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


def test_risk_distribution():
    r = client.get("/api/dashboard/risk-distribution")
    assert r.status_code == 200
    data = r.json()
    levels = [d["risk_level"] for d in data["distribution"]]
    assert "CLEAN" in levels
    assert "HIGH" in levels


def test_indicator_summary():
    r = client.get("/api/dashboard/indicator-summary")
    assert r.status_code == 200
    assert "indicators" in r.json()