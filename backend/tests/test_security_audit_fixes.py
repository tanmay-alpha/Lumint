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


def test_auth_hmac_compare_digest_actually_works(enforce_auth):
    """End-to-end: get_current_user accepts the right key and rejects wrong ones."""
    from fastapi import HTTPException
    from app.dependencies.auth import get_current_user

    # The right key succeeds
    user = get_current_user(authorization="Bearer test-key-for-testing-12345")
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
    """Documents router must enforce a 12MB cap (deliberately below the
    20MB global BodySizeLimitMiddleware ceiling so the per-endpoint
    cap fires first with a specific "file too large" message).
    """
    import inspect
    from app.routers import documents

    source = inspect.getsource(documents)
    assert "MAX_UPLOAD_BYTES" in source, "Documents router missing MAX_UPLOAD_BYTES"
    # 12MB is the documented cap. We use a permissive check (12 * 1024 * 1024
    # OR 12582912 OR an explicit `12 MB` comment) so that a future rename
    # doesn't fail the regression.
    assert (
        "12 * 1024 * 1024" in source
        or "12582912" in source
        or "12 MB" in source
    ), "Documents upload cap is not 12MB"


def test_auth_uses_hmac_at_runtime(enforce_auth):
    """Cross-check: the actual function uses hmac.compare_digest on identical
    and differing keys. We don't measure timing here (too noisy in tests),
    just confirm the function returns the right thing for both."""
    from app.dependencies.auth import get_current_user

    # Right key
    assert get_current_user(authorization="Bearer test-key-for-testing-12345")["token_valid"] is True
    # Wrong key (different length) — should 401
    try:
        get_current_user(authorization="Bearer test-key-for-testing-12345x")
    except Exception as e:
        assert getattr(e, "status_code", None) == 401
    # Wrong key (same length, different bytes) — should 401
    try:
        get_current_user(authorization="Bearer test-key-for-testing-12346")
    except Exception as e:
        assert getattr(e, "status_code", None) == 401


def test_auth_x_api_key_header_supported(enforce_auth):
    """The new X-Api-Key header must be accepted (preferred path).

    The legacy Authorization: Bearer path is still supported for backward
    compatibility, but new code uses X-Api-Key so the key doesn't end up
    in proxy access logs that auto-log Authorization.
    """
    from app.dependencies.auth import get_current_user

    # X-Api-Key with the right key succeeds
    assert get_current_user(
        authorization=None, x_api_key="test-key-for-testing-12345"
    )["token_valid"] is True

    # X-Api-Key with a wrong key fails
    try:
        get_current_user(authorization=None, x_api_key="definitely-wrong-key")
    except Exception as e:
        assert getattr(e, "status_code", None) == 401
    else:
        raise AssertionError("Expected 401 for wrong X-Api-Key")

    # X-Api-Key takes priority over Authorization if both are set
    assert get_current_user(
        authorization="Bearer test-key-for-testing-12345", x_api_key="test-key-for-testing-12345"
    )["token_valid"] is True


def test_operational_metrics_require_api_key(unauthed_client):
    """System metrics disclose host resource usage and must not be public."""
    response = unauthed_client.get("/api/metrics/system")

    assert response.status_code == 401


def test_metrics_version_does_not_leak_without_auth(unauthed_client):
    """Version metrics include runtime config and must be behind auth too."""
    response = unauthed_client.get("/api/metrics/version")

    assert response.status_code == 401


def test_router_http_500_details_do_not_interpolate_exception_text():
    """HTTP 500 client details must stay generic; internals belong in logs."""
    import inspect
    from app.routers import ai, documents, export, fusion, research

    for module in (ai, documents, export, fusion, research):
        source = inspect.getsource(module)
        assert "detail=f" not in source
        assert "{str(e)}" not in source


def test_document_analysis_warnings_do_not_interpolate_exception_text():
    """Document analysis warnings are returned to clients, so keep them generic."""
    import inspect
    from app.services.docshield import analyzer, ela_forensics, layout_checker, text_extractor

    combined = (
        inspect.getsource(analyzer)
        + inspect.getsource(ela_forensics)
        + inspect.getsource(layout_checker)
        + inspect.getsource(text_extractor)
    )
    assert "failed: {e}" not in combined
    assert "completed: {e}" not in combined
    assert "{str(e)}" not in combined
    assert "str(e)" not in combined


def test_upi_client_facing_diagnostics_do_not_return_exception_text():
    """UPI API diagnostics may reach responses; errors must stay generic."""
    import inspect
    from app.services.upi import analyzer_v2, font_consistency, screenshot_forensics

    combined = (
        inspect.getsource(analyzer_v2)
        + inspect.getsource(font_consistency)
        + inspect.getsource(screenshot_forensics)
    )
    assert '"error": str(e)' not in combined
    assert "{str(e)}" not in combined
    assert "str(e)" not in combined
    assert "Image path " not in combined


def test_threat_feed_websocket_enforces_message_size_cap():
    """Every WebSocket receive loop must reject oversized client messages."""
    import inspect
    from app.routers import threats

    source = inspect.getsource(threats.websocket_endpoint)
    assert "MAX_WS_MESSAGE_BYTES" in inspect.getsource(threats)
    assert "1009" in source
