"""
Tests for ML-based fusion scoring — R9 ML Baseline.
All deterministic, no network calls, random_state=42.
"""

import sys
from pathlib import Path

import numpy as np
import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from ml.train import train_fusion_meta, SEED


@pytest.fixture(scope="module")
def fusion_model(tmp_path_factory):
    """Train fusion meta-learner and load it."""
    import ml.train as train_mod
    import joblib

    tmp_dir = tmp_path_factory.mktemp("fusion_models")
    original = train_mod.MODELS_DIR
    train_mod.MODELS_DIR = tmp_dir

    train_fusion_meta()

    model = joblib.load(tmp_dir / "fusion_meta.joblib")
    scaler = joblib.load(tmp_dir / "fusion_meta_scaler.joblib")

    train_mod.MODELS_DIR = original
    return model, scaler


def _predict_fusion(model, scaler, phish_p, doc_p, upi_p) -> float:
    """Helper to get fusion score (0-100)."""
    features = np.array([[phish_p, doc_p, upi_p]], dtype=np.float64)
    scaled = scaler.transform(features)
    proba = model.predict_proba(scaled)[:, 1]
    return float(proba[0]) * 100.0


class TestFusionML:
    def test_fusion_score_in_0_100(self, fusion_model):
        model, scaler = fusion_model
        score = _predict_fusion(model, scaler, 0.5, 0.5, 0.5)
        assert 0 <= score <= 100, f"Fusion score out of range: {score}"

    def test_high_all_inputs_gives_score_above_70(self, fusion_model):
        model, scaler = fusion_model
        score = _predict_fusion(model, scaler, 0.9, 0.85, 0.95)
        assert score > 70, f"All high inputs should give score > 70, got {score}"

    def test_low_all_inputs_gives_score_below_30(self, fusion_model):
        model, scaler = fusion_model
        score = _predict_fusion(model, scaler, 0.05, 0.1, 0.05)
        assert score < 30, f"All low inputs should give score < 30, got {score}"

    def test_mixed_inputs_reasonable(self, fusion_model):
        model, scaler = fusion_model
        score = _predict_fusion(model, scaler, 0.8, 0.1, 0.2)
        assert 0 <= score <= 100
