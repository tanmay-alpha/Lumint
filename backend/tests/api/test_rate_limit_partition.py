"""Tests for rate-limit partition by API key.

slowapi's ``@limiter.limit`` defaults to partitioning the rate-limit
bucket by client IP, which is wrong for an API-key-authenticated
service: two distinct API keys behind the same NAT would share one
30/minute budget. We override the key_func on the phishing endpoints
to partition by ``X-Api-Key`` (with a hash) and fall back to IP.

These tests verify both layers:

* Unit-level: the ``api_key_or_ip_key`` function returns a different
  bucket key for two distinct API keys and a stable key for the same
  key.
* Integration: sending two distinct ``X-Api-Key`` headers to the
  ``/api/phishing/check`` endpoint from the same client yields two
  separate rate-limit buckets — both succeed and the limiter's
  internal storage records them under different keys.
"""
from __future__ import annotations

import pytest
from fastapi import Request

from app.rate_limit import api_key_or_ip_key, limiter


# ─────────────────────────────────────────────────────────────────────
# Pure-function tests for the key_func
# ─────────────────────────────────────────────────────────────────────


def _make_request(headers: dict[str, str], client_host: str = "203.0.113.7") -> Request:
    """Build a minimal Starlette ``Request`` with the given headers."""
    raw_headers = [(k.lower().encode("latin-1"), v.encode("latin-1")) for k, v in headers.items()]
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/phishing/check",
        "headers": raw_headers,
        "client": (client_host, 12345),
        "server": ("testserver", 80),
        "scheme": "http",
        "query_string": b"",
    }
    return Request(scope)


def test_key_func_partitions_by_x_api_key():
    """Two distinct X-Api-Key values must produce distinct bucket keys."""
    req_a = _make_request({"X-Api-Key": "alpha-key-aaaaaaaa"})
    req_b = _make_request({"X-Api-Key": "bravo-key-bbbbbbbb"})

    key_a = api_key_or_ip_key(req_a)
    key_b = api_key_or_ip_key(req_b)

    assert key_a != key_b
    assert key_a.startswith("apikey:")
    assert key_b.startswith("apikey:")


def test_key_func_is_stable_for_same_x_api_key():
    """Repeated calls with the same X-Api-Key must return the same bucket key."""
    headers = {"X-Api-Key": "stable-key-zzzzzzzz"}
    req1 = _make_request(headers)
    req2 = _make_request(headers)

    assert api_key_or_ip_key(req1) == api_key_or_ip_key(req2)


def test_key_func_falls_back_to_ip_when_no_credentials():
    """When no credential header is present we partition by IP."""
    req = _make_request({})  # no headers
    key = api_key_or_ip_key(req)

    assert key.startswith("ip:")
    assert "203.0.113.7" in key


def test_key_func_handles_legacy_bearer_token():
    """``Authorization: Bearer <token>`` should also partition by token hash."""
    req = _make_request({"Authorization": "Bearer legacy-token-xxxxxxxx"})
    key = api_key_or_ip_key(req)

    assert key.startswith("apikey:")
    # Bearer-derived buckets use the "bearer:" sub-namespace so we don't
    # confuse them with X-Api-Key buckets during incident triage.
    assert "bearer:" in key


def test_key_func_does_not_leak_plaintext_key():
    """The bucket key must never contain the raw API key material.

    A leaked log line or metrics dump must not let an attacker recover
    the credential. We assert that only the first 4 chars (public
    prefix) and a hex digest of the full token appear in the bucket key.
    """
    raw_key = "super-secret-token-dddddddd"
    req = _make_request({"X-Api-Key": raw_key})
    bucket = api_key_or_ip_key(req)

    assert raw_key not in bucket, "Plaintext API key leaked into bucket key"
    # The 4-char prefix is intentionally part of the bucket key for
    # operator readability, but the rest of the key is just a hash.
    assert raw_key[:4] in bucket


# ─────────────────────────────────────────────────────────────────────
# Integration test: two API keys must each have their own bucket
# ─────────────────────────────────────────────────────────────────────


def test_two_api_keys_share_no_bucket_under_same_ip(monkeypatch):
    """Sending two distinct X-Api-Key headers from the same client IP
    must register as two separate rate-limit buckets.

    We use the live slowapi storage backend (``limiter._storage``) to
    inspect the buckets after issuing requests. We do NOT need to
    exceed the 30/minute budget — the partition assertion is purely
    about *which key* slowapi records the request against.
    """
    # We bypass auth so the request returns 200 instead of 401. The
    # auth bypass does not affect the rate-limit key_func (it reads
    # the raw request headers directly).
    from app.dependencies import auth as auth_mod
    auth_mod.reset_for_testing()
    monkeypatch.setattr(auth_mod, "get_api_key", lambda: "")

    # Import lazily so the app fixture is wired up before the limiter
    # storage is touched.
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)

    payload = {"url": "https://example.com"}

    # Use two keys that are guaranteed distinct. The auth bypass in
    # dev mode means the value of X-Api-Key is irrelevant for the
    # 401-vs-200 decision, but slowapi's key_func still uses it to
    # partition the bucket.
    key_a = "tenant-a-key-aaaaaaaaaaaaaaaa"
    key_b = "tenant-b-key-bbbbbbbbbbbbbbbb"

    # Hit /check a few times with each key from the same client. The
    # requests are issued from the same TestClient (same client IP),
    # which is the entire point: without the API-key partition they
    # would collide.
    for _ in range(3):
        r_a = client.post("/api/phishing/check", json=payload, headers={"X-Api-Key": key_a})
        r_b = client.post("/api/phishing/check", json=payload, headers={"X-Api-Key": key_b})

    # Auth-bypassed endpoints return 200. If we accidentally regressed
    # to a 401 path the assertion below would still catch it.
    assert r_a.status_code == 200, f"key A request failed: {r_a.status_code} {r_a.text}"
    assert r_b.status_code == 200, f"key B request failed: {r_b.status_code} {r_b.text}"

    # Inspect slowapi's storage directly. The two keys must have
    # incremented DIFFERENT bucket entries.
    storage = limiter._storage
    storage_key_a = api_key_or_ip_key(_make_request({"X-Api-Key": key_a}))
    storage_key_b = api_key_or_ip_key(_make_request({"X-Api-Key": key_b}))

    assert storage_key_a != storage_key_b
    assert storage_key_a.startswith("apikey:")
    assert storage_key_b.startswith("apikey:")

    # Both keys should have been recorded under the /check endpoint.
    # slowapi's in-memory MemoryStorage backend stores entries under a
    # composite string key of the form
    #     "LIMITER/<bucket_key>/<scope>/<amount>/<seconds>/<unit>"
    # i.e. for ``30/minute`` (amount=30, seconds=1, unit=minute):
    #     "LIMITER/apikey:xxxx:hash...//api/phishing/check/30/1/minute"
    # We build that key directly and look it up in the underlying
    # ``storage.storage`` Counter.
    raw_storage = storage.storage  # Counter[str, int]

    composite_key_a = f"LIMITER/{storage_key_a}//api/phishing/check/30/1/minute"
    composite_key_b = f"LIMITER/{storage_key_b}//api/phishing/check/30/1/minute"

    count_a = raw_storage.get(composite_key_a, 0)
    count_b = raw_storage.get(composite_key_b, 0)

    assert count_a >= 3, (
        f"Expected at least 3 hits on key A bucket ({composite_key_a!r}), got {count_a}; "
        f"all storage keys: {list(raw_storage.keys())}"
    )
    assert count_b >= 3, (
        f"Expected at least 3 hits on key B bucket ({composite_key_b!r}), got {count_b}; "
        f"all storage keys: {list(raw_storage.keys())}"
    )

    # Belt-and-braces: the two composite keys must be genuinely
    # different. If the API-key partition were broken both would
    # collapse onto the same key.
    assert composite_key_a != composite_key_b
    # And neither must look like an IP bucket.
    assert "ip:" not in composite_key_a
    assert "ip:" not in composite_key_b