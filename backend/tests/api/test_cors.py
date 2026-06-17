"""
Tests for env-driven CORS configuration.

Verifies:
  1. An Origin in the allowlist receives `access-control-allow-origin`.
  2. An Origin NOT in the allowlist receives no such header.
  3. A request with no Origin header is unaffected (browser flow only).

We build a fresh FastAPI app for the allowed-Origin test so we can override
`cors_allow_origins` (the module-level app picks up settings at import time).
This exercises the real CORS middleware in `app/main.py`, not a re-implementation.
"""
import os

os.environ["APP_ENV"] = "test"
os.environ["DEBUG"] = "False"
os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient

from app.config import settings


def _make_app(allow_origins: list[str]) -> FastAPI:
    """Build a FastAPI app with the same CORS configuration as app.main."""
    app = FastAPI(title="cors-test-app")

    @app.get("/ping")
    def ping():
        return {"ok": True}

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Api-Key", "X-Request-ID"],
    )
    return app


def test_allowed_origin_receives_acao_header():
    """When the request Origin is in the allowlist, the response carries
    `access-control-allow-origin: <origin>`."""
    app = _make_app(["https://fraud-intelligence.vercel.app"])
    client = TestClient(app)

    r = client.get("/ping", headers={"Origin": "https://fraud-intelligence.vercel.app"})

    assert r.status_code == 200
    assert r.headers.get("access-control-allow-origin") == "https://fraud-intelligence.vercel.app"


def test_disallowed_origin_receives_no_acao_header():
    """When the request Origin is NOT in the allowlist, the response MUST NOT
    carry any `access-control-allow-origin` header (browser will block)."""
    app = _make_app(["https://fraud-intelligence.vercel.app"])
    client = TestClient(app)

    r = client.get("/ping", headers={"Origin": "https://evil.example.com"})

    assert r.status_code == 200  # The request itself succeeds
    assert "access-control-allow-origin" not in {k.lower() for k in r.headers}


def test_no_origin_header_request_still_works():
    """Server-to-server / curl requests without an Origin header must work."""
    app = _make_app(["https://fraud-intelligence.vercel.app"])
    client = TestClient(app)

    r = client.get("/ping")

    assert r.status_code == 200
    assert r.json() == {"ok": True}


def test_default_settings_allowlist_is_localhost_only():
    """With no env var set, the default `cors_allow_origins` must be localhost-only
    (a regression here would mean a Vercel deploy starts accepting any origin
    by accident)."""
    # The settings default is loaded at import time; verify the literal value.
    assert settings.cors_allow_origins == [
        "http://localhost:3000",
        "http://localhost:5173",
    ]


def test_module_level_app_uses_env_driven_origins():
    """The real app.main app must wire CORS through settings.origins_list,
    with the regex/wildcard methods/headers removed."""
    from app.main import app as real_app

    cors_layers = [
        m for m in real_app.user_middleware if m.cls.__name__ == "CORSMiddleware"
    ]
    assert cors_layers, "Expected CORSMiddleware on the real app"

    # Inspect the middleware's bound args instead of `options` (the public
    # attribute name changed in recent Starlette versions).
    mw = cors_layers[0]
    args_dict = dict(mw.args) if mw.args else {}
    kwargs_dict = dict(mw.kwargs) if mw.kwargs else {}

    origins = args_dict.get("allow_origins") or kwargs_dict.get("allow_origins")
    assert origins == settings.origins_list

    # The previous config had allow_origin_regex=r"https://.*\.vercel\.app"
    # and wildcard methods/headers. Spec says remove them.
    assert "allow_origin_regex" not in args_dict
    assert "allow_origin_regex" not in kwargs_dict
    assert args_dict.get("allow_methods") != ["*"]
    assert args_dict.get("allow_headers") != ["*"]


def test_module_level_app_allows_preferred_api_key_header():
    """Browser clients must be able to send the preferred X-Api-Key header."""
    from app.main import app as real_app

    cors_layers = [
        m for m in real_app.user_middleware if m.cls.__name__ == "CORSMiddleware"
    ]
    assert cors_layers, "Expected CORSMiddleware on the real app"

    mw = cors_layers[0]
    args_dict = dict(mw.args) if mw.args else {}
    kwargs_dict = dict(mw.kwargs) if mw.kwargs else {}

    allow_headers = args_dict.get("allow_headers") or kwargs_dict.get("allow_headers")
    assert "X-Api-Key" in allow_headers


def test_wildcard_cors_rejects_unconfigured_vercel_origin():
    """Vercel origins are allowed only when explicitly configured.

    Accepting every *.vercel.app preview would let any Vercel project make
    credentialed browser requests to the API.
    """
    from app.main import app as real_app

    client = TestClient(real_app)

    r = client.options(
        "/healthz",
        headers={
            "Origin": "https://attacker-preview.vercel.app",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "X-Api-Key",
        },
    )

    assert r.status_code == 400
    assert "access-control-allow-origin" not in {k.lower() for k in r.headers}


def test_wildcard_cors_rejects_simple_unconfigured_vercel_origin():
    """Simple CORS requests must not get reflected ACAO for unconfigured Vercel origins."""
    from app.main import app as real_app

    client = TestClient(real_app)

    r = client.get(
        "/healthz",
        headers={"Origin": "https://attacker-preview.vercel.app"},
    )

    assert "access-control-allow-origin" not in {k.lower() for k in r.headers}
