import re
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

from app.services.upi.ocr_adapter import extract_text_from_image
from app.services.upi.app_detector import detect_upi_app
from app.services.upi.utr import extract_utr_candidates, validate_utr
from app.services.upi.color_profile import check_color_authenticity
from app.services.upi.screenshot_forensics import run_image_ela
from app.services.upi.font_consistency import check_font_consistency

logger = logging.getLogger("lumint.services.upi.analyzer")

def parse_amount(text: str) -> Optional[float]:
    """
    Extract the transaction amount from OCR text using priority-ordered patterns.
    Returns a float (e.g. 1200.0) or None if not found.

    Priority:
      1. ₹ symbol directly followed by digits (e.g. ₹1,200.00)
      2. Rs. / RS. prefix (e.g. Rs. 15,200.00)
      3. INR prefix (e.g. INR 500)
      4. Amount/Paid label (e.g. amount: 1200)
      5. 3+ digit comma-formatted decimal fallback (e.g. 15,200.00)
    """
    # Normalise — keep ₹ intact, lowercase rest
    text_lower = text.lower()

    def _to_float(raw: str) -> Optional[float]:
        cleaned = raw.replace(",", "").strip()
        try:
            return float(cleaned)
        except ValueError:
            return None

    # 1. ₹ symbol (highest priority)
    m = re.search(r'₹\s*([\d,]+(?:\.\d{1,2})?)', text)
    if m:
        val = _to_float(m.group(1))
        if val is not None:
            return val

    # 2. Rs. prefix (case-insensitive)
    m = re.search(r'rs\.?\s*([\d,]+(?:\.\d{1,2})?)', text_lower)
    if m:
        val = _to_float(m.group(1))
        if val is not None:
            return val

    # 3. INR prefix
    m = re.search(r'inr\s*([\d,]+(?:\.\d{1,2})?)', text_lower)
    if m:
        val = _to_float(m.group(1))
        if val is not None:
            return val

    # 4. Amount / Paid label
    m = re.search(r'(?:amount|paid|total)[:\s]+([\d,]+(?:\.\d{1,2})?)', text_lower)
    if m:
        val = _to_float(m.group(1))
        if val is not None:
            return val

    # 5. General comma-formatted decimal fallback (e.g. 15,200.00)
    matches = re.findall(r'\b\d{1,3}(?:,\d{2,3})*(?:\.\d{2})\b', text_lower)
    if matches:
        val = _to_float(matches[0])
        if val is not None:
            return val

    return None


def parse_vpas(text: str) -> List[str]:
    """Extract virtual payment addresses (VPAs) from text."""
    text_clean = text.lower()
    return re.findall(r'\b[a-zA-Z0-9.\-_]+@[a-zA-Z0-9]+\b', text_clean)

def analyze_upi_screenshot(image_path: Path, custom_ocr_text: Optional[str] = None) -> Dict[str, Any]:
    """
    Unified UPI Shield Analysis Pipeline:
    1. Run OCR (or use provided custom text)
    2. Detect UPI App (PhonePe, GPay, Paytm, etc.)
    3. Extract & Validate UTR candidates
    4. Extract Amount & Payee VPAs
    5. Run ELA Forensics
    6. Verify Font Consistency
    7. Verify Color Authenticity
    8. Compute Forgery Score & Verdict
    9. Compute XAI Feature Contributions
    """
    warnings = []
    
    # 1. OCR Extraction
    ocr_result = extract_text_from_image(image_path, fallback_text=custom_ocr_text)
    ocr_text = ocr_result["text"]
    if ocr_result.get("warnings"):
        warnings.extend(ocr_result["warnings"])
        
    # 2. Extract UTR candidates
    utr_candidates = extract_utr_candidates(ocr_text)
    primary_utr = utr_candidates[0] if utr_candidates else None
    
    # 3. App Detection (needs colors + text)
    # We first extract colors to pass to app detection
    dominant_colors_info = []
    try:
        from app.services.upi.color_profile import extract_dominant_colors
        dominant_colors_info = extract_dominant_colors(image_path)
    except Exception as e:
        logger.debug("Failed to pre-extract colors for app detection: %s", e)
        
    dominant_hex_list = [item["hex"] for item in dominant_colors_info] if dominant_colors_info else None
    app_result = detect_upi_app(ocr_text, dominant_colors=dominant_hex_list)
    app_detected = app_result["app"]
    
    # Re-validate primary UTR with app hint if we have one
    if primary_utr:
        primary_utr = validate_utr(primary_utr["value"], app_hint=app_detected)
        
    # 4. Extract Amount & Payee VPA
    amount_val = parse_amount(ocr_text)
    vpas = parse_vpas(ocr_text)
    payee_vpa = vpas[1] if len(vpas) > 1 else (vpas[0] if len(vpas) > 0 else None)
    sender_upi_id = vpas[0] if len(vpas) > 0 else "unknown@upi"
    receiver_upi_id = vpas[1] if len(vpas) > 1 else "unknown@merchant"
    
    # 5. ELA Forensics
    ela_result = run_image_ela(image_path)
    if ela_result.get("warnings"):
        warnings.extend(ela_result["warnings"])
        
    # 6. Font Consistency
    font_result = check_font_consistency(image_path, ocr_text=ocr_text)
    if font_result.get("warnings"):
        warnings.extend(font_result["warnings"])
        
    # 7. Color Authenticity
    color_result = check_color_authenticity(image_path, app_detected=app_detected)
    if color_result.get("warnings"):
        warnings.extend(color_result["warnings"])
        
    # 8. Compute Forgery Heuristics & Score
    indicators = []
    forgery_score = 0
    
    # Heuristic A: Missing / Invalid UTR (+25)
    if not primary_utr or not primary_utr["valid"]:
        score_add = 25
        forgery_score += score_add
        evidence_str = primary_utr["evidence"] if primary_utr else "No transaction UTR reference found in receipt text."
        indicators.append({
            "rule": "invalid_or_missing_utr",
            "score": score_add,
            "detail": f"Missing or invalid UTR reference. {evidence_str}"
        })
        
    # Heuristic B: App brand color mismatch (+15)
    if not color_result["color_authentic"]:
        score_add = 15
        forgery_score += score_add
        ref_color = color_result["reference_color"]
        dist = color_result["distance"]
        indicators.append({
            "rule": "brand_color_mismatch",
            "score": score_add,
            "detail": f"Color profile does not match expected brand template for {app_detected} (ref: {ref_color}, dist: {dist})."
        })
        
    # Heuristic C: ELA Tamper Suspected (+30)
    if ela_result["tamper_suspected"]:
        score_add = 30
        forgery_score += score_add
        indicators.append({
            "rule": "ela_tamper_detected",
            "score": score_add,
            "detail": f"Error Level Analysis indicates potential image overlay editing (hotspot: {ela_result['hotspot_ratio']})."
        })
        
    # Heuristic D: Font inconsistency (+20)
    if not font_result["font_consistent"]:
        score_add = 20
        forgery_score += score_add
        indicators.append({
            "rule": "font_inconsistent",
            "score": score_add,
            "detail": f"Text bounding-box heights vary significantly (variance: {font_result['height_variance']}), hinting at spliced fonts."
        })
        
    # Heuristic E: OCR low confidence/empty (+10)
    if ocr_result["confidence"] < 0.50 or not ocr_text.strip():
        score_add = 10
        forgery_score += score_add
        indicators.append({
            "rule": "low_ocr_confidence",
            "score": score_add,
            "detail": f"Receipt OCR text confidence is low ({round(ocr_result['confidence'], 2)}), or text is unreadable."
        })
        
    # Heuristic F: Suspicious keywords / status mismatch (+10)
    suspicious_kws = ["scam", "refund", "failed", "reversed", "fake", "cancelled", "void", "generated"]
    matched_kws = [kw for kw in suspicious_kws if kw in ocr_text.lower()]
    if matched_kws:
        score_add = 10
        forgery_score += score_add
        indicators.append({
            "rule": "suspicious_keywords",
            "score": score_add,
            "detail": f"Receipt contains suspicious keywords suggesting failure or generation tools: {', '.join(matched_kws)}."
        })
        
    # Cap score at 100
    forgery_score = min(100, forgery_score)
    
    # Verdict Assignment
    # 0-29 GENUINE, 30-59 SUSPICIOUS, 60-100 LIKELY_FORGED
    if forgery_score >= 60:
        verdict = "LIKELY_FORGED"
    elif forgery_score >= 30:
        verdict = "SUSPICIOUS"
    else:
        verdict = "GENUINE"
        
    # 9. Try using trained ML model if available
    feature_contributions = []
    try:
        from ml.registry import get_registry
        from ml.features.upi_features import extract_upi_features, get_feature_names

        registry = get_registry()
        if registry.is_available("upi"):
            temp_result = {
                "forgery_score": forgery_score,
                "utr": primary_utr,
                "ela": ela_result,
                "font": font_result,
                "color": color_result,
                "ocr": ocr_result,
                "app_detected": app_detected,
            }
            feats = extract_upi_features(temp_result)
            prob = registry.predict_proba("upi", feats)
            forgery_score = round(prob * 100)

            # Update verdict
            if forgery_score >= 60:
                verdict = "LIKELY_FORGED"
            elif forgery_score >= 30:
                verdict = "SUSPICIOUS"
            else:
                verdict = "GENUINE"

            # Use SHAP explanation for XAI contributions
            from app.core.xai import get_feature_contributions
            model_obj = registry._models["upi"]
            feature_names = get_feature_names()
            feature_contributions = get_feature_contributions(
                model=model_obj,
                features=feats,
                feature_names=feature_names
            )
        else:
            from app.core.xai import get_feature_contributions
            feature_contributions = get_feature_contributions(indicators=indicators)
    except Exception as e:
        logger.warning(f"ML/SHAP UPI scoring failed: {e}")
        try:
            from app.core.xai import get_feature_contributions
            feature_contributions = get_feature_contributions(indicators=indicators)
        except Exception:
            feature_contributions = []

    return {
        "analysis_status": "completed",
        "forgery_score": forgery_score,
        "verdict": verdict,
        "app_detected": app_detected,
        "utr": primary_utr,
        "amount_extracted": amount_val,
        "payee_vpa": payee_vpa,
        "sender_upi_id": sender_upi_id,
        "receiver_upi_id": receiver_upi_id,
        "ocr": ocr_result,
        "ela": ela_result,
        "font": font_result,
        "color": color_result,
        "indicators": indicators,
        "feature_contributions": feature_contributions,
        "warnings": warnings
    }
