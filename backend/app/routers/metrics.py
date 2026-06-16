"""Operational metrics for monitoring and health checks."""
from __future__ import annotations

import time
from typing import Any

import psutil
from fastapi import APIRouter, Depends

from app.core.cache import phish_cache, upi_cache
from app.dependencies.auth import get_current_user

router = APIRouter(prefix="/api/metrics", tags=["metrics"], dependencies=[Depends(get_current_user)])


@router.get("/system")
async def system_metrics() -> dict[str, Any]:
    """System resource usage (CPU, memory, disk, uptime)."""
    return {
        "cpu_percent": psutil.cpu_percent(interval=0.1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage("/").percent,
        "uptime_seconds": time.time() - psutil.boot_time(),
    }


@router.get("/cache")
async def cache_metrics() -> dict[str, Any]:
    """Cache hit/miss stats and capacity."""
    return {
        "upi_cache_size": upi_cache.stats()["size"],
        "upi_cache_max": upi_cache.stats()["max_size"],
        "phish_cache_size": phish_cache.stats()["size"],
        "phish_cache_max": phish_cache.stats()["max_size"],
    }


@router.get("/version")
async def version_info() -> dict[str, Any]:
    """Build/deploy info."""
    from app.config import settings

    return {
        "version": getattr(settings, "APP_VERSION", "unknown"),
        "env": getattr(settings, "APP_ENV", "development"),
        "debug": getattr(settings, "DEBUG", False),
    }