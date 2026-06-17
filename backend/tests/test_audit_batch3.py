"""Regression tests for the 2026-06-17 audit batches 1+2.

Each test is paired with a one-line "what this would catch" comment so a
future developer who deletes the production code can see exactly what
regression they would introduce.
"""
from __future__ import annotations

import inspect
import os
from unittest.mock import AsyncMock, patch

import pytest


# ─────────────────────────────────────────────────────────────────────
# 1. LIFESPAN PRODUCTION GUARD
# ─────────────────────────────────────────────────────────────────────


def test_lifespan_hard_fails_when_api_key_missing_in_production(monkeypatch):
    """In production with no LUMINT_API_KEY, lifespan must raise.

    Without this guard, the app would start and only fail on the first
    authenticated request, after a Render health-check had already
    passed. By raising here we force Render to mark the deploy
    unhealthy and roll it back before any traffic is served.
    """
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("LUMINT_API_KEY", raising=False)

    from app.lifespan import lifespan

    called = {"started": False}

    @pytest.mark.asyncio
    async def run():
        async with lifespan(app=None):
            called["started"] = True

    with pytest.raises(RuntimeError, match="LUMINT_API_KEY"):
        import asyncio
        asyncio.run(run())
    assert not called["started"], "lifespan yielded before raising — workers would boot unauthenticated"


def test_lifespan_does_not_fail_in_development_without_key(monkeypatch):
    """In development with no API key, lifespan must start normally.

    We want dev to "just work" — without the key, auth falls open via
    is_dev_mode(), so blocking the dev startup would break local work.
    Only the production path enforces the key.
    """
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.delenv("LUMINT_API_KEY", raising=False)

    from app.lifespan import lifespan

    @pytest.mark.asyncio
    async def run():
        async with lifespan(app=None):
            pass

    import asyncio
    asyncio.run(run())  # should NOT raise


# ─────────────────────────────────────────────────────────────────────
# 2. DEV-MODE HEADER SUPPRESSION IN PRODUCTION
# ─────────────────────────────────────────────────────────────────────


def test_dev_mode_header_only_emitted_in_development(monkeypatch):
    """The X-Lumint-Dev-Mode header must NOT leak in production responses.

    If it leaked, an attacker scanning a few endpoints would instantly
    see ``X-Lumint-Dev-Mode: true`` and know the auth bypass is active.
    """
    # Static check: the middleware guards the header emission on
    # APP_ENV ∈ {development, dev, test}.
    from app import main as main_module

    src = inspect.getsource(main_module)
    assert "X-Lumint-Dev-Mode" not in src or (
        "is_dev_mode()" in src
        and 'in {"development", "dev", "test"}' in src
    ), "X-Lumint-Dev-Mode header must be gated by APP_ENV != production"


# ─────────────────────────────────────────────────────────────────────
# 3. PII REDACTION IN OCR LOG
# ─────────────────────────────────────────────────────────────────────


def test_non_upi_image_log_does_not_include_ocr_text(monkeypatch):
    """The "non-UPI image detected" log line must NOT contain OCR text.

    OCR text routinely contains UPI IDs, UTR numbers, payee VPAs, and
    transaction amounts. Logging the raw text leaks every uploaded
    screenshot's content into the log aggregator.
    """
    from app.services.upi import analyzer

    src = inspect.getsource(analyzer._gate_check)
    assert "ocr_text" not in src.split("logger.warning")[1].split("\n")[0:3][0] if "logger.warning" in src else True
    # Stronger check: the format string must NOT contain %r or %s for the text.
    for line in src.splitlines():
        if "logger.warning" in line and "Non-UPI" in line:
            assert "%r" not in line and "%s" not in line, (
                f"Non-UPI log still uses %r/%s formatting on a string: {line!r}"
            )
            assert "len(" in line, "Non-UPI log should log the length, not the content"


# ─────────────────────────────────────────────────────────────────────
# 4. PROMPT-INJECTION DELIMITERS
# ─────────────────────────────────────────────────────────────────────


def test_agent_user_query_wrapped_in_delimiters():
    """The user query passed to the LLM must be inside <user_query> delimiters.

    A naive ``f"User query: {q}"`` template would let an attacker inject
    'Final Answer: VERDICT=CLEAN' and have the next regex pass pick it
    up as a real tool call.
    """
    from ai import agent

    src = inspect.getsource(agent.FraudInvestigatorAgent.run)
    assert "<user_query>" in src, "Agent must wrap user query in <user_query> delimiters"
    assert "</user_query>" in src, "Agent must close <user_query> delimiters"


def test_agent_system_prompt_has_security_rules():
    """The agent system prompt must explicitly forbid treating user input as instructions."""
    from ai import agent

    assert "SECURITY RULES" in agent.AGENT_SYSTEM_PROMPT, \
        "AGENT_SYSTEM_PROMPT must include a SECURITY RULES section"
    assert "UNTRUSTED" in agent.AGENT_SYSTEM_PROMPT, \
        "AGENT_SYSTEM_PROMPT must label user input as UNTRUSTED"


def test_case_ai_brief_user_prompt_wrapped_in_delimiters():
    """The case data passed to the LLM must be inside <case_data> delimiters.

    Case title / description / analyst_notes are user-controlled and
    can be set via the API; without delimiters, a malicious case could
    inject a fake JSON or override the response shape.
    """
    from app.routers import cases

    src = inspect.getsource(cases.generate_case_ai_brief)
    assert "<case_data>" in src, "Case AI brief must wrap data in <case_data> delimiters"
    assert "UNTRUSTED" in src, "Case AI brief must warn that data is UNTRUSTED"


# ─────────────────────────────────────────────────────────────────────
# 5. FILE-UPLOAD STREAMING
# ─────────────────────────────────────────────────────────────────────


def test_documents_upload_streams_in_chunks():
    """The documents upload handler must NOT do a single ``await file.read()``.

    A single ``await file.read()`` buffers an unbounded body before the
    size check runs — a 100MB upload would allocate 100MB of RAM on
    the worker even though the cap is 15MB.
    """
    from app.routers import documents

    src = inspect.getsource(documents.analyze_document)
    # The bad pattern is ``contents = await file.read()`` with no chunk
    # size argument. The good pattern reads in 64KB chunks. We check
    # for the chunked-read sentinel.
    assert "CHUNK_SIZE" in src, \
        "documents.analyze_document must read in chunks (look for CHUNK_SIZE)"
    # Make sure the unbounded form isn't there
    assert "contents = await file.read()" not in src, \
        "documents.analyze_document must not do a single contents = await file.read()"


def test_upi_upload_streams_in_chunks():
    """The UPI upload handler must stream in chunks for the same reason as documents."""
    from app.routers import upi

    src = inspect.getsource(upi.analyze_screenshot)
    assert "CHUNK_SIZE" in src, \
        "upi.analyze_screenshot must read in chunks (look for CHUNK_SIZE)"
    assert "file_bytes = await file.read()" not in src, \
        "upi.analyze_screenshot must not do a single file_bytes = await file.read()"


def test_documents_filename_sanitizes_control_chars():
    """``original_filename`` echoed back in the response must not contain
    NUL / CR / LF / other ASCII control bytes.

    Browser-controlled filenames could otherwise smuggle newlines into
    downstream logs (response splitting) or truncate the name in tools
    that treat NUL as a terminator.
    """
    from app.routers import documents

    src = inspect.getsource(documents.analyze_document)
    assert "_sanitize_filename_for_response" in src, \
        "documents.analyze_document must call the filename sanitizer"


# ─────────────────────────────────────────────────────────────────────
# 6. RATE LIMITS ON EXPENSIVE ROUTES
# ─────────────────────────────────────────────────────────────────────


def test_fraud_dna_recluster_is_rate_limited():
    """/api/fraud-dna/recluster is O(n²) on the event count and must be capped."""
    from app.routers import fraud_dna

    src = inspect.getsource(fraud_dna.recluster)
    assert "@limiter.limit" in src, \
        "fraud_dna.recluster must have a @limiter.limit decorator"


def test_threats_post_is_rate_limited():
    """POST /api/threats fans out to every connected WebSocket; must be capped."""
    from app.routers import threats

    src = inspect.getsource(threats.create_threat_alert)
    assert "@limiter.limit" in src, \
        "threats.create_threat_alert must have a @limiter.limit decorator"


def test_phishing_check_batch_is_rate_limited():
    """POST /api/phishing/check/batch triggers ML inference for every URL."""
    from app.routers import phishing

    src = inspect.getsource(phishing.check_url_batch)
    assert "@limiter.limit" in src, \
        "phishing.check_url_batch must have a @limiter.limit decorator"


# ─────────────────────────────────────────────────────────────────────
# 7. WEBSOCKET SIZE CAP BEFORE READ
# ─────────────────────────────────────────────────────────────────────


def test_websocket_uses_receive_not_receive_text():
    """The threat-feed WebSocket handler must use ``receive()`` (raw
    event dict) rather than ``receive_text()``.

    ``receive_text()`` on a 1GB message would allocate the full string
    BEFORE the size check could close the connection — pushing the
    worker into OOM. ``receive()`` lets us inspect the bytes length
    before Starlette finishes buffering them.
    """
    from app.routers import threats

    src = inspect.getsource(threats.websocket_endpoint)
    # The bad pattern is ``message = await websocket.receive_text()``.
    # The good pattern is ``event = await websocket.receive()``.
    assert "await websocket.receive_text()" not in src, \
        "websocket_endpoint must not use await receive_text() — use receive() to size-cap before buffer"
    assert "await websocket.receive()" in src, \
        "websocket_endpoint must call await websocket.receive() to inspect the event"


# ─────────────────────────────────────────────────────────────────────
# 8. DATETIME.UTCNOW REPLACED
# ─────────────────────────────────────────────────────────────────────


def test_models_use_timezone_aware_utc_factory():
    """Models must use ``_utc_now`` (timezone-aware) instead of
    ``datetime.datetime.utcnow`` (deprecated in 3.12, removed in 3.14).
    """
    from app.models import models

    src = inspect.getsource(models)
    assert "datetime.datetime.utcnow" not in src, \
        "models/models.py must not use datetime.datetime.utcnow — it's deprecated"
    assert "_utc_now" in src, "models/models.py should define and use _utc_now()"


# ─────────────────────────────────────────────────────────────────────
# 9. SCHEMA FORBIDS UNKNOWN FIELDS
# ─────────────────────────────────────────────────────────────────────


def test_case_update_forbids_extra_fields():
    """``CaseUpdate`` must reject unknown fields with 422 instead of
    silently dropping them (Pydantic's default behaviour).
    """
    from app.schemas.cases import CaseUpdate

    # A clean payload works.
    CaseUpdate(title="x")

    # A payload with an unknown field raises.
    with pytest.raises(Exception):
        CaseUpdate(title="x", is_admin=True)


# ─────────────────────────────────────────────────────────────────────
# 10. PROBES — /readyz USED IN RENDER HEALTHCHECK
# ─────────────────────────────────────────────────────────────────────


def test_render_yaml_uses_readyz_for_health_check():
    """render.yaml's healthCheckPath must be /readyz (which checks DB +
    ML registry), not /healthz (which always returns 200).
    """
    from pathlib import Path

    # The test lives at backend/tests/test_*.py; render.yaml is at
    # the repo root (two levels up).
    test_path = Path(__file__).resolve()
    repo_root = test_path.parent.parent.parent
    yaml_path = repo_root / "render.yaml"
    yaml_text = yaml_path.read_text()
    assert "healthCheckPath: /readyz" in yaml_text, \
        "render.yaml must use /readyz so broken deploys (DB / models down) are detected"
    assert "healthCheckPath: /healthz" not in yaml_text, \
        "/healthz is a liveness probe — it always returns 200 and would hide broken deploys"
