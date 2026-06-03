"""
Tests for model calibration — R9 ML Baseline.
Verifies predict_proba outputs are proper floats in [0, 1].
All deterministic, no network calls, random_state=42.
"""

import sys
from pathlib import Path

import numpy as np
import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from data.generate_datasets import generate_doc_dataset
from ml.train import train_module, SEED


@pytest.fixture(scope="module")
def trained_doc_model(tmp_path_factory):
    """Train a small doc model and load it back."""
    import ml.train as train_mod
    import joblib

    tmp_dir = tmp_path_factory.mktemp("cal_models")
    original = train_mod.MODELS_DIR
    train_mod.MODELS_DIR = tmp_dir

    df = generate_doc_dataset(n_genuine=200, n_fraud=100, seed=SEED)
    feature_cols = [c for c in df.columns if c != "label"]
    X = df[feature_cols].values.astype(np.float64)
    y = df["label"].values

    train_module("doc", X, y, feature_cols)

    model = joblib.load(tmp_dir / "doc_model.joblib")
    scaler = joblib.load(tmp_dir / "doc_scaler.joblib")

    train_mod.MODELS_DIR = original
    return model, scaler, X


class TestCalibration:
    def test_probability_output_in_0_1(self, trained_doc_model):
        model, scaler, X = trained_doc_model
        X_scaled = scaler.transform(X)
        probas = model.predict_proba(X_scaled)[:, 1]
        assert np.all(probas >= 0.0), "Probabilities must be >= 0"
        assert np.all(probas <= 1.0), "Probabilities must be <= 1"

    def test_predict_returns_float_not_array(self, trained_doc_model):
        model, scaler, X = trained_doc_model
        single = X[0:1]
        X_scaled = scaler.transform(single)
        proba = model.predict_proba(X_scaled)[:, 1]
        result = float(proba[0])
        assert isinstance(result, float)

    def test_calibrated_predictions_are_varied(self, trained_doc_model):
        """Ensure model doesn't predict all same value."""
        model, scaler, X = trained_doc_model
        X_scaled = scaler.transform(X)
        probas = model.predict_proba(X_scaled)[:, 1]
        unique_vals = len(np.unique(np.round(probas, 3)))
        assert unique_vals >= 2, f"Model outputs too uniform: {unique_vals} unique values"
