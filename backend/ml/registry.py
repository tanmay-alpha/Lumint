"""
Lumint ML Model Registry — Singleton pattern.

Loads all trained .joblib models at startup and provides
prediction, availability checking, and fallback interfaces.
"""

import logging
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

import numpy as np

logger = logging.getLogger(__name__)

MODELS_DIR = Path(__file__).resolve().parent / "models"


class ModelRegistry:
    """
    Singleton registry that loads all trained ML models.
    Provides predict_proba, availability checks, and heuristic fallback.
    """

    _instance: Optional["ModelRegistry"] = None

    def __new__(cls) -> "ModelRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._models: Dict[str, Any] = {}
        self._scalers: Dict[str, Any] = {}
        self._tfidf: Dict[str, Any] = {}
        self._metrics: Dict[str, Dict] = {}
        self._feature_names: Dict[str, List[str]] = {}
        self._load_all()

    def _load_all(self):
        """Load all available models from the models directory."""
        if not MODELS_DIR.exists():
            logger.warning(f"Models directory not found: {MODELS_DIR}")
            return

        try:
            import joblib
        except ImportError:
            logger.error("joblib not installed — cannot load ML models")
            return

        for module in ["phish", "doc", "upi", "fusion_meta"]:
            model_path = MODELS_DIR / f"{module}_model.joblib"
            scaler_path = MODELS_DIR / f"{module}_scaler.joblib"

            # fusion_meta has different naming
            if module == "fusion_meta":
                model_path = MODELS_DIR / "fusion_meta.joblib"
                scaler_path = MODELS_DIR / "fusion_meta_scaler.joblib"

            if model_path.exists():
                try:
                    self._models[module] = joblib.load(model_path)
                    logger.info(f"Loaded model: {module} from {model_path}")
                except Exception as e:
                    logger.error(f"Failed to load model {module}: {e}")

            if scaler_path.exists():
                try:
                    self._scalers[module] = joblib.load(scaler_path)
                except Exception as e:
                    logger.error(f"Failed to load scaler {module}: {e}")

            # TF-IDF (phish only)
            tfidf_path = MODELS_DIR / f"{module}_tfidf.joblib"
            if tfidf_path.exists():
                try:
                    self._tfidf[module] = joblib.load(tfidf_path)
                except Exception as e:
                    logger.error(f"Failed to load TF-IDF {module}: {e}")

            # Metrics
            metrics_path = MODELS_DIR / f"{module}_metrics.json"
            if metrics_path.exists():
                try:
                    with open(metrics_path, "r") as f:
                        self._metrics[module] = json.load(f)
                except Exception:
                    pass

            # Feature names
            features_path = MODELS_DIR / f"{module}_feature_names.json"
            if features_path.exists():
                try:
                    with open(features_path, "r") as f:
                        self._feature_names[module] = json.load(f)
                except Exception:
                    pass

        loaded = list(self._models.keys())
        logger.info(f"ModelRegistry loaded {len(loaded)} models: {loaded}")

    def is_available(self, module: str) -> bool:
        """Check if a trained model is available for the given module."""
        return module in self._models and module in self._scalers

    def predict_proba(self, module: str, features: np.ndarray) -> float:
        """
        Predict fraud probability (0-1) for the given module.
        Features should be raw (pre-scaling) — scaler is applied internally.
        Returns a single float, not an array.
        """
        if not self.is_available(module):
            raise ValueError(f"Model not available for module: {module}")

        model = self._models[module]
        scaler = self._scalers[module]

        # Ensure 2D
        if features.ndim == 1:
            features = features.reshape(1, -1)

        # Scale
        features_scaled = scaler.transform(features)

        # Predict probability of positive class
        proba = model.predict_proba(features_scaled)[:, 1]
        result = float(proba[0])

        # Clamp to [0, 1]
        return max(0.0, min(1.0, result))

    def fallback_to_heuristic(self, module: str, heuristic_score: float) -> float:
        """
        Used when model not trained yet.
        Returns the heuristic score normalized to 0-1.
        """
        logger.warning(
            f"ML model not available for '{module}', using heuristic fallback"
        )
        return max(0.0, min(1.0, heuristic_score / 100.0))

    def get_feature_importances(self, module: str) -> List[Dict[str, Any]]:
        """
        Return feature importances for the given module.
        Works with tree-based models (feature_importances_) and
        linear models (coef_).
        """
        if not self.is_available(module):
            return []

        model = self._models[module]
        names = self._feature_names.get(module, [])

        # Unwrap CalibratedClassifierCV to get base estimator
        base = model
        if hasattr(model, "estimator"):
            base = model.estimator
        elif hasattr(model, "calibrated_classifiers_"):
            try:
                base = model.calibrated_classifiers_[0].estimator
            except (IndexError, AttributeError):
                pass

        importances = None

        if hasattr(base, "feature_importances_"):
            importances = base.feature_importances_
        elif hasattr(base, "coef_"):
            importances = np.abs(base.coef_[0])

        if importances is None:
            return []

        # Build name→importance pairs
        results = []
        for i, imp in enumerate(importances):
            name = names[i] if i < len(names) else f"feature_{i}"
            results.append({
                "name": name,
                "importance": round(float(imp), 6),
            })

        # Sort descending
        results.sort(key=lambda x: x["importance"], reverse=True)
        return results

    def get_tfidf(self, module: str = "phish"):
        """Return the TF-IDF vectorizer for URL feature extraction."""
        return self._tfidf.get(module)

    def get_metrics(self, module: str) -> Dict:
        """Return stored training metrics for the given module."""
        return self._metrics.get(module, {})

    @classmethod
    def reset(cls):
        """Reset singleton for testing purposes."""
        cls._instance = None


# Module-level convenience function
_registry: Optional[ModelRegistry] = None


def get_registry() -> ModelRegistry:
    """Get or create the singleton ModelRegistry."""
    global _registry
    if _registry is None:
        _registry = ModelRegistry()
    return _registry
