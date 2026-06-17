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

    # Startup: Create tables
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ready")

    yield

    # Shutdown: Dispose engine connections
    logger.info("Shutting down database connections...")
    engine.dispose()
    logger.info("Database connections closed")
