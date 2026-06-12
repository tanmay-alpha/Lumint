"""Shared test fixtures for Lumint backend.

IMPORTANT: These fixtures run BEFORE any test module is imported.
This allows us to set environment variables (LUMINT_API_KEY) BEFORE
the app imports get_current_user, so all protected endpoints return
200 instead of 401.
"""
import os
import sys

# Set env vars before any other imports.
TEST_KEY = "test-key-for-testing-12345"
os.environ["LUMINT_API_KEY"] = TEST_KEY
os.environ["CORS_ALLOW_ORIGINS"] = '["http://localhost:3000","http://localhost:5173"]'
os.environ["APP_ENV"] = "development"  # explicitly development
os.environ["DEBUG"] = "False"
os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture(autouse=True)
def _auto_bypass_auth(monkeypatch):
    """Bypass the API key check for all tests by default.

    Tests that specifically want to verify 401 responses should use
    the `unauthed_client` fixture, which DOES enforce auth.
    """
    from app.dependencies import auth as auth_mod

    # Reset the internal cache so our monkeypatch takes effect.
    auth_mod.reset_for_testing()
    # Set to empty string — in dev mode, this makes it auth-free.
    monkeypatch.setattr(auth_mod, "get_api_key", lambda: "")
    yield


@pytest.fixture
def client():
    """Test client (auth bypassed by default via _auto_bypass_auth)."""
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Explicit auth headers (for tests that need them).

    Uses the new ``X-Api-Key`` header (preferred). ``Authorization:
    Bearer <key>`` is still accepted by the server for backward
    compatibility, but new tests should use ``X-Api-Key``.
    """
    return {"X-Api-Key": TEST_KEY}


@pytest.fixture
def bearer_auth_headers():
    """Legacy ``Authorization: Bearer`` headers — still accepted by the
    server for backward compatibility, but new tests should use the
    ``X-Api-Key`` variant via :func:`auth_headers`."""
    return {"Authorization": f"Bearer {TEST_KEY}"}


@pytest.fixture
def enforce_auth(monkeypatch):
    """Opt-in: turn auth enforcement ON for this test.

    Use this when you want to verify that a 401 is returned for
    unauthenticated requests.
    """
    from app.dependencies import auth as auth_mod

    # Set the *real* test key (not empty string).
    monkeypatch.setattr(auth_mod, "get_api_key", lambda: TEST_KEY)
    return None


@pytest.fixture
def authed_client(monkeypatch):
    """Client that enforces auth explicitly (tests expect 200 authed / 401 unauthed)."""
    from app.dependencies import auth as auth_mod

    # Use the test key (not empty).
    monkeypatch.setattr(auth_mod, "get_api_key", lambda: TEST_KEY)
    return TestClient(app)


@pytest.fixture
def unauthed_client(monkeypatch):
    """Client that fails auth for tests expecting 401."""
    from app.dependencies import auth as auth_mod

    # Use a wrong key (not empty).
    monkeypatch.setattr(auth_mod, "get_api_key", lambda: TEST_KEY + "-wrong")
    return TestClient(app)


# ─────────────────────────────────────────────────────────────────────
# Database fixture
# ─────────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _auto_setup_test_db():
    """Initialize test database in memory."""
    from app.database import engine, Base

    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


# ─────────────────────────────────────────────────────────────────────
# Other fixtures as needed
# ─────────────────────────────────────────────────────────────────────


@pytest.fixture
def sample_upi_result():
    """Return sample UPI analysis result data."""
    return {
        "analysis_status": "completed",
        "forgery_score": 10,
        "verdict": "GENUINE",
        "app_detected": "PhonePe",
        "utr": {"value": "123456789012", "normalized": "123456789012", "valid": True},
        "amount_extracted": 1200.0,
        "payee_vpa": "merchant@axis",
        "sender_upi_id": "user@paytm",
        "receiver_upi_id": "merchant@axis",
        "score_source": "heuristic",
    }
