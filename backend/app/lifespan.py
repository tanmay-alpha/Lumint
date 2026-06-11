"""FastAPI lifespan manager for Lumint."""
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import logging

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
    """
    # Startup: Create tables
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ready")

    yield

    # Shutdown: Dispose engine connections
    logger.info("Shutting down database connections...")
    engine.dispose()
    logger.info("Database connections closed")