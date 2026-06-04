"""
PhishShield AI Analyst
======================
Analyzes PhishShield URL detection results using Groq LLaMA 3.3 70B.
Produces a threat intelligence report with brand impersonation identification,
attack vector classification, IOC enumeration, and confidence scoring.
"""

import json
import logging
from typing import Literal

from pydantic import BaseModel

from ai.client import MODEL_ID, ask_groq

from ml.llm.local_inference import LumintFraudLLM

logger = logging.getLogger("lumint.ai.phishshield")

llm = LumintFraudLLM()

_SYSTEM_PROMPT = """You are a senior cybersecurity threat intelligence analyst specializing in
phishing campaign attribution, brand impersonation detection, and attack vector classification.
You are familiar with MITRE ATT&CK framework, credential harvesting infrastructure, and
common phishing kit signatures used by threat actors like Scattered Spider, FIN7, and TA505.

You will receive raw detection data from the Lumint PhishShield URL analysis engine.
Your task is to produce a structured threat intelligence report.

RULES:
- verdict must be one of: SAFE, SUSPICIOUS, PHISHING
- target_brand: identify the SPECIFIC brand being impersonated (e.g. "Chase Bank", "PayPal",
  "HDFC Bank", "Microsoft") or null if none detected.
- attack_vector must be one of: credential_harvest, malware_delivery, financial_scam,
  account_takeover, brand_impersonation, unknown
- confidence: 0-100 integer based on signal strength
- ioc_summary: 3-6 CONCRETE indicators of compromise in DM Mono style
  (e.g. "Domain registered 4 days ago via GoDaddy", not "suspicious domain")
- analyst_note: 2-3 sentences written like a REAL threat intel brief — specific, not generic.
  Describe the attack chain, not just the symptoms.

Return ONLY valid JSON matching this exact schema:
{
  "verdict": "SAFE" | "SUSPICIOUS" | "PHISHING",
  "target_brand": "<brand name>" | null,
  "attack_vector": "credential_harvest" | "malware_delivery" | "financial_scam" | "account_takeover" | "brand_impersonation" | "unknown",
  "confidence": <integer 0-100>,
  "analyst_note": "<2-3 sentence threat intel brief>",
  "ioc_summary": ["<specific IOC>", ...]
}"""


class PhishingAIResult(BaseModel):
    """Structured AI threat intelligence report for a PhishShield URL analysis."""

    verdict: Literal["SAFE", "SUSPICIOUS", "PHISHING"]
    target_brand: str | None
    attack_vector: Literal[
        "credential_harvest",
        "malware_delivery",
        "financial_scam",
        "account_takeover",
        "brand_impersonation",
        "unknown",
    ]
    confidence: int
    analyst_note: str
    ioc_summary: list[str]
    model_used: str
    latency_ms: int


_FALLBACK_RESULT = PhishingAIResult(
    verdict="SUSPICIOUS",
    target_brand=None,
    attack_vector="unknown",
    confidence=0,
    analyst_note=(
        "The Lumint AI analyst could not complete threat attribution due to a service timeout. "
        "The base PhishShield heuristic results remain valid. The domain should be treated as "
        "suspicious until manual threat intelligence review can be completed."
    ),
    ioc_summary=["AI analysis unavailable — base heuristics still apply"],
    model_used=MODEL_ID,
    latency_ms=0,
)


async def analyze_phishing_ai(phishing_result: dict) -> PhishingAIResult:
    """
    Analyze a PhishShield URL scan result using LumintFraudLLM (local with Groq fallback).

    Args:
        phishing_result: Raw dict returned by the PhishShield /check endpoint.

    Returns:
        PhishingAIResult with verdict, brand attribution, attack vector, IOCs,
        and analyst note. Never raises — returns fallback on error.
    """
    raw = await llm.analyze(phishing_result, module="phish")

    if not raw or "verdict" not in raw:
        return _FALLBACK_RESULT

    try:
        return PhishingAIResult(
            verdict=raw.get("verdict", "SUSPICIOUS"),
            target_brand=raw.get("target_brand"),
            attack_vector=raw.get("attack_vector", "unknown"),
            confidence=int(raw.get("confidence", 50)),
            analyst_note=raw.get("analyst_note", "Analysis incomplete."),
            ioc_summary=raw.get("ioc_summary") or ["No IOCs listed"],
            model_used=raw.get("model_used", MODEL_ID),
            latency_ms=raw.get("latency_ms", 0),
        )
    except Exception as exc:
        logger.error("PhishShield AI result parsing failed: %s", exc)
        return _FALLBACK_RESULT
