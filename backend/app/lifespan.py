"""FastAPI lifespan manager for Lumint."""
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import logging
import os

from fastapi import FastAPI

from app.database import engine, Base
from app.models.models import UPIShieldEvent, Case, ThreatFeedAlert

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Lifespan context manager for Lumint.

    Startup: Create database tables if they don't exist.
    Shutdown: Close database connections gracefully.

    Production auth guard
    ---------------------
    On startup we independently re-verify that ``LUMINT_API_KEY`` is set
    whenever ``APP_ENV`` is production. ``app.dependencies.auth`` already
    raises on the first authenticated request if the key is missing, but
    the dependency is lazy — if the first request to hit the server is
    something other than an authenticated route (e.g. a Render
    ``/healthz`` probe), a missing key would only be discovered after
    a real user request reached a protected endpoint. Failing here
    during startup means Render marks the deploy unhealthy immediately
    and rolls it back, which is the right behaviour for a security
    configuration error.
    """
    # Hard-fail in production if LUMINT_API_KEY is not set. We read the
    # env directly here (not via the cached Pydantic Settings) so the
    # guard fires even if a stale .env file shadowed the OS env during
    # Pydantic's startup read.
    app_env = os.environ.get("APP_ENV", "development").strip().lower()
    api_key = os.environ.get("LUMINT_API_KEY", "").strip()
    if app_env in {"prod", "production"} and not api_key:
        raise RuntimeError(
            "FATAL: LUMINT_API_KEY is required when APP_ENV is 'production'. "
            "Refusing to start. Set LUMINT_API_KEY in your environment "
            "(e.g. Render env vars) before deploying."
        )

    # Groq AI key check. The AI router is mounted unconditionally, but
    # calls to it would fail with an opaque 500 if the key is missing.
    # We *warn* in development (so the rest of the API still works)
    # and *fail* in production when AI features are explicitly enabled
    # via ENABLE_AI=1. This is a softer guard than LUMINT_API_KEY
    # because many deployments run the detection side without the LLM
    # explanation layer; we only want to fail when the operator has
    # asked for the LLM.
    groq_key = os.environ.get("GROQ_API_KEY", "").strip()
    enable_ai = os.environ.get("ENABLE_AI", "0").strip().lower() in {"1", "true", "yes", "on"}
    if enable_ai and not groq_key:
        if app_env in {"prod", "production"}:
            raise RuntimeError(
                "FATAL: ENABLE_AI=1 requires GROQ_API_KEY in production. "
                "Either set GROQ_API_KEY or unset ENABLE_AI."
            )
        logger.warning(
            "ENABLE_AI=1 but GROQ_API_KEY is empty. AI endpoints will return "
            "errors at request time. Set GROQ_API_KEY in your environment to "
            "silence this warning."
        )
    elif not groq_key and app_env in {"prod", "production"}:
        # Even when AI isn't explicitly enabled, surface that the
        # explanation layer is offline. We don't fail — most prod
        # deployments work fine without LLM explanations.
        logger.info(
            "GROQ_API_KEY is empty; AI explanation endpoints will return "
            "fallback responses. This is informational only."
        )

    # Startup: Create tables
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ready")

    yield

    # Shutdown: Dispose engine connections
    logger.info("Shutting down database connections...")
    engine.dispose()
    logger.info("Database connections closed")
