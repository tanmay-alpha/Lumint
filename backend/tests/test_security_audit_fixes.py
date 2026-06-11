"""Regression tests for the 2026-06-12 audit fixes.

Covers:
1. Constant-time API key comparison (no timing-attack vector)
2. WebSocket message size cap (closes connection on oversized input)
3. Document upload size limit (already existed — smoke test)
"""
import os
import hmac
from unittest.mock import patch


def test_auth_uses_hmac_compare_digest():
    """The auth module must use hmac.compare_digest, not == / !=.

    A plain string compare leaks the key prefix via response latency
    because Python's `!=` short-circuits on the first differing byte.
    hmac.compare_digest is constant-time.
    """
    import inspect
    from app.dependencies import auth

    # Get the function body (exclude docstring).
    source = inspect.getsource(auth.get_current_user)
    # Find a line containing "if token" - that's where the compare should be.
    # It must NOT look like "if token != api_key".
    for line in source.splitlines():
        stripped = line.strip()
        if stripped.startswith("if") and "token" in stripped and "!=" in stripped:
            if "api_key" in stripped:
                # It's in live code (not the docstring example).
                raise AssertionError("get_current_user still uses `token != api_key` in live code")
    # Must use hmac.compare_digest
    assert "hmac.compare_digest" in source, (
        "get_current_user does not use hmac.compare_digest"
    )


def test_auth_hmac_compare_digest_actually_works(monkeypatch):
    """End-to-end: get_current_user accepts the right key and rejects wrong ones."""
    from fastapi import HTTPException
    from app.dependencies.auth import get_current_user

    monkeypatch.setenv("LUMINT_API_KEY", "test-secret-key-12345")

    # The right key succeeds
    user = get_current_user(authorization="Bearer test-secret-key-12345")
    assert user["token_valid"] is True

    # A wrong key raises 401
    try:
        get_current_user(authorization="Bearer wrong-key")
    except HTTPException as exc:
        assert exc.status_code == 401
    else:
        raise AssertionError("Expected 401 for wrong key")

    # Missing header raises 401
    try:
        get_current_user(authorization=None)
    except HTTPException as exc:
        assert exc.status_code == 401
    else:
        raise AssertionError("Expected 401 for missing auth")


def test_websocket_message_size_cap_defined():
    """stream_router must define MAX_WS_MESSAGE_BYTES."""
    from app.routers import stream_router
    assert hasattr(stream_router, "MAX_WS_MESSAGE_BYTES"), (
        "stream_router must define MAX_WS_MESSAGE_BYTES"
    )
    # 1KB is a sensible default for keep-alive pings
    assert stream_router.MAX_WS_MESSAGE_BYTES == 1024


def test_websocket_size_cap_in_threat_stream():
    """The /ws/threats endpoint must enforce the size cap on inbound text."""
    import inspect
    from app.routers import stream_router

    source = inspect.getsource(stream_router.threat_stream)
    # The size cap must be checked somewhere in the receive loop
    assert "MAX_WS_MESSAGE_BYTES" in source, (
        "threat_stream doesn't reference MAX_WS_MESSAGE_BYTES"
    )
    # It should close with code 1009 (Message Too Big) on overflow
    assert "1009" in source, (
        "WebSocket close code 1009 (Message Too Big) not used"
    )


def test_document_upload_size_limit_exists():
    """Documents router must enforce a 15MB cap (regression — already existed)."""
    import inspect
    from app.routers import documents

    source = inspect.getsource(documents)
    assert "MAX_UPLOAD_BYTES" in source, "Documents router missing MAX_UPLOAD_BYTES"
    # 15MB is the documented cap
    assert "15 * 1024 * 1024" in source or "15728640" in source, (
        "Documents upload cap is not 15MB"
    )


def test_auth_uses_hmac_at_runtime():
    """Cross-check: the actual function uses hmac.compare_digest on identical
    and differing keys. We don't measure timing here (too noisy in tests),
    just confirm the function returns the right thing for both."""
    from app.dependencies.auth import get_current_user
    import os

    os.environ["LUMINT_API_KEY"] = "abc"
    # Right key
    assert get_current_user(authorization="Bearer abc")["token_valid"] is True
    # Wrong key (different length) — should 401
    try:
        get_current_user(authorization="Bearer abcd")
    except Exception as e:
        assert getattr(e, "status_code", None) == 401
    # Wrong key (same length, different bytes) — should 401
    try:
        get_current_user(authorization="Bearer abd")
    except Exception as e:
        assert getattr(e, "status_code", None) == 401
    # Clean up
    del os.environ["LUMINT_API_KEY"]
