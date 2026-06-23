"""Regression tests for phishing endpoint body-size caps.

The /check/batch endpoint accepts up to 100 URLs, each up to 2048
chars. The naive case (100 max-length URLs) is ~200 KB. We add an
explicit aggregate cap so:

  1. The endpoint can return a clean 413 with a useful message
     before the per-URL validator's slower path.
  2. A rate-limit slot isn't consumed by a request that was always
     going to be rejected.

Tests run through the FastAPI TestClient so the rate-limiter
wrappers and middleware all exercise normally.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_single_check_rejects_oversize_url(client):
    """A 2 KB+ URL must be rejected with a 4xx (not 200, not 500).

    The pydantic Field validator (max_length=2048) catches the
    request first with 422. Our explicit check in the handler would
    return 413, but the pydantic layer fires first. Either rejection
    is acceptable — the key is that the endpoint doesn't 500 and
    doesn't process a multi-KB URL.
    """
    huge_url = "https://example.com/" + ("a" * 5000)
    res = client.post("/api/phishing/check", json={"url": huge_url})
    assert res.status_code in (413, 422), (
        f"Expected 413 or 422, got {res.status_code}: {res.text}"
    )


def test_batch_check_aggregate_cap_under_limit_works(client):
    """A small batch (10 URLs of 100 chars) must still be processed
    end-to-end through the new cap check.
    """
    urls = [f"https://example.com/{'a' * 80}/{i}" for i in range(10)]
    res = client.post("/api/phishing/check/batch", json={"urls": urls})
    # The endpoint runs the analyzer on each URL; with valid input
    # we expect 200 and a results list. The exact scores don't
    # matter — we just want the cap check to let it through.
    assert res.status_code == 200, f"Got {res.status_code}: {res.text}"
    body = res.json()
    assert body.get("total") == len(urls)
    assert len(body.get("results", [])) == len(urls)


def test_batch_check_rejects_when_aggregate_chars_exceed_cap(client, monkeypatch):
    """Confirm the cap fires when total chars > the threshold.
    We can't construct a legal 100*2048+ payload in a unit test
    (200 KB of JSON is wasteful), so we temporarily lower the
    constant and re-issue a small request that exceeds it.
    """
    from app.routers import phishing

    original = phishing.MAX_BATCH_BODY_CHARS
    monkeypatch.setattr(phishing, "MAX_BATCH_BODY_CHARS", 100)
    try:
        # 5 URLs * 30 chars = 150 chars total, over the (artificial) cap.
        urls = [f"https://example.com/{'a' * 20}/{i}" for i in range(5)]
        res = client.post("/api/phishing/check/batch", json={"urls": urls})
        assert res.status_code == 413, f"Expected 413, got {res.status_code}: {res.text}"
    finally:
        # monkeypatch handles restore; this is just defensive.
        phishing.MAX_BATCH_BODY_CHARS = original
