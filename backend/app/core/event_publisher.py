import uuid
import datetime
import logging
from app.routers.stream_router import manager

logger = logging.getLogger("lumint.event_publisher")

async def publish_threat_event(
    module: str,
    detection_result: dict,
    ai_result: dict,
    drift_signal: dict
) -> None:
    """
    Formats results into standard ThreatEvent.
    Broadcasts to all connected WebSocket clients.
    Non-blocking: fire and forget.
    """
    try:
        # Determine threat level & risk score
        risk_score = 50
        threat_level = "MEDIUM"
        
        if isinstance(detection_result, dict):
            risk_score = detection_result.get("risk_score", risk_score)
            threat_level = detection_result.get("risk_level", threat_level)
        if isinstance(ai_result, dict) and "risk_score" in ai_result:
            risk_score = ai_result.get("risk_score", risk_score)
            threat_level = ai_result.get("risk_level", threat_level)
            
        if isinstance(threat_level, str):
            threat_level = threat_level.upper()
            if threat_level in ["CLEAN", "LOW_RISK", "LOW"]:
                threat_level = "LOW"
            elif threat_level in ["SUSPICIOUS", "MEDIUM_RISK", "MEDIUM"]:
                threat_level = "MEDIUM"
            elif threat_level in ["HIGH_RISK", "HIGH"]:
                threat_level = "HIGH"
            elif threat_level in ["CRITICAL", "CRITICAL_RISK"]:
                threat_level = "CRITICAL"
                
        if threat_level not in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
            if risk_score >= 81:
                threat_level = "CRITICAL"
            elif risk_score >= 61:
                threat_level = "HIGH"
            elif risk_score >= 31:
                threat_level = "MEDIUM"
            else:
                threat_level = "LOW"

        # Determine indicators
        indicators = []
        if isinstance(detection_result, dict):
            if "triggered_rules" in detection_result:
                rules = detection_result["triggered_rules"]
                if isinstance(rules, list):
                    for r in rules:
                        if isinstance(r, dict) and "rule" in r:
                            indicators.append(r["rule"])
                        elif isinstance(r, str):
                            indicators.append(r)
            elif "indicators" in detection_result:
                rules = detection_result["indicators"]
                if isinstance(rules, list):
                    for r in rules:
                        if isinstance(r, dict) and "rule" in r:
                            indicators.append(r["rule"])
                        elif isinstance(r, str):
                            indicators.append(r)
            elif "risk_indicators" in detection_result:
                rules = detection_result["risk_indicators"]
                if isinstance(rules, list):
                    for r in rules:
                        if isinstance(r, str):
                            indicators.append(r)
                            
        if not indicators:
            indicators = ["threat detected"]

        # Build summary and AI verdict
        ai_verdict = "UNKNOWN"
        summary = ""
        
        if module == "phish":
            domain = detection_result.get("domain") or "unknown domain"
            summary = f"Phishing URL detected targeting {domain}"
            if isinstance(ai_result, dict):
                ai_verdict = ai_result.get("verdict", "PHISHING").upper()
            else:
                ai_verdict = "PHISHING"
        elif module == "doc":
            filename = detection_result.get("original_filename") or "document.pdf"
            summary = f"Suspicious document metadata tampering in {filename}"
            if isinstance(ai_result, dict):
                ai_verdict = ai_result.get("verdict", "TAMPERED").upper()
            else:
                ai_verdict = "TAMPERED"
        elif module == "upi":
            amount = detection_result.get("amount") or 0.0
            summary = f"UPI screenshot verification of amount {amount} INR"
            if isinstance(ai_result, dict):
                ai_verdict = ai_result.get("verdict", "FRAUD").upper()
            else:
                ai_verdict = "FRAUD"
        elif module == "fraud_dna":
            summary = f"Fraud DNA Campaign Correlation Alert"
            ai_verdict = "FRAUD"
            
        if not summary:
            summary = f"Threat event in {module}"

        drift_status = "stable"
        if isinstance(drift_signal, dict):
            drift_status = drift_signal.get("status", "stable")
        elif hasattr(drift_signal, "status"):
            drift_status = drift_signal.status
            if hasattr(drift_status, "value"):
                drift_status = drift_status.value

        event = {
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "module": module,
            "threat_level": threat_level,
            "summary": summary,
            "risk_score": risk_score,
            "ai_verdict": ai_verdict,
            "indicators": indicators,
            "drift_status": drift_status
        }
        
        await manager.broadcast(event)
    except Exception as e:
        logger.error(f"Failed to publish threat event: {e}")
