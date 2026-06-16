"""
Tests for /healthz (liveness) and /readyz (readiness).

We patch the individual check functions in `app.routers.probes` to avoid
flakiness from a real DB / ML-registry / tesseract environment. The point
of these tests is the wiring (status codes, response shape, dependency
injection), not the real checks themselves — those have their own tests
elsewhere.
"""
import os

os.environ["APP_ENV"] = "test"
os.environ["DEBUG"] = "False"
os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.routers import probes as probes_module


@pytest.fixture
def client():
    return TestClient(app)


def test_healthz_always_returns_200(client):
    """Liveness probe: 200 unconditionally, even if readiness checks would fail."""
    # Force every check to "fail" — /healthz must still return 200.
    original_check_db = probes_module._check_db
    original_check_reg = probes_module._check_registry
    original_check_tes = probes_module._check_tesseract

    probes_module._check_db = lambda: (False, "forced db failure")
    probes_module._check_registry = lambda: (False, "forced reg failure", ["upi"])
    probes_module._check_tesseract = lambda: (False, "no tesseract")

    try:
        r = client.get("/healthz")
    finally:
        probes_module._check_db = original_check_db
        probes_module._check_registry = original_check_reg
        probes_module._check_tesseract = original_check_tes

    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "version" in body


def test_readyz_returns_200_when_all_checks_pass(client, monkeypatch):
    monkeypatch.setattr(probes_module, "_check_db", lambda: (True, "ok"))
    monkeypatch.setattr(
        probes_module, "_check_registry", lambda: (True, "ok", [])
    )
    monkeypatch.setattr(probes_module, "_check_tesseract", lambda: (True, "/usr/bin/tesseract"))

    r = client.get("/readyz")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ready"
    assert body["checks"]["database"]["ok"] is True
    assert body["checks"]["ml_registry"]["ok"] is True
    assert body["checks"]["tesseract"]["ok"] is True
    assert body["checks"]["tesseract"]["detail"] == "available"
    assert "app_env" not in body["checks"]


def test_readyz_returns_503_when_db_check_fails(client, monkeypatch):
    monkeypatch.setattr(probes_module, "_check_db", lambda: (False, "db unreachable"))
    monkeypatch.setattr(
        probes_module, "_check_registry", lambda: (True, "ok", [])
    )
    monkeypatch.setattr(probes_module, "_check_tesseract", lambda: (True, "/usr/bin/tesseract"))

    r = client.get("/readyz")
    assert r.status_code == 503
    body = r.json()
    assert body["status"] == "not_ready"
    assert "database" in body["missing"]
    assert body["checks"]["database"]["ok"] is False


def test_readyz_returns_503_when_models_missing(client, monkeypatch):
    monkeypatch.setattr(probes_module, "_check_db", lambda: (True, "ok"))
    monkeypatch.setattr(
        probes_module,
        "_check_registry",
        lambda: (False, "missing models: upi,phish", ["upi", "phish"]),
    )
    monkeypatch.setattr(probes_module, "_check_tesseract", lambda: (True, "/usr/bin/tesseract"))

    r = client.get("/readyz")
    assert r.status_code == 503
    body = r.json()
    assert body["status"] == "not_ready"
    assert "model:upi" in body["missing"]
    assert "model:phish" in body["missing"]


def test_readyz_returns_200_when_only_tesseract_missing(client, monkeypatch):
    """Tesseract is a soft dependency. Its absence is reported but does
    NOT cause a 503 — the API can still serve non-OCR routes."""
    monkeypatch.setattr(probes_module, "_check_db", lambda: (True, "ok"))
    monkeypatch.setattr(
        probes_module, "_check_registry", lambda: (True, "ok", [])
    )
    monkeypatch.setattr(
        probes_module,
        "_check_tesseract",
        lambda: (False, "tesseract binary not on PATH"),
    )

    r = client.get("/readyz")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ready"
    assert body["checks"]["tesseract"]["ok"] is False
    assert "tesseract" in body.get("soft_missing", [])


def test_readyz_returns_503_when_hard_and_soft_both_missing(client, monkeypatch):
    """A hard failure (DB) still 503s even if tesseract is also missing;
    the hard_missing list is the one that flips the status code."""
    monkeypatch.setattr(probes_module, "_check_db", lambda: (False, "db unreachable"))
    monkeypatch.setattr(
        probes_module,
        "_check_registry",
        lambda: (False, "missing models: upi", ["upi"]),
    )
    monkeypatch.setattr(
        probes_module,
        "_check_tesseract",
        lambda: (False, "tesseract binary not on PATH"),
    )

    r = client.get("/readyz")
    assert r.status_code == 503
    body = r.json()
    assert "database" in body["missing"]
    assert "model:upi" in body["missing"]
    # tesseract is reported in soft_missing, not in `missing`
    assert "tesseract" in body.get("soft_missing", [])
    assert "tesseract" not in body.get("missing", [])


def test_legacy_api_health_still_works(client):
    """The existing /api/health endpoint must keep working for back-compat."""
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
