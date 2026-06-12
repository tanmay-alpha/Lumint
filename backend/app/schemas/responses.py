"""Standardized response models for Lumint API.

These Pydantic models are the canonical shape of the public API
response. They are referenced via ``response_model=...`` on each
route so the OpenAPI schema is self-documenting, and they enable
TypeScript type generation on the frontend via ``openapi-typescript``.

Keep these models stable — they are part of the public contract.
"""
from __future__ import annotations

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


# ── UPI / Screenshot Forensics ──────────────────────────────────────


class UPIResult(BaseModel):
    """Output of POST /api/upi/analyze."""

    verdict: str = Field(
        ...,
        description="LIKELY_FORGED | SUSPICIOUS | LIKELY_GENUINE | NOT_UPI_SCREENSHOT",
    )
    forgery_score: float = Field(..., ge=0, le=100)
    confidence: float = Field(..., ge=0, le=1)
    score_source: str = Field(..., description="ml | heuristic")

    amount: Optional[float] = None
    payee_vpa: Optional[str] = None
    sender_vpa: Optional[str] = None
    primary_utr: Optional[Dict[str, Any]] = None
    app_detected: Optional[str] = None

    indicators: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


# ── PhishShield / URL Risk ──────────────────────────────────────────


class PhishingResult(BaseModel):
    """Output of POST /api/phishing/check."""

    risk_score: int = Field(..., ge=0, le=100)
    risk_level: str = Field(..., description="CLEAN | LOW_RISK | SUSPICIOUS | HIGH")
    url: str
    normalized_url: Optional[str] = None
    domain: Optional[str] = None
    confidence: float = Field(default=0.5, ge=0, le=1)

    signals: List[Dict[str, Any]] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    message: Optional[str] = None


# ── Document Forensics ──────────────────────────────────────────────


class DocShieldResult(BaseModel):
    """Output of POST /api/documents/analyze."""

    risk_score: float = Field(..., ge=0, le=100)
    verdict: str = Field(..., description="GENUINE | SUSPICIOUS | LIKELY_FORGED")
    confidence: float = Field(..., ge=0, le=1)

    ela_regions: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = None
    warnings: List[str] = Field(default_factory=list)


# ── Error ───────────────────────────────────────────────────────────


class ErrorResponse(BaseModel):
    """Standard error envelope."""

    error: str
    detail: Optional[str] = None
    request_id: Optional[str] = None


# ── Metrics ─────────────────────────────────────────────────────────


class SystemMetrics(BaseModel):
    """Output of GET /api/metrics/system."""

    cpu_percent: float
    memory_percent: float
    disk_percent: float
    uptime_seconds: float


class CacheMetrics(BaseModel):
    """Output of GET /api/metrics/cache."""

    upi_cache_size: int
    upi_cache_max: int
    phish_cache_size: int
    phish_cache_max: int


class VersionInfo(BaseModel):
    """Output of GET /api/metrics/version."""

    version: str
    env: str
    debug: bool
