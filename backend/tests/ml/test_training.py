"""
Tests for ML training pipeline — R9 ML Baseline.
Runs training on small subsets to verify output format and sanity gates.
All deterministic, no network calls, random_state=42.
"""

import sys
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from data.generate_datasets import generate_phishing_dataset, generate_doc_dataset, generate_upi_dataset
from ml.features.url_features import extract_lexical_features, fit_tfidf, get_tfidf_features
from ml.train import train_module, SEED


@pytest.fixture(scope="module")
def small_phishing_data():
    """Generate small phishing dataset for fast testing."""
    df = generate_phishing_dataset(n_legit=200, n_phish=100, seed=SEED)
    urls = df["url"].tolist()
    labels = df["label"].values

    vectorizer = fit_tfidf(urls, random_state=SEED)
    X_list = []
    for url in urls:
        lexical = extract_lexical_features(url)
        tfidf = get_tfidf_features(url, vectorizer)
        X_list.append(np.concatenate([lexical, tfidf]))
    X = np.array(X_list, dtype=np.float64)
    return X, labels, vectorizer


@pytest.fixture(scope="module")
def small_doc_data():
    """Generate small document dataset for fast testing."""
    df = generate_doc_dataset(n_genuine=200, n_fraud=100, seed=SEED)
    feature_cols = [c for c in df.columns if c != "label"]
    X = df[feature_cols].values.astype(np.float64)
    y = df["label"].values
    return X, y, feature_cols


@pytest.fixture(scope="module")
def small_upi_data():
    """Generate small UPI dataset for fast testing."""
    df = generate_upi_dataset(n_genuine=150, n_fake=75, seed=SEED)
    feature_cols = [c for c in df.columns if c != "label"]
    X = df[feature_cols].values.astype(np.float64)
    y = df["label"].values
    return X, y, feature_cols


@pytest.fixture(scope="module")
def phish_metrics(small_phishing_data, tmp_path_factory):
    """Train phish model and return metrics."""
    import ml.train as train_mod
    # Redirect models dir to tmp
    original_dir = train_mod.MODELS_DIR
    tmp_dir = tmp_path_factory.mktemp("models")
    train_mod.MODELS_DIR = tmp_dir

    X, y, vectorizer = small_phishing_data
    feature_names = [f"f_{i}" for i in range(X.shape[1])]
    result = train_module("phish", X, y, feature_names, tfidf_vectorizer=vectorizer)

    train_mod.MODELS_DIR = original_dir
    return result, tmp_dir


@pytest.fixture(scope="module")
def doc_metrics(small_doc_data, tmp_path_factory):
    """Train doc model and return metrics."""
    import ml.train as train_mod
    original_dir = train_mod.MODELS_DIR
    tmp_dir = tmp_path_factory.mktemp("models_doc")
    train_mod.MODELS_DIR = tmp_dir

    X, y, feature_cols = small_doc_data
    result = train_module("doc", X, y, feature_cols)

    train_mod.MODELS_DIR = original_dir
    return result, tmp_dir


class TestTrainingPipeline:
    def test_train_phish_produces_metrics_json(self, phish_metrics):
        result, tmp_dir = phish_metrics
        metrics_path = tmp_dir / "phish_metrics.json"
        assert metrics_path.exists()

    def test_metrics_json_has_all_required_keys(self, phish_metrics):
        result, _ = phish_metrics
        required = ["module", "best_model", "cv_results", "test_set",
                     "n_train", "n_test", "random_state", "timestamp"]
        for key in required:
            assert key in result, f"Missing key: {key}"

    def test_cv_results_has_three_models(self, phish_metrics):
        result, _ = phish_metrics
        cv = result["cv_results"]
        assert len(cv) == 3
        for model_name in ["LogisticRegression", "RandomForest", "GradientBoosting"]:
            assert model_name in cv

    def test_f1_above_0_75(self, phish_metrics):
        """Sanity gate: best model F1 should be reasonable."""
        result, _ = phish_metrics
        best = result["best_model"]
        f1 = result["cv_results"][best]["f1"]
        assert f1 >= 0.75, f"F1 too low: {f1}. Model may not be learning."

    def test_auc_above_0_80(self, phish_metrics):
        """Sanity gate: best model AUC should be above 0.80."""
        result, _ = phish_metrics
        best = result["best_model"]
        auc = result["cv_results"][best]["auc"]
        assert auc >= 0.80, f"AUC too low: {auc}."

    def test_doc_f1_reasonable(self, doc_metrics):
        result, _ = doc_metrics
        best = result["best_model"]
        f1 = result["cv_results"][best]["f1"]
        assert f1 >= 0.75, f"Doc F1 too low: {f1}"

    def test_model_file_saved(self, phish_metrics):
        _, tmp_dir = phish_metrics
        assert (tmp_dir / "phish_model.joblib").exists()
        assert (tmp_dir / "phish_scaler.joblib").exists()

    def test_feature_names_saved(self, phish_metrics):
        _, tmp_dir = phish_metrics
        path = tmp_dir / "phish_feature_names.json"
        assert path.exists()
        with open(path) as f:
            names = json.load(f)
        assert isinstance(names, list)
        assert len(names) > 0

    def test_random_state_is_42(self, phish_metrics):
        result, _ = phish_metrics
        assert result["random_state"] == 42
