import re
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

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


# Layout keywords that, when followed by a VPA, identify it as the *payee*
# (i.e. the party being paid). UPI receipts typically label the recipient
# with "Paid to" or "To:" or "Received by". We use these to disambiguate
# the sender-vs-receiver VPAs so that "payee_vpa" reflects the right one.
_PAYEE_LABEL_KEYWORDS = ("paid to", "to:", "received by", "credited to")


def select_payee_vpa(text: str, vpas: List[str]) -> Optional[str]:
    """
    Pick the *payee* VPA from a list using layout cues.

    Strategy:
      1. If the OCR text contains a "Paid to"/"To:"/"Received by"/"Credited to"
         label, prefer the first VPA appearing *after* that label — that's
         almost always the receiver on a UPI receipt.
      2. Fall back to the last VPA in the list. On a typical PhonePe/GPay
         receipt the sender VPA appears at the top and the receiver VPA
         near the bottom near the amount line, so the last VPA is a
         reasonable default when no label is found.
      3. Return None if there are no VPAs.
    """
    if not vpas:
        return None

    text_lower = text.lower()
    for keyword in _PAYEE_LABEL_KEYWORDS:
        idx = text_lower.find(keyword)
        if idx < 0:
            continue
        tail = text_lower[idx:]
        for vpa in vpas:
            if vpa.lower() in tail:
                return vpa

    return vpas[-1]

def _is_upi_screenshot(ocr_text: str) -> bool:
    """
    Gate check: returns True only if OCR text contains enough UPI signals
    to be worth running the full forensic pipeline.
    A LinkedIn chat, random photo, meme etc. will return False.
    """
    text_lower = ocr_text.lower()

    # Hard positive signals — any ONE of these is enough
    strong_signals = [
        "phonepe", "gpay", "google pay", "paytm", "bhim",
        "upi", "utr", "transaction id", "txn id", "ref no",
        "payment successful", "paid to", "sent to", "received from",
        "okaxis", "okhdfcbank", "oksbi", "okicici", "ybl", "ibl",
        "payment", "₹", "rs.", "inr",
    ]

    # VPA pattern (@axis, @okaxis, etc.)
    has_vpa = bool(re.search(r'\b[a-zA-Z0-9.\-_]+@[a-zA-Z0-9]+\b', ocr_text))
    # 12-digit number (UTR)
    has_utr_candidate = bool(re.search(r'\b\d{12}\b', ocr_text))

    hit_count = sum(1 for sig in strong_signals if sig in text_lower)

    # Require at least 2 strong signals OR a VPA + 1 signal OR a 12-digit candidate + 1 signal
    if hit_count >= 2:
        return True
    if has_vpa and hit_count >= 1:
        return True
    if has_utr_candidate and hit_count >= 1:
        return True
    return False


_NOT_UPI_RESULT_TEMPLATE = {
    "analysis_status": "not_upi_screenshot",
    "forgery_score": 95,
    "verdict": "NOT_UPI_SCREENSHOT",
    "app_detected": "Unknown",
    "utr": None,
    "amount_extracted": None,
    "payee_vpa": None,
    "sender_upi_id": "N/A",
    "receiver_upi_id": "N/A",
    "score_source": "heuristic",
    "ocr": {"text": "", "confidence": 0.0, "method": "none", "warnings": []},
    "ela": {
        "ela_score": 0,
        "tamper_suspected": False,
        "hotspot_ratio": 0.0,
        "mean_difference": 0.0,
        "max_difference": 0,
        "tamper_regions": [],
        "warnings": [],
    },
    "font": {
        "font_consistent": False,
        "confidence": 0.0,
        "component_count": 0,
        "height_variance": None,
        "warnings": [],
    },
    "color": {
        "color_authentic": False,
        "confidence": 0.0,
        "dominant_colors": [],
        "reference_color": None,
        "distance": None,
        "warnings": [],
    },
    "indicators": [
        {
            "rule": "not_upi_screenshot",
            "score": 95,
            "detail": (
                "The uploaded image does not appear to be a UPI payment screenshot. "
                "No UPI-specific signals (UTR, VPA, app name, ₹ symbol, 'payment successful', etc.) "
                "were detected in the OCR text. "
                "Please upload a PhonePe, Google Pay, Paytm, or BHIM payment receipt screenshot."
            ),
        }
    ],
    "feature_contributions": [],
    "warnings": [
        "NOT A UPI SCREENSHOT: The image you uploaded does not look like a UPI payment receipt. "
        "The analysis pipeline was aborted to prevent false positives."
    ],
}


# ──────────────────────────────────────────────────────────────────────
# Pipeline step helpers (extracted from the long orchestrator)
# ──────────────────────────────────────────────────────────────────────


def _gate_check(ocr_text: str, ocr_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Return a NOT_UPI_RESULT template if the image is not a UPI screenshot, else None.

    This is the early-exit gate that prevents false positives on LinkedIn
    chats, random photos, etc. The returned dict is the standard envelope
    that the caller can return directly.
    """
    if _is_upi_screenshot(ocr_text):
        return None
    # Log only the *length* of the OCR text, not the text itself. OCR
    # text routinely contains UPI IDs, UTR numbers, payee VPAs, and
    # transaction amounts — all of which are PII. If a log aggregator
    # ever ingests this, every screenshot a user uploads ends up in
    # plaintext. Operators who need to debug a non-UPI classification
    # can ask the user to re-upload with verbose-mode enabled; we do
    # not pay that risk in the default path.
    logger.warning(
        "Non-UPI image detected. OCR text length=%d chars", len(ocr_text),
    )
    result = dict(_NOT_UPI_RESULT_TEMPLATE)
    result["ocr"] = ocr_result
    return result


def _extract_metadata(ocr_text: str) -> Dict[str, Any]:
    """Extract UTR, amount, payee/sender VPAs from OCR text.

    Returns a dict with keys: primary_utr, amount, payee_vpa, sender_vpa.
    """
    utr_candidates = extract_utr_candidates(ocr_text)
    primary_utr = utr_candidates[0] if utr_candidates else None
    vpas = parse_vpas(ocr_text)
    return {
        "primary_utr": primary_utr,
        "amount": parse_amount(ocr_text),
        "payee_vpa": select_payee_vpa(ocr_text, vpas),
        "sender_vpa": vpas[0] if vpas else None,
    }


def _detect_app(image_path: Path, ocr_text: str) -> str:
    """Run app detection (PhonePe / GPay / Paytm / etc.) and return the app name."""
    dominant_hex_list: Optional[List[str]] = None
    try:
        from app.services.upi.color_profile import extract_dominant_colors
        dominant_colors_info = extract_dominant_colors(image_path)
        dominant_hex_list = [item["hex"] for item in dominant_colors_info] or None
    except Exception as e:
        logger.debug("Failed to pre-extract colors for app detection: %s", e)
    app_result = detect_upi_app(ocr_text, dominant_colors=dominant_hex_list)
    return app_result["app"]


def _run_forensics(
    image_path: Path,
    ocr_text: str,
    app_detected: str,
) -> Dict[str, Any]:
    """Run ELA + font consistency + color authenticity in sequence.

    Returns a dict with keys: ela, font, color. Each is the raw result
    of the corresponding service.
    """
    return {
        "ela": run_image_ela(image_path),
        "font": check_font_consistency(
            image_path,
            ocr_text=ocr_text,
            app_hint=app_detected,
        ),
        "color": check_color_authenticity(image_path, app_detected=app_detected),
    }


def _collect_forensic_warnings(forensics: Dict[str, Any]) -> List[str]:
    """Flatten the warnings from each forensic signal into a single list."""
    out: List[str] = []
    for key in ("ela", "font", "color"):
        for w in forensics.get(key, {}).get("warnings", []) or []:
            out.append(w)
    return out


def _compute_heuristic_score(
    primary_utr: Optional[Dict[str, Any]],
    forensics: Dict[str, Any],
    ocr_result: Dict[str, Any],
    ocr_text: str,
    app_detected: str,
) -> Tuple[int, List[Dict[str, Any]]]:
    """Apply rule-based forgery detection. Returns (score, indicators).

    Score is capped at 100. Indicators are a list of {rule, score, detail}
    dicts that explain which rules fired. Each rule fires independently.
    """
    indicators: List[Dict[str, Any]] = []
    score = 0

    ela_result = forensics.get("ela", {})
    font_result = forensics.get("font", {})
    color_result = forensics.get("color", {})

    # Rule A: Invalid UTR (+25)
    if not primary_utr or not primary_utr.get("valid"):
        add = 25
        score += add
        evidence = primary_utr["evidence"] if primary_utr else "No transaction UTR reference found in receipt text."
        indicators.append({
            "rule": "invalid_or_missing_utr",
            "score": add,
            "detail": f"Missing or invalid UTR reference. {evidence}",
        })

    # Rule B: App brand color mismatch (+15)
    if not color_result.get("color_authentic"):
        add = 15
        score += add
        indicators.append({
            "rule": "brand_color_mismatch",
            "score": add,
            "detail": (
                f"Color profile does not match expected brand template for {app_detected} "
                f"(ref: {color_result.get('reference_color')}, dist: {color_result.get('distance')})."
            ),
        })

    # Rule C: ELA tamper suspected (+30)
    if ela_result.get("tamper_suspected"):
        add = 30
        score += add
        indicators.append({
            "rule": "ela_tamper_detected",
            "score": add,
            "detail": f"Error Level Analysis indicates potential image overlay editing (hotspot: {ela_result.get('hotspot_ratio')}).",
        })

    # Rule D: Font inconsistency (+20)
    if not font_result.get("font_consistent"):
        add = 20
        score += add
        indicators.append({
            "rule": "font_inconsistent",
            "score": add,
            "detail": f"Text bounding-box heights vary significantly (variance: {font_result.get('height_variance')}), hinting at spliced fonts.",
        })

    # Rule E: OCR low confidence or empty (+10)
    if ocr_result.get("confidence", 1.0) < 0.50 or not ocr_text.strip():
        add = 10
        score += add
        indicators.append({
            "rule": "low_ocr_confidence",
            "score": add,
            "detail": f"Receipt OCR text confidence is low ({round(ocr_result.get('confidence', 0), 2)}), or text is unreadable.",
        })

    # Rule F: Suspicious keywords / status mismatch (+10)
    suspicious_kws = ["scam", "refund", "failed", "reversed", "fake", "cancelled", "void", "generated"]
    matched_kws = [kw for kw in suspicious_kws if kw in ocr_text.lower()]
    if matched_kws:
        add = 10
        score += add
        indicators.append({
            "rule": "suspicious_keywords",
            "score": add,
            "detail": f"Receipt contains suspicious keywords suggesting failure or generation tools: {', '.join(matched_kws)}.",
        })

    return min(100, score), indicators


def _score_to_verdict(score: int) -> str:
    """Map a numeric score (0-100) to a categorical verdict."""
    if score >= 60:
        return "LIKELY_FORGED"
    if score >= 30:
        return "SUSPICIOUS"
    return "GENUINE"


def _compute_confidence(score: int, indicators: List[Dict[str, Any]]) -> float:
    """Confidence is higher when the score and the rule set agree.

    Blends the score (0-100) and the average per-indicator score. Returns
    a float in [0, 1].
    """
    if not indicators:
        return 0.5
    avg_indicator_score = sum(i["score"] for i in indicators) / len(indicators)
    return min(1.0, max(0.0, score / 100.0 * 0.7 + avg_indicator_score / 50.0 * 0.3))


def _apply_ml_overlay(
    primary_utr: Optional[Dict[str, Any]],
    forensics: Dict[str, Any],
    ocr_result: Dict[str, Any],
    app_detected: str,
    heuristic_score: int,
) -> Tuple[int, List[Dict[str, Any]], str]:
    """Run the trained ML model on top of the heuristic score.

    Returns (final_score, feature_contributions, score_source).
    On any error, returns the heuristic score unchanged and
    `feature_contributions=[]`.
    """
    try:
        from ml.registry import get_registry
        from ml.features.upi_features import extract_upi_features, get_feature_names
        from app.core.xai import get_feature_contributions

        registry = get_registry()
        if registry.is_available("upi"):
            temp_result = {
                "forgery_score": heuristic_score,
                "utr": primary_utr,
                "ela": forensics.get("ela", {}),
                "font": forensics.get("font", {}),
                "color": forensics.get("color", {}),
                "ocr": ocr_result,
                "app_detected": app_detected,
            }
            feats = extract_upi_features(temp_result)
            prob = registry.predict_proba("upi", feats)
            final_score = round(prob * 100)
            feature_contributions = get_feature_contributions(
                model=registry._models["upi"],
                features=feats,
                feature_names=get_feature_names(),
            )
            return final_score, feature_contributions, "ml"
    except Exception as e:
        logger.warning("ML/SHAP UPI scoring failed: %s", e)

    # Fallback: heuristic only
    try:
        from app.core.xai import get_feature_contributions
        # Indicators are passed in by the caller via the score source; here we just
        # return an empty contributions list to keep the function signature simple.
        return heuristic_score, [], "heuristic"
    except Exception:
        return heuristic_score, [], "heuristic"


def analyze_upi_screenshot(image_path: Path, custom_ocr_text: Optional[str] = None) -> Dict[str, Any]:
    """
    Unified UPI Shield Analysis Pipeline.

    Reads as a clear 5-step pipeline. Each step has a focused helper
    function above; this entry point is just the orchestration.

    0. Pre-screen: reject non-UPI images immediately with a clear verdict
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
    # Step 1: OCR
    ocr_result = extract_text_from_image(image_path, fallback_text=custom_ocr_text)
    ocr_text = ocr_result["text"]
    warnings: List[str] = list(ocr_result.get("warnings", []) or [])

    # Step 2: Gate check (early exit if not a UPI screenshot)
    not_upi = _gate_check(ocr_text, ocr_result)
    if not_upi is not None:
        base_warnings: List[str] = list(_NOT_UPI_RESULT_TEMPLATE["warnings"])  # type: ignore[arg-type]
        not_upi["warnings"] = base_warnings + warnings
        return not_upi

    # Step 3: Extract metadata
    metadata = _extract_metadata(ocr_text)
    primary_utr = metadata["primary_utr"]

    # Step 4: App detection
    app_detected = _detect_app(image_path, ocr_text)

    # Re-validate primary UTR with app hint if we have one
    if primary_utr:
        primary_utr = validate_utr(primary_utr["value"], app_hint=app_detected)

    # Step 5: Forensics (ELA + font + color)
    forensics = _run_forensics(image_path, ocr_text, app_detected)
    warnings.extend(_collect_forensic_warnings(forensics))

    # Step 6: Heuristic score
    heuristic_score, indicators = _compute_heuristic_score(
        primary_utr, forensics, ocr_result, ocr_text, app_detected,
    )
    verdict = _score_to_verdict(heuristic_score)

    # Step 7: ML overlay (if available) — overrides heuristic
    final_score, feature_contributions, score_source = _apply_ml_overlay(
        primary_utr, forensics, ocr_result, app_detected, heuristic_score,
    )
    if score_source == "ml":
        verdict = _score_to_verdict(final_score)
    else:
        final_score = heuristic_score

    # Step 8: Build response
    payee_vpa = metadata["payee_vpa"]
    vpas = parse_vpas(ocr_text)
    return {
        "analysis_status": "completed",
        "forgery_score": final_score,
        "verdict": verdict,
        "app_detected": app_detected,
        "utr": primary_utr,
        "amount_extracted": metadata["amount"],
        "payee_vpa": payee_vpa,
        "sender_upi_id": metadata["sender_vpa"],
        "receiver_upi_id": payee_vpa if payee_vpa else (vpas[1] if len(vpas) > 1 else None),
        "score_source": score_source,
        "confidence": _compute_confidence(final_score, indicators),
        "ocr": ocr_result,
        "ela": forensics.get("ela", {}),
        "font": forensics.get("font", {}),
        "color": forensics.get("color", {}),
        "indicators": indicators,
        "feature_contributions": feature_contributions,
        "warnings": warnings,
    }
