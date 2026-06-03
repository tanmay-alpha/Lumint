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

logger = logging.getLogger("lumint.ai.phishshield")

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
    Analyze a PhishShield URL scan result using Groq LLaMA 3.3 70B.

    Extracts domain signals, triggered rules, similarity matches, and keywords
    then sends a structured threat intelligence prompt to the AI analyst.

    Args:
        phishing_result: Raw dict returned by the PhishShield /check endpoint.

    Returns:
        PhishingAIResult with verdict, brand attribution, attack vector, IOCs,
        and analyst note. Never raises — returns fallback on error.
    """
    url = phishing_result.get("normalized_url") or phishing_result.get("url", "unknown")
    domain = phishing_result.get("domain", "unknown")
    risk_score = phishing_result.get("risk_score", 0)
    risk_level = phishing_result.get("risk_level", "UNKNOWN")
    triggered_rules = phishing_result.get("triggered_rules") or []
    similarity_matches = phishing_result.get("domain_similarity_matches") or []
    keywords = phishing_result.get("top_keywords") or []
    is_official = phishing_result.get("is_official_bank_domain", False)

    rule_summary = [
        f"[{r.get('rule', '?')} +{r.get('score', 0)}pt] {r.get('detail', '')}"
        for r in triggered_rules[:8]
    ]
    sim_summary = [
        f"{m.get('bank', '?')} — {round(m.get('similarity', 0) * 100)}% similarity"
        for m in similarity_matches[:5]
    ]

    user_prompt = f"""PHISHSHIELD URL ANALYSIS REPORT — Lumint Engine
Target URL: {url}
Domain: {domain}
Risk Score: {risk_score}/100 | Risk Level: {risk_level}
Official Bank Domain: {is_official}

TRIGGERED DETECTION RULES ({len(triggered_rules)} total):
{json.dumps(rule_summary, indent=2)}

BRAND SIMILARITY MATCHES:
{json.dumps(sim_summary, indent=2) if sim_summary else "None detected"}

SUSPICIOUS KEYWORDS FOUND: {keywords}

Based on the above PhishShield detection data, produce your threat intelligence report as structured JSON."""

    raw = await ask_groq(system=_SYSTEM_PROMPT, user=user_prompt, json_mode=True)

    if "_error" in raw:
        logger.warning("PhishShield AI fallback triggered: %s", raw.get("_error"))
        return _FALLBACK_RESULT.model_copy(
            update={"latency_ms": raw.get("_latency_ms", 0)}
        )

    try:
        return PhishingAIResult(
            verdict=raw.get("verdict", "SUSPICIOUS"),
            target_brand=raw.get("target_brand"),
            attack_vector=raw.get("attack_vector", "unknown"),
            confidence=int(raw.get("confidence", 50)),
            analyst_note=raw.get("analyst_note", "Analysis incomplete."),
            ioc_summary=raw.get("ioc_summary") or ["No IOCs listed"],
            model_used=raw.get("_model", MODEL_ID),
            latency_ms=raw.get("_latency_ms", 0),
        )
    except Exception as exc:
        logger.error("PhishShield AI result parsing failed: %s", exc)
        return _FALLBACK_RESULT
