"""
Liveness (/healthz) and readiness (/readyz) probes.

These are mounted at the root (no prefix) so they are reachable at
`/healthz` and `/readyz` directly, matching standard Kubernetes/12-factor
conventions and the Render health-check path in `render.yaml`.

  GET /healthz  — liveness. Always 200 if the process is alive.
  GET /readyz   — readiness. 200 only when the hard dependencies (DB,
                  ML registry) are usable. Tesseract is a *soft* check
                  and is reported but does NOT mark the service unready,
                  because OCR is one feature in a multi-module pipeline —
                  the API can still serve non-OCR routes. A 503 with a
                  `missing` list is returned when any HARD dependency is
                  not yet usable.

The legacy `/api/health` route in `routers/health.py` is kept unchanged
for back-compat with existing tests/clients.
"""
from __future__ import annotations

import logging
import shutil
from typing import Any, Dict, List, Tuple

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import check_db_connection

logger = logging.getLogger(__name__)

router = APIRouter(tags=["probes"])


# Modules the registry should be able to serve. If any are missing,
# the service is considered not ready. These MUST match the module names
# used by `ml/registry.py` — see `_load_all()` for the canonical list.
_REQUIRED_MODULES = ("upi", "phish", "doc", "fusion_meta")


def _check_db() -> Tuple[bool, str]:
    """HARD check. A bad DB is a restart signal."""
    try:
        ok = check_db_connection()
        return (ok, "ok" if ok else "db unreachable")
    except Exception as exc:  # pragma: no cover - defensive
        return (False, f"db error: {exc.__class__.__name__}")


def _check_registry() -> Tuple[bool, str, List[str]]:
    """HARD check. The whole point of the service is the ML pipeline; if
    no models are loaded, traffic would 500 on every prediction."""
    try:
        from ml.registry import get_registry  # local import: avoids forcing
        # registry init at module-import time (which would load joblib models
        # in environments where the models dir is not present, e.g. CI).
        registry = get_registry()
    except Exception as exc:  # pragma: no cover - defensive
        return (False, f"registry init failed: {exc.__class__.__name__}", [])

    missing = [m for m in _REQUIRED_MODULES if not registry.is_available(m)]
    if missing:
        return (False, "missing models: " + ",".join(missing), missing)
    return (True, "ok", [])


def _check_tesseract() -> Tuple[bool, str]:
    """SOFT check. Reported in /readyz but does not fail readiness — the
    service can still answer most requests without OCR. UPI analyze will
    return a graceful 503-style error if it actually needs tesseract."""
    path = shutil.which("tesseract")
    if path:
        return (True, path)
    return (False, "tesseract binary not on PATH")


def _run_all_checks() -> Tuple[bool, Dict[str, Any], List[str], List[str]]:
    """Run every readiness check.

    Returns (ready, checks_dict, hard_missing, soft_missing).
    `ready` is True iff the hard_missing list is empty.
    """
    db_ok, db_msg = _check_db()
    reg_ok, reg_msg, reg_missing = _check_registry()
    tess_ok, tess_msg = _check_tesseract()

    checks: Dict[str, Any] = {
        "database": {"ok": db_ok, "detail": db_msg, "hard": True},
        "ml_registry": {"ok": reg_ok, "detail": reg_msg, "missing": reg_missing, "hard": True},
        "tesseract": {"ok": tess_ok, "detail": tess_msg, "hard": False},
        "app_env": settings.APP_ENV,
    }

    hard_missing: List[str] = []
    if not db_ok:
        hard_missing.append("database")
    if not reg_ok:
        hard_missing.extend(f"model:{m}" for m in reg_missing)

    soft_missing: List[str] = []
    if not tess_ok:
        soft_missing.append("tesseract")

    ready = not hard_missing
    return ready, checks, hard_missing, soft_missing


@router.get("/healthz")
def healthz() -> Dict[str, Any]:
    """Liveness probe — process is up. Returns 200 unconditionally.

    Kept dependency-free: no DB, no model registry, no tesseract. The point
    of a liveness probe is to let the orchestrator know when to *restart*
    the process, and a probe that depends on a flaky DB will trigger
    pointless restart loops.
    """
    return {
        "status": "ok",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@router.get("/readyz")
def readyz() -> JSONResponse:
    """Readiness probe — service can accept traffic.

    Returns 200 with `{"status": "ready", "checks": {...}}` when hard
    dependencies (DB, ML registry) are usable. Returns 503 with a
    `missing` list naming every hard-failed component otherwise. Tesseract
    (a soft dependency) is reported in `checks.tesseract` and in
    `soft_missing` if absent, but does not change the HTTP status.
    """
    ready, checks, hard_missing, soft_missing = _run_all_checks()
    payload: Dict[str, Any] = {
        "status": "ready" if ready else "not_ready",
        "checks": checks,
    }
    if soft_missing:
        payload["soft_missing"] = soft_missing
    if not ready:
        payload["missing"] = hard_missing
        return JSONResponse(status_code=503, content=payload)
    return JSONResponse(status_code=200, content=payload)
