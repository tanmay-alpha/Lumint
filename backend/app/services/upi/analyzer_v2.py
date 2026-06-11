"""
UPI Analyzer v2 — Enhanced version with 80+ feature ensemble model integration.

Integrates alongside the rule-based analyzer as a shadow model, running
the same image through a richer feature extractor and ensemble prediction
to contribute to XAI without replacing the heuristic logic.

Features:
- Uses UPIFeatureExtractorV2 (80+ features)
- Loads ensemble of 4 models (RF+GB+XGB+LGB) when available
- Provides calibrated probabilities and SHAP explanations
- Falls back gracefully if model files missing
"""
import logging
import re
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

from app.services.upi.ocr_adapter import extract_text_from_image
from app.services.upi.app_detector import detect_upi_app
from app.services.upi.utr import extract_utr_candidates, validate_utr
from app.services.upi.color_profile import check_color_authenticity
from app.services.upi.screenshot_forensics import run_image_ela
from app.services.upi.font_consistency import check_font_consistency

logger = logging.getLogger("lumint.services.upi.analyzer_v2")

# Load the v2 ensemble model if available
_V2_LOADED = False
_V2_SCALER = None
_V2_MODELS = None
_V2_CALIBRATOR = None


def _load_v2_models() -> bool:
    """Load ensemble models, scaler, and calibrator if available."""
    global _V2_LOADED, _V2_SCALER, _V2_MODELS, _V2_CALIBRATOR
    if _V2_LOADED:
        return True

    try:
        import joblib
        from ml.features.upi_features_v2 import UPIFeatureExtractorV2

        # Resolve the ml/models directory relative to the backend root.
        # Try both the conventional layout (backend/ml/models) and the in-app
        # layout (backend/app/ml/models).
        candidates = [
            Path(__file__).resolve().parents[3] / "ml" / "models",  # backend/ml/models
            Path(__file__).resolve().parents[2] / "ml" / "models",  # backend/app/ml/models
        ]
        model_path = next((p for p in candidates if p.exists()), candidates[0])
        scaler_path = model_path / "upi_v2_scaler.joblib"
        models_path = model_path / "upi_v2_models.joblib"
        calibrator_path = model_path / "upi_v2_calibrator.joblib"

        if not (scaler_path.exists() and models_path.exists() and calibrator_path.exists()):
            logger.info("V2 models not found — will run in heuristic-only mode")
            return False

        _V2_SCALER = joblib.load(scaler_path)
        _V2_MODELS = joblib.load(models_path)
        _V2_CALIBRATOR = joblib.load(calibrator_path)
        _V2_LOADED = True
        logger.info("V2 ensemble model loaded: %d models", len(_V2_MODELS))
        return True
    except Exception as e:
        logger.warning("Failed to load V2 models: %s", e)
        return False


def predict_with_ensemble(
    image_path: str,
    ocr_text: str,
    primary_utr: Optional[Dict[str, Any]],
    app_detected: str,
    ela_result: Dict[str, Any],
    font_result: Dict[str, Any],
    color_result: Dict[str, Any],
    ocr_result: Dict[str, Any],
) -> Tuple[float, Dict[str, Any]]:
    """
    Get ensemble prediction and feature contributions for a UPI screenshot.

    Returns:
        calibrated_risk_score: float (0-100)
        feature_contributions: list of dicts for XAI
        model_info: dict with metadata
    """
    if not _load_v2_models():
        return 50.0, {}, {"available": False}

    try:
        from ml.features.upi_features_v2 import UPIFeatureExtractorV2
        import numpy as np
        from app.core.xai import get_feature_contributions

        extractor = UPIFeatureExtractorV2()
        features = extractor.extract(
            image_path,
            ocr_text=ocr_text,
            ocr_confidence=ocr_result.get("confidence", 0.5),
        )

        # Scale
        features_scaled = _V2_SCALER.transform(features.reshape(1, -1))

        # Ensemble average
        probas = [m.predict_proba(features_scaled)[:, 1] for m in _V2_MODELS.values()]
        ensemble_proba = np.mean(probas, axis=0)[0]

        # Calibrate
        calibrated_proba = _V2_CALIBRATOR.predict_proba([[ensemble_proba]])[0, 1]
        risk_score = round(calibrated_proba * 100)

        # SHAP explanation (if available)
        feature_contributions = []
        try:
            model_obj = list(_V2_MODELS.values())[0]  # Use RF for SHAP
            feature_contributions = get_feature_contributions(
                model=model_obj,
                features=features,
                feature_names=extractor.FEATURE_NAMES
            )
        except Exception as e:
            logger.warning("SHAP failed for V2: %s", e)

        model_info = {
            "available": True,
            "ensemble_size": len(_V2_MODELS),
            "models": list(_V2_MODELS.keys()),
            "risk_score": risk_score,
            "calibrated_proba": round(float(calibrated_proba), 3),
        }

        return risk_score, feature_contributions, model_info

    except Exception as e:
        logger.error("V2 prediction failed: %s", e)
        return 50.0, {}, {"available": False, "error": str(e)}


def extract_for_v2(image_path: Path) -> Dict[str, Any]:
    """Extract all needed data for V2 prediction from an image."""
    # OCR
    ocr_result = extract_text_from_image(image_path)

    # App detection (extract colors)
    dominant_colors = []
    try:
        from app.services.upi.color_profile import extract_dominant_colors
        dominant_colors = extract_dominant_colors(image_path)
    except Exception:
        pass

    app_result = detect_upi_app(ocr_result["text"], dominant_colors=[c["hex"] for c in dominant_colors])

    # UTR candidates
    utr_candidates = extract_utr_candidates(ocr_result["text"])
    primary_utr = utr_candidates[0] if utr_candidates else None
    if primary_utr and app_result["app"]:
        primary_utr = validate_utr(primary_utr["value"], app_hint=app_result["app"])

    # Extract forensics
    ela_result = run_image_ela(image_path)
    font_result = check_font_consistency(image_path, ocr_text=ocr_result["text"])
    color_result = check_color_authenticity(image_path, app_detected=app_result["app"])

    return {
        "ocr_text": ocr_result["text"],
        "primary_utr": primary_utr,
        "app_detected": app_result["app"],
        "ela_result": ela_result,
        "font_result": font_result,
        "color_result": color_result,
        "ocr_result": ocr_result,
    }


def analyze_upi_v2(image_path: Path) -> Dict[str, Any]:
    """
    Run the V2 enhanced UPI analysis with ensemble model.
    This should be called alongside the original analyzer.
    """
    # Extract needed data
    data = extract_for_v2(image_path)

    # Get ensemble prediction
    risk_score, contributions, model_info = predict_with_ensemble(
        str(image_path),
        data["ocr_text"],
        data["primary_utr"],
        data["app_detected"],
        data["ela_result"],
        data["font_result"],
        data["color_result"],
        data["ocr_result"]
    )

    # Compute verdict
    if risk_score >= 60:
        verdict = "LIKELY_FORGED"
    elif risk_score >= 30:
        verdict = "SUSPICIOUS"
    else:
        verdict = "GENUINE"

    return {
        "v2_risk_score": risk_score,
        "v2_verdict": verdict,
        "v2_model_info": model_info,
        "v2_feature_contributions": contributions,
        "confidence_in_v2": model_info.get("calibrated_proba", 0.0),
    }


if __name__ == "__main__":
    # Example usage: test V2 loading
    if _load_v2_models():
        print("V2 models loaded successfully")
    else:
        print("V2 models not available")