"""
Fraud DNA Campaign Intelligence
================================
Analyzes fraud campaign cluster data using Groq LLaMA 3.3 70B.
Produces threat actor profiling, MITRE-style TTP mapping, and
a campaign intelligence brief with prioritized recommended actions.
"""

import json
import logging
from typing import Literal

from pydantic import BaseModel

from ai.client import MODEL_ID, ask_groq

logger = logging.getLogger("lumint.ai.frauddna")

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
    """Structured AI campaign intelligence brief for a Fraud DNA cluster."""

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
    pattern_summary="AI campaign analysis unavailable — manual threat intelligence review required.",
    estimated_scale="Unknown — data insufficient for automated estimate",
    analyst_brief=(
        "The Lumint AI analyst could not complete campaign attribution due to a service timeout. "
        "The base Fraud DNA cluster data remains valid and actionable. Manual correlation of "
        "campaign fingerprints against known threat actor databases is recommended. "
        "Do not discard this campaign data pending AI re-analysis."
    ),
    recommended_actions=[
        "Escalate campaign data to senior threat intelligence analyst",
        "Correlate fingerprints manually against known threat actor TTPs",
        "Block all associated domains and file hashes at perimeter controls",
    ],
    ttps=["TTP mapping unavailable — AI timeout"],
    model_used=MODEL_ID,
    latency_ms=0,
)


async def analyze_campaign_ai(campaign_data: dict) -> CampaignAIResult:
    """
    Generate a threat intelligence brief for a Fraud DNA campaign cluster.

    Extracts campaign metadata, common indicators, risk profiles, and event data
    then sends a structured prompt to the AI for TTP mapping and actor profiling.

    Args:
        campaign_data: Raw campaign dict from GET /api/fraud-dna/campaigns.

    Returns:
        CampaignAIResult with operation name, threat level, TTPs, analyst brief,
        and prioritized recommended actions. Never raises — returns fallback on error.
    """
    campaign_id = campaign_data.get("campaign_id", "unknown")
    event_count = campaign_data.get("event_count", 0)
    risk_level = campaign_data.get("risk_level", "UNKNOWN")
    avg_score = campaign_data.get("avg_risk_score", 0)
    indicators = campaign_data.get("common_indicators") or []
    keywords = campaign_data.get("common_keywords") or []
    first_seen = campaign_data.get("first_seen", "unknown")
    last_seen = campaign_data.get("last_seen", "unknown")
    events = campaign_data.get("events") or []

    # Summarize event types
    doc_events = [e for e in events if e.get("source_type") == "DOCUMENT"]
    url_events = [e for e in events if e.get("source_type") == "URL"]
    event_labels = [e.get("label", "unknown") for e in events[:6]]

    user_prompt = f"""FRAUD DNA CAMPAIGN CLUSTER — Lumint Engine Analysis
Campaign ID: {campaign_id}
Total Events: {event_count} ({len(doc_events)} documents, {len(url_events)} URLs)
Risk Level: {risk_level} | Avg Risk Score: {avg_score}/100
Active Window: {first_seen} → {last_seen}

COMMON INDICATORS OF COMPROMISE:
{json.dumps(indicators, indent=2)}

COMMON KEYWORDS/THEMES:
{json.dumps(keywords, indent=2)}

SAMPLED EVENT LABELS (first 6 of {event_count}):
{json.dumps(event_labels, indent=2)}

Based on this Fraud DNA cluster data, generate a complete campaign intelligence brief as structured JSON."""

    raw = await ask_groq(system=_SYSTEM_PROMPT, user=user_prompt, json_mode=True)

    if "_error" in raw:
        logger.warning("Campaign AI fallback triggered for %s: %s", campaign_id, raw.get("_error"))
        return _FALLBACK_RESULT.model_copy(
            update={"latency_ms": raw.get("_latency_ms", 0)}
        )

    try:
        return CampaignAIResult(
            campaign_name=raw.get("campaign_name", f"Operation Unknown-{campaign_id[:6]}"),
            threat_level=raw.get("threat_level", "MEDIUM"),
            pattern_summary=raw.get("pattern_summary", "Pattern analysis unavailable."),
            estimated_scale=raw.get("estimated_scale", "Unknown scale."),
            analyst_brief=raw.get("analyst_brief", "Brief unavailable."),
            recommended_actions=raw.get("recommended_actions") or ["Manual review required."],
            ttps=raw.get("ttps") or ["TTP mapping incomplete."],
            model_used=raw.get("_model", MODEL_ID),
            latency_ms=raw.get("_latency_ms", 0),
        )
    except Exception as exc:
        logger.error("Campaign AI result parsing failed for %s: %s", campaign_id, exc)
        return _FALLBACK_RESULT
