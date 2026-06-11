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
os.environ["APP_ENV"] = "test"
os.environ["DEBUG"] = "False"
os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"

import pytest
from fastapi.testclient import TestClient
from app.main import app


# Auto-use: skip auth on every test, regardless of whether it was written
# with auth in mind. The conftest runs at session-scope so the override
# is in effect for the whole test run.
@pytest.fixture(autouse=True)
def _auto_bypass_auth(monkeypatch):
    """Bypass the API key check for all tests by default.

    Tests that specifically want to verify 401 responses should use
    the `unauthed_client` fixture, which DOES enforce auth.
    """
    from app.dependencies import auth as auth_mod
    monkeypatch.setattr(auth_mod, "get_api_key", lambda: "")  # empty = dev mode
    yield


@pytest.fixture
def client():
    """Test client (auth bypassed by default via _auto_bypass_auth)."""
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Explicit auth headers (for tests that need them)."""
    return {"Authorization": f"Bearer {TEST_KEY}"}


@pytest.fixture
def enforce_auth(monkeypatch):
    """Opt-in: turn auth enforcement ON for this test.

    Use this when you want to verify that a 401 is returned for
    unauthenticated requests.
    """
    from app.dependencies import auth as auth_mod
    monkeypatch.setattr(auth_mod, "get_api_key", lambda: TEST_KEY)
    return None


@pytest.fixture
def client():
    """Pre-configured test client (auth included via env var).

    The environment variable LUMINT_API_KEY is set before app.main
    is imported (above), so get_current_user sees it and returns
    successful auth: all /api/* endpoints return 200.
    """
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Explicit auth headers (for tests that need them)."""
    return {"Authorization": f"Bearer {TEST_KEY}"}


@pytest.fixture
def unauthed_client(monkeypatch):
    """Client that fails auth for tests expecting 401."""
    from app.dependencies import auth as auth_mod
    monkeypatch.setattr(auth_mod, "get_api_key", lambda: TEST_KEY + "-wrong")
    return TestClient(app)
