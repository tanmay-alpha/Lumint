"""
Document Feature Extractor for Lumint DocShield ML Layer.

Extracts 13 numeric features from a DocShield analysis result dictionary.
All outputs are numeric numpy arrays with no NaN or Inf values.
"""

import numpy as np
from typing import Dict, Any, List

DOC_FEATURE_NAMES = [
    "ela_mean",
    "ela_std",
    "ela_max",
    "ela_high_pixel_ratio",
    "metadata_anomaly_score",
    "file_size_kb",
    "page_count",
    "font_count",
    "image_count",
    "creation_to_mod_delta_days",
    "has_javascript",
    "has_encryption",
    "text_extraction_failed",
]


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


def extract_doc_features(result: Dict[str, Any]) -> np.ndarray:
    """
    Extract exactly 13 features from a DocShield analysis result dictionary.
    Returns numpy array of shape (13,), all numeric, no NaN.

    Expected keys in result dict (may be nested under 'ela', 'metadata', etc.):
        - ela.mean, ela.std, ela.max, ela.high_pixel_ratio
        - metadata flags count
        - file_size, page_count, font_count, image_count
        - creation/modification delta
        - javascript, encryption, text extraction status
    """
    if not result or not isinstance(result, dict):
        return np.zeros(13, dtype=np.float64)

    features = np.zeros(13, dtype=np.float64)

    # ELA features — may be nested under 'ela' key or flat
    ela = result.get("ela", {}) if isinstance(result.get("ela"), dict) else {}

    features[0] = _safe_float(ela.get("ela_mean") or result.get("ela_mean"), 0.0)
    features[1] = _safe_float(ela.get("ela_std") or result.get("ela_std"), 0.0)
    features[2] = _safe_float(ela.get("ela_max") or result.get("ela_max"), 0.0)
    features[3] = _safe_float(
        ela.get("ela_high_pixel_ratio")
        or ela.get("hotspot_ratio")
        or result.get("ela_high_pixel_ratio"),
        0.0,
    )

    # Metadata anomaly score: count of triggered metadata flags (0-5)
    metadata = result.get("metadata", {}) if isinstance(result.get("metadata"), dict) else {}
    indicators = result.get("indicators", [])
    if isinstance(indicators, list):
        meta_flags = sum(
            1
            for ind in indicators
            if isinstance(ind, dict) and "metadata" in str(ind.get("rule", "")).lower()
        )
    else:
        meta_flags = 0
    features[4] = min(
        _safe_float(result.get("metadata_anomaly_score", meta_flags)),
        5.0,
    )

    # File size in KB
    file_size_bytes = _safe_float(result.get("file_size") or result.get("file_size_bytes"), 0.0)
    features[5] = file_size_bytes / 1024.0

    # Page count
    features[6] = _safe_float(result.get("page_count") or result.get("pages"), 0.0)

    # Font count
    features[7] = _safe_float(result.get("font_count") or result.get("fonts"), 0.0)

    # Image count
    features[8] = _safe_float(result.get("image_count") or result.get("images"), 0.0)

    # Creation to modification delta in days
    features[9] = _safe_float(
        result.get("creation_to_mod_delta_days")
        or metadata.get("creation_to_mod_delta_days"),
        -1.0,
    )

    # Has JavaScript (PDF only)
    features[10] = 1.0 if result.get("has_javascript") or metadata.get("has_javascript") else 0.0

    # Has encryption
    features[11] = 1.0 if result.get("has_encryption") or result.get("is_encrypted") else 0.0

    # Text extraction failed
    features[12] = 1.0 if result.get("text_extraction_failed") or result.get("ocr_failed") else 0.0

    features = np.nan_to_num(features, nan=0.0, posinf=0.0, neginf=0.0)
    return features


def get_feature_names() -> List[str]:
    """Return ordered feature name list for the 13-dim vector."""
    return list(DOC_FEATURE_NAMES)
