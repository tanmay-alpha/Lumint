"""
Fraud DNA Campaign Intelligence
================================
Analyzes fraud campaign cluster data.
Produces threat actor profiling, MITRE-style TTP mapping, and
a campaign intelligence brief with prioritized recommended actions.
"""

import json
import logging
from typing import Literal

from pydantic import BaseModel

from ai.client import MODEL_ID, ask_groq

from ml.llm.local_inference import LumintFraudLLM

logger = logging.getLogger("lumint.ai.frauddna")

llm = LumintFraudLLM()

_SYSTEM_PROMPT = """You are a senior threat intelligence analyst with deep expertise in
fraud campaign attribution, MITRE ATT&CK framework mapping, and threat actor profiling.
You have tracked groups like FIN7, Scattered Spider, TA505, and UNC3429.

You will receive cluster analysis data from the Lumint Fraud DNA engine — a system
that groups related fraud events into campaigns using behavioral fingerprinting.

Your task is to produce a structured campaign intelligence brief.

RULES:
- campaign_name: Generate a creative but realistic operation name like "Operation GhostInvoice"
  or "Operation SilverThread". Use "Operation" prefix. Make it thematic to the attack type.
- threat_level: one of LOW, MEDIUM, HIGH, CRITICAL — based on scale and sophistication
- pattern_summary: 1-2 sentences describing the fraud methodology, not just the data
- estimated_scale: concise estimate e.g. "3-7 active threat actors, estimated 50-200 victims"
- analyst_brief: 3-4 sentences written like a REAL threat intelligence report.
  Describe the attack chain, actor sophistication, and campaign lifecycle stage.
  Do NOT sound like a chatbot. Sound like a CTI analyst at a CIRT.
- ttps: 4-8 MITRE ATT&CK style TTPs, formatted as "T#### — <Name>: <brief description>"
  Map to real MITRE IDs where appropriate (phishing=T1566, credential=T1589, etc.)
- recommended_actions: 3-5 specific, prioritized actions. Start each with an action verb.
  Be concrete — not "improve monitoring" but "Block all subdomains of [pattern] at DNS layer."

Return ONLY valid JSON matching this exact schema:
{
  "campaign_name": "Operation <Name>",
  "threat_level": "LOW" | "MEDIUM" | "HIGH" | "CRITICAL",
  "pattern_summary": "<1-2 sentences>",
  "estimated_scale": "<scale estimate>",
  "analyst_brief": "<3-4 sentence TI report>",
  "recommended_actions": ["<action>", ...],
  "ttps": ["T#### — <Name>: <description>", ...]
}"""


class CampaignAIResult(BaseModel):
    """Structured AI threat intelligence report for a Fraud DNA campaign cluster."""

    campaign_name: str
    threat_level: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    pattern_summary: str
    estimated_scale: str
    analyst_brief: str
    recommended_actions: list[str]
    ttps: list[str]
    model_used: str
    latency_ms: int


_FALLBACK_RESULT = CampaignAIResult(
    campaign_name="Operation Unknown",
    threat_level="MEDIUM",
    pattern_summary="AI campaign cluster classification failed or timed out.",
    estimated_scale="Unknown scale.",
    analyst_brief=(
        "The Lumint AI analyst timed out while generating this threat brief. "
        "The cluster signature points to systemic behavior, but actor classification "
        "remains inconclusive. Incident response protocols should proceed with baseline indicators."
    ),
    recommended_actions=["Review the cluster event list manually.", "Block all related indicators of compromise."],
    ttps=["T1566 — Phishing: User execution required"],
    model_used=MODEL_ID,
    latency_ms=0,
)


async def analyze_campaign_ai(cluster_data: dict) -> CampaignAIResult:
    """
    Analyze a Fraud DNA campaign cluster using LumintFraudLLM (local with Groq fallback).

    Args:
        cluster_data: Cluster metadata dict (id, stats, events, first/last seen, keywords).

    Returns:
        CampaignAIResult with operational name, threat level, TTPs, brief, actions.
        Never raises — returns fallback on error.
    """
    raw = await llm.analyze(cluster_data, module="campaign")

    if not raw or "campaign_name" not in raw:
        return _FALLBACK_RESULT

    try:
        return CampaignAIResult(
            campaign_name=raw.get("campaign_name", "Operation Unknown"),
            threat_level=raw.get("threat_level", "MEDIUM"),
            pattern_summary=raw.get("pattern_summary", "Pattern analysis unavailable."),
            estimated_scale=raw.get("estimated_scale", "Unknown scale."),
            analyst_brief=raw.get("analyst_brief", "Brief unavailable."),
            recommended_actions=raw.get("recommended_actions") or ["Manual review required."],
            ttps=raw.get("ttps") or ["TTP mapping incomplete."],
            model_used=raw.get("model_used", MODEL_ID),
            latency_ms=raw.get("latency_ms", 0),
        )
    except Exception as exc:
        logger.error("Fraud DNA AI result parsing failed: %s", exc)
        return _FALLBACK_RESULT
