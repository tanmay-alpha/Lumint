"""
DocShield AI Analyst
====================
Analyzes raw DocShield forensics results using Groq LLaMA 3.3 70B.
Produces an expert fraud analyst report with verdict, confidence scoring,
anomaly enumeration, attack type classification, and actionable guidance.
"""

import json
import logging
from typing import Literal

from pydantic import BaseModel

from ai.client import MODEL_ID, ask_groq

from ml.llm.local_inference import LumintFraudLLM

logger = logging.getLogger("lumint.ai.docshield")

llm = LumintFraudLLM()

_SYSTEM_PROMPT = """You are a senior forensic document fraud analyst with 15 years of experience
in banking fraud investigation, identity document verification, and financial crime intelligence.
You specialize in detecting forged invoices, altered KYC documents, and tampered PDF metadata.

You will receive raw forensic scan data from the Lumint DocShield engine.
Your task is to produce a structured intelligence report.

RULES:
- Be specific about anomalies. Do NOT write generic statements like "metadata mismatch found".
  Instead write: "Creation date precedes the PDF producer version by 3 years — impossible without backdating."
- If the pattern matches a known fraud kit or method (e.g. FIN7 invoice overlay, photoshop ELA signature),
  name it explicitly.
- verdict must be one of: GENUINE, SUSPICIOUS, FRAUDULENT
- confidence must be an integer 0-100 based on evidence strength
- attack_type should be concise: e.g. "Invoice Amount Override", "Photoshop Identity Forgery",
  "Backdated Metadata Tampering", "Creator Field Spoofing", "None Detected"
- analyst_note must be 2-3 sentences written like a real TI report paragraph — not a chatbot.
- recommended_action must be specific and actionable, not vague ("reject and escalate to fraud desk").
- anomalies must be concrete, specific list items (3-8 items max)

Return ONLY valid JSON matching this exact schema:
{
  "verdict": "GENUINE" | "SUSPICIOUS" | "FRAUDULENT",
  "confidence": <integer 0-100>,
  "anomalies": ["<specific anomaly>", ...],
  "attack_type": "<classification>",
  "analyst_note": "<2-3 sentence expert paragraph>",
  "recommended_action": "<specific action>"
}"""


class DocumentAIResult(BaseModel):
    """Structured AI analyst report for a forensic document scan."""

    verdict: Literal["GENUINE", "SUSPICIOUS", "FRAUDULENT"]
    confidence: int
    anomalies: list[str]
    attack_type: str
    analyst_note: str
    recommended_action: str
    model_used: str
    latency_ms: int


_FALLBACK_RESULT = DocumentAIResult(
    verdict="SUSPICIOUS",
    confidence=0,
    anomalies=["AI analysis unavailable — manual review required"],
    attack_type="Unknown — AI timeout",
    analyst_note=(
        "The Lumint AI analyst could not complete this analysis due to a service timeout. "
        "The base forensic engine findings remain valid. Manual escalation is recommended "
        "given the inability to confirm or rule out fraud programmatically."
    ),
    recommended_action="Escalate to manual fraud review. Do not approve this document automatically.",
    model_used=MODEL_ID,
    latency_ms=0,
)


async def analyze_document_ai(forensics_result: dict) -> DocumentAIResult:
    """
    Analyze a DocShield forensics result dict using LumintFraudLLM (local with Groq fallback).

    Extracts key forensic signals (risk score, indicators, metadata, ELA results)
    and sends a structured prompt to the AI analyst. Parses and validates the
    structured response into a DocumentAIResult Pydantic model.

    Args:
        forensics_result: Raw dict returned by the DocShield /analyze endpoint.

    Returns:
        DocumentAIResult with verdict, confidence, anomalies, attack type,
        analyst note, and recommended action. Never raises — returns fallback on error.
    """
    raw = await llm.analyze(forensics_result, module="doc")

    if not raw or "verdict" not in raw:
        return _FALLBACK_RESULT

    try:
        return DocumentAIResult(
            verdict=raw.get("verdict", "SUSPICIOUS"),
            confidence=int(raw.get("confidence", 50)),
            anomalies=raw.get("anomalies") or ["No specific anomalies listed"],
            attack_type=raw.get("attack_type", "Unknown"),
            analyst_note=raw.get("analyst_note", "Analysis incomplete."),
            recommended_action=raw.get("recommended_action", "Manual review required."),
            model_used=raw.get("model_used", MODEL_ID),
            latency_ms=raw.get("latency_ms", 0),
        )
    except Exception as exc:
        logger.error("DocShield AI result parsing failed: %s", exc)
        return _FALLBACK_RESULT
