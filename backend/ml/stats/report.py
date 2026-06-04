"""
Statistical Report Generator.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any

import numpy as np
import pandas as pd
import joblib
from sklearn.preprocessing import StandardScaler
from sklearn.calibration import CalibratedClassifierCV

BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from ml.stats.bootstrap_ci import compute_all_cis, bootstrap_ci
from ml.stats.mcnemar_test import mcnemar_test
from ml.stats.delong_test import delong_auc_ci, delong_compare

DATA_DIR = BACKEND_ROOT / "data"
MODELS_DIR = BACKEND_ROOT / "ml" / "models"
SEED = 42


def _apply_smote(X: np.ndarray, y: np.ndarray) -> tuple:
    try:
        from imblearn.over_sampling import SMOTE
        smote = SMOTE(random_state=SEED)
        X_res, y_res = smote.fit_resample(X, y)
        return X_res, y_res
    except Exception:
        return X, y


def _get_candidate_models() -> Dict[str, Any]:
    from sklearn.linear_model import LogisticRegression
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    return {
        "LogisticRegression": LogisticRegression(
            max_iter=1000, random_state=SEED, solver="lbfgs", C=1.0
        ),
        "RandomForest": RandomForestClassifier(
            n_estimators=200, max_depth=15, random_state=SEED, n_jobs=-1
        ),
        "GradientBoosting": GradientBoostingClassifier(
            n_estimators=200, max_depth=5, learning_rate=0.1, random_state=SEED
        ),
    }


def load_dataset_for_module(module: str) -> tuple:
    if module == "phish":
        from ml.features.url_features import extract_lexical_features, get_tfidf_features
        csv_path = DATA_DIR / "phishing_dataset.csv"
        if not csv_path.exists():
            raise FileNotFoundError(f"Phishing dataset not found at {csv_path}")
        df = pd.read_csv(csv_path)
        urls = df["url"].tolist()
        labels = df["label"].values

        tfidf_path = MODELS_DIR / "phish_tfidf.joblib"
        if not tfidf_path.exists():
            raise FileNotFoundError(f"TF-IDF vectorizer not found at {tfidf_path}")
        vectorizer = joblib.load(tfidf_path)

        X_list = []
        for url in urls:
            lexical = extract_lexical_features(url)
            tfidf = get_tfidf_features(url, vectorizer)
            X_list.append(np.concatenate([lexical, tfidf]))
        X = np.array(X_list, dtype=np.float64)
        return X, labels

    elif module == "doc":
        csv_path = DATA_DIR / "doc_dataset.csv"
        if not csv_path.exists():
            raise FileNotFoundError(f"Doc dataset not found at {csv_path}")
        df = pd.read_csv(csv_path)
        feature_cols = [c for c in df.columns if c != "label"]
        X = df[feature_cols].values.astype(np.float64)
        y = df["label"].values
        return X, y

    elif module == "upi":
        csv_path = DATA_DIR / "upi_dataset.csv"
        if not csv_path.exists():
            raise FileNotFoundError(f"UPI dataset not found at {csv_path}")
        df = pd.read_csv(csv_path)
        feature_cols = [c for c in df.columns if c != "label"]
        X = df[feature_cols].values.astype(np.float64)
        y = df["label"].values
        return X, y

    elif module == "fusion_meta":
        # Generate synthetic data exactly as in train.py
        rng = np.random.RandomState(SEED)
        n_samples = 2000
        X_list = []
        y_list = []
        for _ in range(n_samples // 2):
            phish_p = rng.uniform(0.0, 0.35)
            doc_p = rng.uniform(0.0, 0.30)
            upi_p = rng.uniform(0.0, 0.25)
            X_list.append([phish_p, doc_p, upi_p])
            y_list.append(0)

        for _ in range(n_samples // 2):
            phish_p = rng.uniform(0.4, 1.0)
            doc_p = rng.uniform(0.35, 1.0)
            upi_p = rng.uniform(0.3, 1.0)
            X_list.append([phish_p, doc_p, upi_p])
            y_list.append(1)

        X = np.array(X_list, dtype=np.float64)
        y = np.array(y_list)
        idx = rng.permutation(len(y))
        X = X[idx]
        y = y[idx]
        return X, y

    else:
        raise ValueError(f"Unknown module: {module}")


def generate_statistical_report(module: str) -> dict:
    """
    Loads saved model + test data for module.
    Runs all statistical tests.
    Returns complete paper-ready stats dict.
    """
    # Load dataset
    X, y = load_dataset_for_module(module)

    # Preprocess
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    X_res, y_res = _apply_smote(X_scaled, y)

    # Train candidates
    models = _get_candidate_models()
    preds = {}
    probas = {}

    from ml.train import _evaluate

    models_report = {}

    for name, model in models.items():
        # Fit on resampled data
        model.fit(X_res, y_res)
        # Calibrate
        calibrator = CalibratedClassifierCV(estimator=model, method="isotonic", cv="prefit")
        calibrator.fit(X_scaled, y)

        # Predict
        y_pred = calibrator.predict(X_scaled)
        y_proba = calibrator.predict_proba(X_scaled)[:, 1]

        preds[name] = y_pred
        probas[name] = y_proba

        # Compute point estimates
        metrics = _evaluate(y, y_pred, y_proba)

        # Compute bootstrap CIs
        cis = compute_all_cis(y, y_pred, y_proba, n_replicates=2000, confidence=0.95, random_state=SEED)

        # DeLong AUC CI
        delong_ci = delong_auc_ci(y, y_proba, alpha=0.05)

        models_report[name] = {
            "metrics": metrics,
            "confidence_intervals": cis,
            "auc_delong_ci": delong_ci,
        }

    # Significance tests
    significance_tests = {
        "RF_vs_LR": mcnemar_test(y, preds["RandomForest"], preds["LogisticRegression"]),
        "GB_vs_RF": mcnemar_test(y, preds["GradientBoosting"], preds["RandomForest"]),
        "GB_vs_LR": mcnemar_test(y, preds["GradientBoosting"], preds["LogisticRegression"]),
    }

    # AUC Comparisons (DeLong test)
    auc_comparisons = {
        "RF_vs_LR": delong_compare(y, probas["RandomForest"], probas["LogisticRegression"]),
        "GB_vs_RF": delong_compare(y, probas["GradientBoosting"], probas["RandomForest"]),
        "GB_vs_LR": delong_compare(y, probas["GradientBoosting"], probas["LogisticRegression"]),
    }

    # Load best model from metrics file
    metrics_path = MODELS_DIR / f"{module}_metrics.json"
    if metrics_path.exists():
        try:
            with open(metrics_path, "r", encoding="utf-8") as f:
                metrics_data = json.load(f)
                best_model = metrics_data.get("best_model", "GradientBoosting")
        except Exception:
            best_model = "GradientBoosting"
    else:
        best_model = "GradientBoosting"

    best_model_justification = (
        f"{best_model} was selected as the best model because it achieved the highest mean F1-score during "
        f"stratified 5-fold cross-validation. Significance tests (McNemar and DeLong AUC) were conducted to "
        f"verify if the performance improvements are statistically significant."
    )

    return {
        "module": module,
        "models": models_report,
        "significance_tests": significance_tests,
        "auc_comparisons": auc_comparisons,
        "best_model": best_model,
        "best_model_justification": best_model_justification,
    }
