from typing import Dict, Any, List, Optional, Union

DEFAULT_WEIGHTS = {
    "document": 0.35,
    "phishing": 0.35,
    "upi": 0.30,
}

VALID_RISK_LEVELS = [
    "CLEAN",
    "LOW",
    "SUSPICIOUS",
    "HIGH",
    "CRITICAL"
]

def extract_score(result: Union[Dict[str, Any], Any, None]) -> Optional[float]:
    if result is None:
        return None
        
    score = None
    if isinstance(result, dict):
        for key in ["risk_score", "forgery_score", "score", "unified_score"]:
            if key in result and result[key] is not None:
                try:
                    score = float(result[key])
                    break
                except (ValueError, TypeError):
                    pass
    else:
        # Pydantic or class object
        for attr in ["risk_score", "forgery_score", "score", "unified_score"]:
            if hasattr(result, attr):
                val = getattr(result, attr)
                if val is not None:
                    try:
                        score = float(val)
                        break
                    except (ValueError, TypeError):
                        pass
                        
    if score is None:
        return None
        
    # Clamp score to 0..100
    return max(0.0, min(100.0, score))

def extract_level(score: float) -> str:
    if score < 25.0:
        return "CLEAN"
    elif score < 50.0:
        return "LOW"
    elif score < 70.0:
        return "SUSPICIOUS"
    elif score < 90.0:
        return "HIGH"
    else:
        return "CRITICAL"

def normalize_weights(active_modalities: List[str], custom_weights: Optional[Dict[str, float]] = None) -> Dict[str, float]:
    """
    Renormalizes the weights of active modalities so they sum to 1.0.
    """
    weights_source = custom_weights or DEFAULT_WEIGHTS
    
    # Filter active weights
    active_weights = {}
    for modality in active_modalities:
        active_weights[modality] = float(weights_source.get(modality, DEFAULT_WEIGHTS.get(modality, 0.0)))
        
    total_weight = sum(active_weights.values())
    
    if total_weight == 0:
        # Split equally if weights are all 0 or empty
        if not active_modalities:
            return {}
        equal_weight = 1.0 / len(active_modalities)
        return {m: equal_weight for m in active_modalities}
        
    # Renormalize to sum to 1.0
    return {m: w / total_weight for m, w in active_weights.items()}

def dominant_signal(scores_by_modality: Dict[str, float]) -> Optional[str]:
    valid_scores = {k: v for k, v in scores_by_modality.items() if v is not None and v > 0.0}
    if not valid_scores:
        return None
    return max(valid_scores, key=valid_scores.get)

def has_url_phish_indicator(result: Any) -> bool:
    """Helper to check if document analysis mentions urls or phishing."""
    if not result:
        return False
        
    indicators = []
    if isinstance(result, dict):
        indicators = result.get("indicators") or []
        # Check text analysis or metadata too
        text_str = str(result.get("text_analysis") or "").lower()
        if "http" in text_str or "url" in text_str or "phish" in text_str:
            return True
    else:
        indicators = getattr(result, "indicators", []) or []
        text_str = str(getattr(result, "text_analysis", "")).lower()
        if "http" in text_str or "url" in text_str or "phish" in text_str:
            return True
            
    for ind in indicators:
        rule_name = ""
        if isinstance(ind, dict):
            rule_name = str(ind.get("rule", "")).lower()
        else:
            rule_name = str(getattr(ind, "rule", "")).lower()
            
        if any(term in rule_name for term in ["url", "phish", "link", "domain"]):
            return True
            
    return False

def has_campaign_evidence(result: Any) -> bool:
    if not result:
        return False
        
    if isinstance(result, dict):
        # Look for campaign keys
        if result.get("campaign_id") or result.get("campaign"):
            return True
        # Check inside nested fingerprint
        fingerprint = result.get("phishing_fingerprint") or {}
        if isinstance(fingerprint, dict) and (fingerprint.get("campaign_id") or fingerprint.get("campaign")):
            return True
    else:
        if getattr(result, "campaign_id", None) or getattr(result, "campaign", None):
            return True
        fingerprint = getattr(result, "phishing_fingerprint", None)
        if fingerprint and (getattr(fingerprint, "campaign_id", None) or getattr(fingerprint, "campaign", None)):
            return True
            
    return False

def correlation_flags(doc_result: Any, phish_result: Any, upi_result: Any) -> List[Dict[str, Any]]:
    flags = []
    
    doc_score = extract_score(doc_result)
    phish_score = extract_score(phish_result)
    upi_score = extract_score(upi_result)
    
    scores = [s for s in [doc_score, phish_score, upi_score] if s is not None]
    
    # 1. shared_high_risk: 2+ modalities score >= 70
    high_risk_count = sum(1 for s in scores if s >= 70.0)
    if high_risk_count >= 2:
        flags.append({
            "flag": "shared_high_risk",
            "severity": "critical",
            "detail": f"Multiple modalities ({high_risk_count}) flagged high risk simultaneously."
        })
        
    # 2. doc_url_alignment: document has URL/phishing-like indicator and phish score >= 50
    if has_url_phish_indicator(doc_result) and phish_score is not None and phish_score >= 50.0:
        flags.append({
            "flag": "doc_url_alignment",
            "severity": "warning",
            "detail": "Document text/metadata contains suspicious URLs/links and phishing scan is high risk."
        })
        
    # 3. payment_fraud_alignment: UPI score >= 50 and phishing score >= 50
    if upi_score is not None and upi_score >= 50.0 and phish_score is not None and phish_score >= 50.0:
        flags.append({
            "flag": "payment_fraud_alignment",
            "severity": "critical",
            "detail": "High correlation: Both UPI screenshot layout check and Phishing checker flagged threats."
        })
        
    # 4. campaign_escalation: any campaign evidence present
    if has_campaign_evidence(doc_result) or has_campaign_evidence(phish_result) or has_campaign_evidence(upi_result):
        flags.append({
            "flag": "campaign_escalation",
            "severity": "warning",
            "detail": "Campaign attribution fingerprint identified. Possible coordinated attack group."
        })
        
    return flags

def compute_lumint_score(
    doc_result: Any = None, 
    phish_result: Any = None, 
    upi_result: Any = None, 
    weights: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Combines DocShield, PhishShield, and UPI Shield results into a unified fraud risk score.
    Supports partial inputs by renormalizing weights over active modalities.
    """
    doc_score = extract_score(doc_result)
    phish_score = extract_score(phish_result)
    upi_score = extract_score(upi_result)
    
    scores_by_modality = {}
    active_modalities = []
    
    if doc_score is not None:
        scores_by_modality["document"] = doc_score
        active_modalities.append("document")
    if phish_score is not None:
        scores_by_modality["phishing"] = phish_score
        active_modalities.append("phishing")
    if upi_score is not None:
        scores_by_modality["upi"] = upi_score
        active_modalities.append("upi")
        
    # If no inputs are present
    if not active_modalities:
        return {
            "unified_score": 0,
            "risk_level": "CLEAN",
            "dominant_signal": None,
            "scores": {
                "document": None,
                "phishing": None,
                "upi": None
            },
            "weights": {
                "document": DEFAULT_WEIGHTS["document"],
                "phishing": DEFAULT_WEIGHTS["phishing"],
                "upi": DEFAULT_WEIGHTS["upi"]
            },
            "correlation_flags": [],
            "explanation": ["No active signals provided for fusion evaluation."]
        }
        
    normalized_w = normalize_weights(active_modalities, weights)
    
    weighted_score = 0.0
    for modality in active_modalities:
        weighted_score += scores_by_modality[modality] * normalized_w[modality]
        
    unified_score = int(round(max(0.0, min(100.0, weighted_score))))
    risk_level = extract_level(unified_score)
    dom_signal = dominant_signal(scores_by_modality)
    
    corr_flags = correlation_flags(doc_result, phish_result, upi_result)
    
    # Generate human readable explanation
    explanation = []
    for modality in active_modalities:
        explanation.append(
            f"Modality '{modality}' contributed score {scores_by_modality[modality]:.1f} (Weight: {normalized_w[modality]*100:.1f}%)."
        )
    if dom_signal:
        explanation.append(f"Dominant threat vector identified: '{dom_signal}'.")
        
    if corr_flags:
        flag_names = [f["flag"] for f in corr_flags]
        explanation.append(f"Correlations triggered: {', '.join(flag_names)}.")
        
    # Output schema format
    return {
        "unified_score": unified_score,
        "risk_level": risk_level,
        "dominant_signal": dom_signal,
        "scores": {
            "document": doc_score,
            "phishing": phish_score,
            "upi": upi_score
        },
        "weights": {
            "document": normalized_w.get("document", 0.0),
            "phishing": normalized_w.get("phishing", 0.0),
            "upi": normalized_w.get("upi", 0.0)
        },
        "correlation_flags": corr_flags,
        "explanation": explanation
    }
