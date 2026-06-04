import logging
from typing import Any, Dict
from ai.client import ask_groq
from ml.llm.local_inference import LumintFraudLLM

logger = logging.getLogger("lumint.ai.upi")

llm = LumintFraudLLM()

SYSTEM_PROMPT = """
You are Lumint's Lead Banking Forensic Analyst.
Analyze the extracted OCR text and metadata from a UPI payment receipt / screenshot.
Evaluate:
1. Structural red flags (e.g. UTR digit length mismatch, invalid character sets, mismatch between transaction date and UTR prefixes, amount inconsistency).
2. Graphic/Layout Manipulation Probability (0% to 100%).
3. Recommendations for bank mitigation or recovery action.
4. Clean summary statement of findings.

You must respond with a JSON object containing EXACTLY these keys:
{
  "risk_score": 0-100 (integer representing risk score),
  "risk_level": "CLEAN", "SUSPICIOUS", "HIGH", or "CRITICAL",
  "font_anomalies_detected": true/false (boolean),
  "suspicious_handle_flagged": true/false (boolean),
  "ai_fraud_explanation": "detailed analytical narrative here",
  "red_flags": ["flag 1", "flag 2", ...],
  "mitigation": "recommended action plan here"
}
"""

async def analyze_upi_screenshot_ai(ocr_text: str, utr_number: str, sender: str, receiver: str, amount: float) -> Dict[str, Any]:
    """
    Query LumintFraudLLM (local with Groq fallback) to evaluate fraud indicators in a UPI screenshot.
    """
    detection_result = {
        "ocr_text": ocr_text,
        "utr_number": utr_number,
        "sender": sender,
        "receiver": receiver,
        "amount": amount
    }
    try:
        response = await llm.analyze(detection_result, module="upi")
        if not response or "risk_score" not in response:
            logger.warning("LumintFraudLLM check failed for UPI; using heuristic fallback.")
            return get_fallback_report(utr_number, amount)
        return response
    except Exception as e:
        logger.error("Error analyzing UPI receipt with LumintFraudLLM: %s", e)
        return get_fallback_report(utr_number, amount)

def get_fallback_report(utr_number: str, amount: float) -> Dict[str, Any]:
    # Basic rules fallback report
    is_valid_len = len(utr_number) == 12 if utr_number else False
    risk_score = 15 if (is_valid_len and amount < 50000) else (65 if not is_valid_len else 45)
    return {
        "risk_score": risk_score,
        "risk_level": "CLEAN" if risk_score < 30 else ("SUSPICIOUS" if risk_score < 60 else "HIGH"),
        "font_anomalies_detected": not is_valid_len,
        "suspicious_handle_flagged": False,
        "ai_fraud_explanation": "AI engine fallback: structural analysis flags formatting inconsistency.",
        "red_flags": ["UTR length mismatch" if not is_valid_len else "None"],
        "mitigation": "Manually verify the transaction with the bank using UTR."
    }
