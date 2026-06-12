"""
Lumint ML Model Registry — Singleton pattern.

Loads all trained .joblib models at startup and provides
prediction, availability checking, and fallback interfaces.

Security
--------
We verify a SHA-256 hash of every model file against an allow-list
shipped in ``models/CHECKSUMS.json`` before deserialising. ``joblib.load``
ultimately calls ``pickle.load`` under the hood, and pickle can execute
arbitrary code at deserialisation time, so loading an attacker-supplied
file would be RCE. The checksum check is the only thing standing between
us and a hostile model artifact.

The checksum file is committed alongside the models in the same git
tree, so an attacker would need to compromise the repository to swap
both the model *and* its expected hash. This is the standard
"trust-on-first-use + signed manifest" model.
"""

import hashlib
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

import numpy as np

logger = logging.getLogger(__name__)

MODELS_DIR = Path(__file__).resolve().parent / "models"
CHECKSUMS_FILE = MODELS_DIR / "CHECKSUMS.json"

# Set to False to skip checksum verification (e.g. for local dev when
# the user has just retrained a model and the CHECKSUMS file hasn't
# been updated yet). The env var is read in :func:`_is_checksum_enforced`.
# Production deployments MUST set this to "1".
import os as _os
_CHECKSUMS_ENFORCED = _os.environ.get("LUMINT_ENFORCE_MODEL_CHECKSUMS", "1") != "0"


def _sha256_of_file(path: Path) -> str:
    """Compute the SHA-256 of a file, streamed so it works on multi-MB models."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(64 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_expected_checksums() -> Dict[str, str]:
    """Load the expected {filename: sha256} map. Returns {} if missing or
    the file is malformed — in which case we'll either log a warning
    (if checksums are enforced) or skip verification (if not)."""
    if not CHECKSUMS_FILE.exists():
        logger.warning(
            "Model checksum manifest not found at %s. "
            "Run `python ml/tools/hash_models.py` to generate it.",
            CHECKSUMS_FILE,
        )
        return {}
    try:
        with open(CHECKSUMS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            logger.error("CHECKSUMS.json is not a dict — ignoring.")
            return {}
        return {str(k): str(v) for k, v in data.items()}
    except Exception as e:
        logger.error("Failed to parse CHECKSUMS.json: %s", e)
        return {}


def _verify_checksum(path: Path, expected_map: Dict[str, str]) -> bool:
    """Returns True if ``path`` matches its expected hash, or if no
    expected hash is recorded AND checksums are not enforced."""
    name = path.name
    expected = expected_map.get(name)
    if expected is None:
        if _CHECKSUMS_ENFORCED:
            logger.error(
                "Model file %s has no entry in CHECKSUMS.json — "
                "refusing to load (set LUMINT_ENFORCE_MODEL_CHECKSUMS=0 "
                "to override in dev).",
                name,
            )
            return False
        logger.warning(
            "Model file %s has no entry in CHECKSUMS.json — loading anyway "
            "(checksums not enforced).",
            name,
        )
        return True
    actual = _sha256_of_file(path)
    if actual != expected:
        logger.error(
            "Checksum mismatch for %s: expected %s, got %s. "
            "REFUSING to load — possible tampering or stale manifest.",
            name, expected, actual,
        )
        return False
    return True


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

        # Pre-compute the expected checksum map once, then verify each
        # file individually before deserialising.
        expected_checksums = _load_expected_checksums()

        for module in ["phish", "doc", "upi", "fusion_meta"]:
            model_path = MODELS_DIR / f"{module}_model.joblib"
            scaler_path = MODELS_DIR / f"{module}_scaler.joblib"

            # fusion_meta has different naming
            if module == "fusion_meta":
                model_path = MODELS_DIR / "fusion_meta.joblib"
                scaler_path = MODELS_DIR / "fusion_meta_scaler.joblib"

            if model_path.exists():
                if not _verify_checksum(model_path, expected_checksums):
                    # Skip this model — its bytes don't match the
                    # committed hash. We never call joblib.load.
                    continue
                try:
                    self._models[module] = joblib.load(model_path)
                    logger.info(f"Loaded model: {module} from {model_path}")
                except Exception as e:
                    logger.error(f"Failed to load model {module}: {e}")

            if scaler_path.exists():
                if not _verify_checksum(scaler_path, expected_checksums):
                    continue
                try:
                    self._scalers[module] = joblib.load(scaler_path)
                except Exception as e:
                    logger.error(f"Failed to load scaler {module}: {e}")

            # TF-IDF (phish only)
            tfidf_path = MODELS_DIR / f"{module}_tfidf.joblib"
            if tfidf_path.exists():
                if not _verify_checksum(tfidf_path, expected_checksums):
                    continue
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
