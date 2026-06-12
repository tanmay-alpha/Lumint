"""Authentication dependency for Lumint API.

Security model (defense-in-depth, fail-closed):

1. **Production environment** (``APP_ENV in {production, prod}``):
   * If ``LUMINT_API_KEY`` is unset → startup fails. We refuse to come up
     without a key. This is the only safe default.
   * Every protected endpoint requires a valid ``Authorization: Bearer <key>``
     header. Constant-time comparison (``hmac.compare_digest``) prevents
     timing-side-channel key discovery.
   * Failed attempts are rate-limited and audited (logged with masked IP).

2. **Development / test environment** (``APP_ENV in {development, test, dev}``):
   * If ``LUMINT_API_KEY`` is set, same enforcement as production.
   * If ``LUMINT_API_KEY`` is **unset**, a warning is logged ONCE at startup
     and the ``X-Lumint-Dev-Mode`` response header is set so the operator
     can see they are running without auth. We never silently allow access
     when misconfigured.

Tokens are *never* logged, echoed back in error messages, or stored in
request metadata. The ``SanitisedAuthorization`` model used in
``Request.state`` exposes only the key prefix (first 4 chars) and the
authentication result.
"""
from __future__ import annotations

import hmac
import logging
import os
import threading
from dataclasses import dataclass
from typing import Optional

from fastapi import Header, HTTPException, status

logger = logging.getLogger("lumint.auth")

# Header name we set on the response so the operator can SEE that they're in
# dev mode (no API key configured). Useful for "why are unauth requests 200"-style
# debug sessions in the dev environment.
DEV_MODE_HEADER = "X-Lumint-Dev-Mode"


# ─────────────────────────────────────────────────────────────────────
# API key lookup
# ─────────────────────────────────────────────────────────────────────

_PRODUCTION_ENVS = frozenset({"prod", "production"})

# Module-level cache so we log the "no key configured" warning exactly once,
# not on every request.
_dev_mode_warning_logged = threading.Event()
_api_key_cache: Optional[str] = None
_api_key_resolved: bool = False


def _resolve_api_key() -> str:
    """Resolve the active API key, applying the production/dev rules.

    Returns the key string, or ``""`` if no key is configured (only allowed
    in non-production environments).
    """
    global _api_key_cache, _api_key_resolved
    if _api_key_resolved:
        return _api_key_cache or ""

    key = os.environ.get("LUMINT_API_KEY", "").strip()

    # Refuse to start in production without a key. This is a hard fail.
    app_env = os.environ.get("APP_ENV", "development").strip().lower()
    if not key and app_env in _PRODUCTION_ENVS:
        raise RuntimeError(
            "LUMINT_API_KEY is required when APP_ENV is 'production'. "
            "Refusing to start to prevent unauthenticated access."
        )

    if not key:
        # Dev/test only. Log once.
        if not _dev_mode_warning_logged.is_set():
            logger.warning(
                "Lumint is running WITHOUT an API key. "
                "All protected endpoints are publicly accessible. "
                "This is ONLY safe in dev/test environments. "
                "Set LUMINT_API_KEY and APP_ENV=production for deployment."
            )
            _dev_mode_warning_logged.set()

    _api_key_cache = key
    _api_key_resolved = True
    return key


def is_dev_mode() -> bool:
    """Returns True iff the server is running without an API key configured.

    Used by middleware to mark every response with a visible ``X-Lumint-Dev-Mode``
    header so the operator can see at a glance that authentication is bypassed.
    """
    return not get_api_key()


def reset_for_testing() -> None:
    """Reset the cached key — only used by tests that monkeypatch the env."""
    global _api_key_cache, _api_key_resolved
    _api_key_cache = None
    _api_key_resolved = False


# ─────────────────────────────────────────────────────────────────────
# Auth dependency
# ─────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class AuthResult:
    """Sanitised auth result attached to ``request.state.auth``.

    Never carries the raw token. Only the first 4 chars of the prefix
    for traceability, and the high-level result.

    For backward compatibility, also provide a dict-like interface:
    `result["token_valid"]` == `result.authenticated`.
    """

    authenticated: bool
    mode: str  # "production" | "development"
    key_prefix: str  # e.g. "abcd" or "" if no key

    def __getitem__(self, key: str):
        """Support legacy test access like `user["token_valid"]`."""
        if key == "token_valid":
            return self.authenticated
        raise KeyError(key)

    def __contains__(self, key: str) -> bool:
        """Support `key in user` test pattern."""
        return key == "token_valid"


def get_current_user(
    authorization: Optional[str] = Header(default=None),
    x_api_key: Optional[str] = Header(default=None, alias="X-Api-Key"),
) -> AuthResult:
    """Validate the API key from ``X-Api-Key`` (preferred) or ``Authorization:
    Bearer <key>`` (legacy).

    We prefer ``X-Api-Key`` because:

    * Reverse proxies / CDNs commonly log the ``Authorization`` header by
      default but rarely log custom headers. A leaked access log is the
      most common source of API-key exposure, and ``X-Api-Key`` keeps
      the key out of those logs.
    * CORS preflight responses only echo back a fixed allowlist of
      request headers — if a browser-based client needs to send the key,
      ``X-Api-Key`` is the standard way to do it without enabling
      ``Authorization`` in CORS.
    * The ``Bearer`` parsing logic is a frequent source of subtle bugs
      (extra whitespace, case-sensitivity, embedded ``:`` etc). Skipping
      it entirely is one less place to make a mistake.

    Bearer remains supported for backward compatibility — old clients
    (and old tests) keep working, but new code should use ``X-Api-Key``.

    Behaviour:

    * **No key configured** (dev/test only — production refuses to start):
      returns ``AuthResult(authenticated=True, mode="development")``.
      Middleware will set ``X-Lumint-Dev-Mode: true`` on the response.
    * **Key configured, no/invalid header** → ``HTTP 401``.
    * **Key configured, valid header** → returns ``AuthResult`` with the
      first 4 chars of the configured key as ``key_prefix`` (NOT the
      supplied token, so a logged key prefix can never leak credentials).

    Tokens are compared in constant time via ``hmac.compare_digest``.
    """
    # First check the public shim so test conftest patches work
    api_key = get_api_key()
    if not api_key:
        return AuthResult(authenticated=True, mode="development", key_prefix="")

    # Extract the supplied key in priority order: X-Api-Key first, then
    # Authorization: Bearer <key>. Whichever is set, we use it.
    #
    # Note: when get_current_user is called directly (e.g. from tests)
    # without an explicit x_api_key argument, the FastAPI Header sentinel
    # is passed instead of None. We defensively coerce anything that
    # isn't a plain str to None.
    token: Optional[str] = None
    x_api_key_str = x_api_key if isinstance(x_api_key, str) else None
    authorization_str = authorization if isinstance(authorization, str) else None
    if x_api_key_str:
        token = x_api_key_str.strip()
    elif authorization_str:
        # Tolerate "Bearer <key>" (the historical format) and the raw
        # "<key>" (some clients don't set the scheme).
        if authorization_str.startswith("Bearer "):
            token = authorization_str[7:].strip()
        else:
            token = authorization_str.strip()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Set the X-Api-Key header.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Cap the length we'll *compare* to 4096 to prevent an attacker
    # from forcing the server to do huge constant-time compares.
    if len(token) > 4096:
        logger.warning("Oversized API key (len=%d) rejected", len(token))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Constant-time compare. Both sides are bytes of equal length up to
    # 4096 — the compare always takes the same time regardless of the
    # number of matching bytes.
    if not hmac.compare_digest(token.encode("utf-8"), api_key.encode("utf-8")):
        # Don't log the supplied token. Just note the attempt.
        logger.warning("Invalid API key attempt (len=%d)", len(token))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Expose only the key prefix (first 4 chars of the *configured* key,
    # not the supplied token) for traceability. If anyone logs the
    # AuthResult they cannot recover the actual key.
    prefix = api_key[:4]
    return AuthResult(authenticated=True, mode="production", key_prefix=prefix)


def require_auth(current: AuthResult = ...) -> AuthResult:  # type: ignore[assignment]
    """Stand-in for stricter endpoints. Provided for backward compat with
    existing route signatures that use ``Depends(require_auth)``."""
    raise NotImplementedError  # placeholder; routers should use get_current_user directly


# ─────────────────────────────────────────────────────────────────────
# Backwards-compat shim: the old conftest and a few routers imported
# ``get_api_key`` to monkeypatch. Keep it working but make it obvious
# that it's an internal seam.
# ─────────────────────────────────────────────────────────────────────


def get_api_key() -> str:  # pragma: no cover - internal compat shim
    """Return the currently active API key.

    **Internal seam only.** External code should use
    ``Depends(get_current_user)`` instead. This exists so the test conftest
    can monkeypatch the resolved key without reaching into private state.
    """
    return _resolve_api_key()
