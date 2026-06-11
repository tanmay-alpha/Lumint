"""Authentication dependency for Lumint API."""
from fastapi import Depends, HTTPException, Header
from typing import Optional
import os
import logging

logger = logging.getLogger(__name__)


def get_api_key() -> str:
    """Get the API key from environment, with fallback to render.yaml's JWT_SECRET."""
    # Primary: LUMINT_API_KEY
    key = os.environ.get("LUMINT_API_KEY")
    if key:
        return key

    # Fallback: JWT_SECRET (for backward compat with existing render.yaml deployments)
    key = os.environ.get("JWT_SECRET")
    if key:
        logger.warning("Using JWT_SECRET as API key - migration complete when LUMINT_API_KEY is set")
        return key

    # No key configured - return empty so we can detect "not set" vs "empty string"
    return ""


def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    """
    Validate the Authorization header against the configured API key.

    Expected format: Authorization: Bearer <token>

    Returns user dict if valid, raises 401 if invalid/missing.
    """
    # If no API key is configured at all, allow access (for development)
    # In production, LUMINT_API_KEY must be set
    api_key = get_api_key()

    # Development mode: no key configured = allow all
    if not api_key:
        logger.debug("No API key configured - allowing unauthenticated access (development mode)")
        return {"user": "dev", "token_valid": False, "mode": "development"}

    # Production mode: key configured, authorization required
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Authorization header required. Use 'Authorization: Bearer <token>'"
        )

    # Check Bearer scheme
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization scheme. Use 'Bearer <token>'"
        )

    # Extract token
    token = authorization[7:]  # Remove "Bearer " prefix

    # Validate (simple string comparison - not cryptographic)
    if token != api_key:
        logger.warning("Invalid API key attempt")
        raise HTTPException(status_code=401, detail="Invalid API key")

    return {"user": "api", "token_valid": True, "mode": "production"}


def require_auth(current_user: dict = Depends(get_current_user)) -> dict:
    """Dependency that enforces authentication."""
    if not current_user.get("token_valid"):
        raise HTTPException(
            status_code=401,
            detail="Authentication required in production mode"
        )
    return current_user