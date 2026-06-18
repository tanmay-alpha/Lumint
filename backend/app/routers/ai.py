import logging
import time
from fastapi import APIRouter, HTTPException, Depends, Request

from app.dependencies.auth import get_current_user
from app.rate_limit import limiter
from app.schemas.ai import (
    DocumentAIRequest,
    DocumentAIResponse,
    PhishingAIRequest,
    PhishingAIResponse,
    CampaignAIRequest,
    CampaignAIResponse,
    UPIAIRequest,
    UPIAIResponse,
)
from ai.docshield_ai import analyze_document_ai
from ai.phishshield_ai import analyze_phishing_ai
from ai.frauddna_ai import analyze_campaign_ai
from ai.upi_ai import analyze_upi_screenshot_ai

logger = logging.getLogger("lumint.routers.ai")
router = APIRouter(prefix="/api/ai", tags=["ai"], dependencies=[Depends(get_current_user)])


@router.post("/document", response_model=DocumentAIResponse)
@limiter.limit("10/minute")
async def run_document_ai(request: Request, body: DocumentAIRequest):
    """
    Generate an expert AI forensic analyst report for a scanned document.
    """
    try:
        result = await analyze_document_ai(body.model_dump())
        return result
    except Exception:
        logger.exception("Document AI routing failed")
        raise HTTPException(
            status_code=500, detail="Failed to generate document AI report."
        )


@router.post("/phishing", response_model=PhishingAIResponse)
async def run_phishing_ai(body: PhishingAIRequest):
    """
    Generate threat intelligence attribution and IOC summaries for a URL scan.
    """
    try:
        result = await analyze_phishing_ai(body.model_dump())
        return result
    except Exception:
        logger.exception("Phishing AI routing failed")
        raise HTTPException(
            status_code=500, detail="Failed to generate phishing AI report."
        )


@router.post("/campaign", response_model=CampaignAIResponse)
async def run_campaign_ai(body: CampaignAIRequest):
    """
    Generate a complete campaign intelligence brief, profiling TTPs and scaling threat vectors.
    """
    try:
        result = await analyze_campaign_ai(body.model_dump())
        return result
    except Exception:
        logger.exception("Campaign AI routing failed")
        raise HTTPException(
            status_code=500, detail="Failed to generate campaign AI report."
        )


from pydantic import BaseModel, Field

class AgentInvestigationRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=2000, description="Investigation query (max 2000 chars)")

@router.post("/investigate")
async def run_agent_investigation(body: AgentInvestigationRequest):
    """
    Execute an autonomous fraud intelligence investigation using the ReAct reasoning agent.
    """
    try:
        from ai.agent import FraudInvestigatorAgent
        agent = FraudInvestigatorAgent()
        result = await agent.run(body.query)
        return result
    except Exception:
        logger.exception("Autonomous agent investigation failed")
        raise HTTPException(
            status_code=500, detail="Agent investigation failed."
        )


@router.post("/analyze-upi", response_model=UPIAIResponse)
async def run_upi_ai(body: UPIAIRequest):
    """
    Generate a Groq LLM narrative report for a UPI screenshot forensics result.
    Wraps the existing `analyze_upi_screenshot_ai` output into the
    `UPIAIResponse` shape used by the frontend UPI Shield UI.
    """
    started = time.time()
    try:
        # Reuse the existing LLM-backed analyzer. We don't have the raw OCR
        # text on the wire (the frontend only sends parsed fields), so we
        # pass empty OCR — the LLM prompt falls back to heuristic scoring
        # if it has no ocr_text to work with.
        raw = await analyze_upi_screenshot_ai(
            ocr_text="",
            utr_number=body.utr_number or "",
            sender=body.sender or "",
            receiver=body.receiver or "",
            amount=body.amount or 0.0,
        )
    except Exception:
        logger.exception("UPI AI routing failed")
        raise HTTPException(
            status_code=500, detail="Failed to generate UPI AI report."
        )

    risk_score = int(raw.get("risk_score", 0) or 0)
    risk_level = (raw.get("risk_level") or "CLEAN").upper()
    if risk_level in ("CRITICAL", "HIGH", "FORGED"):
        verdict = "FORGED"
    elif risk_level in ("SUSPICIOUS", "MEDIUM", "WARN"):
        verdict = "SUSPICIOUS"
    else:
        verdict = "GENUINE"

    red_flags = raw.get("red_flags") or []
    evidence_points: list[str] = []
    if body.font_anomalies:
        evidence_points.append("Font rendering inconsistencies detected in receipt typography")
    if body.suspicious_handle:
        evidence_points.append("Receiver VPA matched a known suspicious-handle pattern")
    if body.utr_number and len(body.utr_number) != 12:
        evidence_points.append(f"UTR length anomaly: expected 12 digits, got {len(body.utr_number)}")
    for f in red_flags:
        if f and f not in evidence_points and f.lower() != "none":
            evidence_points.append(f)

    forgery_method = None
    if body.font_anomalies and body.suspicious_handle:
        forgery_method = "Composite spoof: typography + handle impersonation"
    elif body.font_anomalies:
        forgery_method = "Typography / font-metric tampering"
    elif body.suspicious_handle:
        forgery_method = "Lookalike VPA handle"

    confidence = max(35, min(99, risk_score if risk_score else 65))

    analyst_note = raw.get("ai_fraud_explanation") or "AI narrative unavailable."
    mitigation = raw.get("mitigation") or "Verify with issuing bank before acting."

    return UPIAIResponse(
        verdict=verdict,
        confidence=confidence,
        forgery_method=forgery_method,
        evidence_points=evidence_points or ["No specific red flags returned by the AI engine"],
        analyst_note=analyst_note,
        recommended_action=mitigation,
        model_used="lumint-fraud-llm+groq-fallback",
        latency_ms=int((time.time() - started) * 1000),
    )
