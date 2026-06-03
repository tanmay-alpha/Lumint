"""
UPI Feature Extractor for Lumint UPI Shield ML Layer.

Extracts 8 numeric features from a UPI analysis result dictionary.
All outputs are numeric numpy arrays with no NaN or Inf values.
"""

import numpy as np
from typing import Dict, Any, List

UPI_FEATURE_NAMES = [
    "forgery_score_heuristic",
    "utr_valid",
    "utr_length",
    "ela_tamper_regions",
    "font_consistent",
    "color_authentic",
    "ocr_confidence",
    "app_detected_encoded",
]

APP_ENCODING = {
    "phonepe": 0,
    "phonepay": 0,
    "googlepay": 1,
    "google pay": 1,
    "gpay": 1,
    "paytm": 2,
    "unknown": 3,
}


def _safe_float(val: Any, default: float = 0.0) -> float:
    """Safely convert value to float, returning default on failure."""
    if val is None:
        return default
    try:
        result = float(val)
        if np.isnan(result) or np.isinf(result):
            return default
        return result
    except (ValueError, TypeError):
        return default


def extract_upi_features(result: Dict[str, Any]) -> np.ndarray:
    """
    Extract exactly 8 features from a UPI analysis result dictionary.
    Returns numpy array of shape (8,), all numeric, no NaN.

    Expected keys in result dict:
        - forgery_score (0-100)
        - utr: {valid, normalized}
        - ela: {hotspot_ratio, tamper_suspected}
        - font: {font_consistent}
        - color: {color_authentic}
        - ocr: {confidence}
        - app_detected
    """
    if not result or not isinstance(result, dict):
        return np.zeros(8, dtype=np.float64)

    features = np.zeros(8, dtype=np.float64)

    # 0: forgery_score_heuristic (0-100 → normalized to 0-1)
    forgery_raw = _safe_float(result.get("forgery_score") or result.get("risk_score"), 0.0)
    features[0] = min(forgery_raw, 100.0) / 100.0

    # 1: utr_valid (binary)
    utr_info = result.get("utr", {}) if isinstance(result.get("utr"), dict) else {}
    features[1] = 1.0 if utr_info.get("valid") else 0.0

    # 2: utr_length
    utr_norm = utr_info.get("normalized") or ""
    features[2] = float(len(str(utr_norm))) if utr_norm else 0.0

    # 3: ela_tamper_regions
    ela = result.get("ela", {}) if isinstance(result.get("ela"), dict) else {}
    features[3] = _safe_float(
        ela.get("tamper_regions")
        or ela.get("hotspot_ratio")
        or result.get("ela_tamper_regions"),
        0.0,
    )

    # 4: font_consistent (binary)
    font = result.get("font", {}) if isinstance(result.get("font"), dict) else {}
    features[4] = 1.0 if font.get("font_consistent", result.get("font_consistent")) else 0.0

    # 5: color_authentic (binary)
    color = result.get("color", {}) if isinstance(result.get("color"), dict) else {}
    features[5] = 1.0 if color.get("color_authentic", result.get("color_authentic")) else 0.0

    # 6: ocr_confidence (0-100 → normalized to 0-1)
    ocr = result.get("ocr", {}) if isinstance(result.get("ocr"), dict) else {}
    ocr_conf = _safe_float(
        ocr.get("confidence") or result.get("ocr_confidence"), 0.0
    )
    features[6] = min(ocr_conf, 100.0) / 100.0

    # 7: app_detected_encoded
    app_raw = str(result.get("app_detected", "unknown")).lower().strip()
    features[7] = float(APP_ENCODING.get(app_raw, 3))

    features = np.nan_to_num(features, nan=0.0, posinf=0.0, neginf=0.0)
    return features


def get_feature_names() -> List[str]:
    """Return ordered feature name list for the 8-dim vector."""
    return list(UPI_FEATURE_NAMES)
