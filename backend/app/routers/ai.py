import logging
from fastapi import APIRouter, HTTPException

from app.schemas.ai import (
    DocumentAIRequest,
    DocumentAIResponse,
    PhishingAIRequest,
    PhishingAIResponse,
    CampaignAIRequest,
    CampaignAIResponse,
)
from ai.docshield_ai import analyze_document_ai
from ai.phishshield_ai import analyze_phishing_ai
from ai.frauddna_ai import analyze_campaign_ai

logger = logging.getLogger("lumint.routers.ai")
router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.post("/document", response_model=DocumentAIResponse)
async def run_document_ai(body: DocumentAIRequest):
    """
    Generate an expert AI forensic analyst report for a scanned document.
    """
    try:
        result = await analyze_document_ai(body.model_dump())
        return result
    except Exception as e:
        logger.error("Document AI routing failed: %s", e)
        raise HTTPException(
            status_code=500, detail=f"Failed to generate document AI report: {str(e)}"
        )


@router.post("/phishing", response_model=PhishingAIResponse)
async def run_phishing_ai(body: PhishingAIRequest):
    """
    Generate threat intelligence attribution and IOC summaries for a URL scan.
    """
    try:
        result = await analyze_phishing_ai(body.model_dump())
        return result
    except Exception as e:
        logger.error("Phishing AI routing failed: %s", e)
        raise HTTPException(
            status_code=500, detail=f"Failed to generate phishing AI report: {str(e)}"
        )


@router.post("/campaign", response_model=CampaignAIResponse)
async def run_campaign_ai(body: CampaignAIRequest):
    """
    Generate a complete campaign intelligence brief, profiling TTPs and scaling threat vectors.
    """
    try:
        result = await analyze_campaign_ai(body.model_dump())
        return result
    except Exception as e:
        logger.error("Campaign AI routing failed: %s", e)
        raise HTTPException(
            status_code=500, detail=f"Failed to generate campaign AI report: {str(e)}"
        )


from pydantic import BaseModel

class AgentInvestigationRequest(BaseModel):
    query: str

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
    except Exception as e:
        logger.error("Autonomous agent investigation failed: %s", e)
        raise HTTPException(
            status_code=500, detail=f"Agent investigation failed: {str(e)}"
        )
