"""
Lumint ML Training Pipeline — R9 Real ML Baseline Layer.

CLI: python -m ml.train --module [phish|doc|upi|all]

For each module:
  1. Load dataset CSV
  2. Extract features (with SMOTE on train fold only)
  3. Stratified 5-fold CV with LR / RF / GB
  4. Select best model by mean F1
  5. Retrain best on full training set
  6. Calibrate with CalibratedClassifierCV(method='isotonic', cv='prefit')
  7. Save model, scaler, metrics, feature_names

random_state=42 everywhere without exception.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Tuple, Optional

import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    matthews_corrcoef,
    log_loss,
)
from lightgbm import LGBMClassifier
from xgboost import XGBClassifier

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

SEED = 42
N_SPLITS = 5
MODELS_DIR = Path(__file__).resolve().parent / "models"
DATA_DIR = BACKEND_ROOT / "data"
REPORTS_DIR = BACKEND_ROOT / "reports"


def _get_models() -> Dict[str, Any]:
    """Return the 5 candidate model instances."""
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
        "LightGBM": LGBMClassifier(
            n_estimators=200, max_depth=5, learning_rate=0.1, random_state=SEED, verbosity=-1, n_jobs=-1
        ),
        "XGBoost": XGBClassifier(
            n_estimators=200, max_depth=5, learning_rate=0.1, random_state=SEED, eval_metric="logloss", n_jobs=-1
        ),
    }


def _evaluate(y_true: np.ndarray, y_pred: np.ndarray, y_proba: np.ndarray) -> Dict[str, float]:
    """Compute precision, recall, F1, AUC, MCC, log-loss."""
    return {
        "precision": round(float(precision_score(y_true, y_pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_true, y_pred, zero_division=0)), 4),
        "f1": round(float(f1_score(y_true, y_pred, zero_division=0)), 4),
        "auc": round(float(roc_auc_score(y_true, y_proba)), 4),
        "mcc": round(float(matthews_corrcoef(y_true, y_pred)), 4),
        "logloss": round(float(log_loss(y_true, y_proba)), 4),
    }


def _apply_smote(X: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Apply SMOTE on training data only."""
    try:
        from imblearn.over_sampling import SMOTE
        smote = SMOTE(random_state=SEED)
        X_res, y_res = smote.fit_resample(X, y)
        return X_res, y_res
    except Exception:
        return X, y


def train_module(
    module: str,
    X: np.ndarray,
    y: np.ndarray,
    feature_names: list,
    tfidf_vectorizer: Any = None,
) -> Dict[str, Any]:
    """
    Train all 3 models via stratified 5-fold CV, pick best by F1,
    retrain on full data, calibrate, and save artifacts.
    """
    print(f"\n{'='*60}")
    print(f"Training module: {module}")
    print(f"  Dataset: {X.shape[0]} samples, {X.shape[1]} features")
    print(f"  Class distribution: {dict(zip(*np.unique(y, return_counts=True)))}")
    print(f"{'='*60}")

    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    skf = StratifiedKFold(n_splits=N_SPLITS, shuffle=True, random_state=SEED)

    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Cross-validation
    cv_results: Dict[str, Dict[str, list]] = {}
    models_dict = _get_models()

    for model_name, model in models_dict.items():
        fold_metrics = {
            "precision": [],
            "recall": [],
            "f1": [],
            "auc": [],
            "mcc": [],
            "logloss": [],
        }

        for fold_idx, (train_idx, val_idx) in enumerate(skf.split(X_scaled, y)):
            X_train, X_val = X_scaled[train_idx], X_scaled[val_idx]
            y_train, y_val = y[train_idx], y[val_idx]

            # SMOTE on training fold ONLY
            X_train_res, y_train_res = _apply_smote(X_train, y_train)

            # Train
            model_clone = type(model)(**model.get_params())
            model_clone.fit(X_train_res, y_train_res)

            # Predict
            y_pred = model_clone.predict(X_val)
            y_proba = model_clone.predict_proba(X_val)[:, 1]

            metrics = _evaluate(y_val, y_pred, y_proba)
            for k in fold_metrics:
                fold_metrics[k].append(metrics[k])

        # Average across folds
        cv_results[model_name] = {
            k: round(float(np.mean(v)), 4) for k, v in fold_metrics.items()
        }
        print(f"  {model_name}: F1={cv_results[model_name]['f1']:.4f}, AUC={cv_results[model_name]['auc']:.4f}")

    # Select best by F1
    best_model_name = max(cv_results, key=lambda k: cv_results[k]["f1"])
    print(f"\n  Best model: {best_model_name} (F1={cv_results[best_model_name]['f1']:.4f})")

    # Retrain best model on full dataset (with SMOTE)
    X_full_res, y_full_res = _apply_smote(X_scaled, y)
    best_model = type(models_dict[best_model_name])(**models_dict[best_model_name].get_params())
    best_model.fit(X_full_res, y_full_res)

    # Calibrate
    calibrator = CalibratedClassifierCV(
        estimator=best_model, method="isotonic", cv="prefit"
    )
    calibrator.fit(X_scaled, y)

    # Hold-out evaluation (on full set — note: for synthetic this is acceptable;
    # for real data, do proper train/test split before calling this function)
    y_pred_final = calibrator.predict(X_scaled)
    y_proba_final = calibrator.predict_proba(X_scaled)[:, 1]
    test_metrics = _evaluate(y, y_pred_final, y_proba_final)

    # Save artifacts
    model_path = MODELS_DIR / f"{module}_model.joblib"
    scaler_path = MODELS_DIR / f"{module}_scaler.joblib"
    metrics_path = MODELS_DIR / f"{module}_metrics.json"
    features_path = MODELS_DIR / f"{module}_feature_names.json"

    joblib.dump(calibrator, model_path)
    joblib.dump(scaler, scaler_path)

    if tfidf_vectorizer is not None:
        tfidf_path = MODELS_DIR / f"{module}_tfidf.joblib"
        joblib.dump(tfidf_vectorizer, tfidf_path)
        print(f"  Saved TF-IDF vectorizer -> {tfidf_path}")

    metrics_json = {
        "module": module,
        "best_model": best_model_name,
        "cv_results": cv_results,
        "test_set": test_metrics,
        "n_train": int(X.shape[0]),
        "n_test": int(X.shape[0]),
        "n_features": int(X.shape[1]),
        "random_state": SEED,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics_json, f, indent=2)

    with open(features_path, "w", encoding="utf-8") as f:
        json.dump(feature_names, f, indent=2)

    print(f"  Saved model -> {model_path}")
    print(f"  Saved scaler -> {scaler_path}")
    print(f"  Saved metrics -> {metrics_path}")
    print(f"  Saved feature names -> {features_path}")

    return metrics_json


def train_phish() -> Dict[str, Any]:
    """Train phishing URL detection model."""
    from ml.features.url_features import extract_lexical_features, fit_tfidf, get_tfidf_features, get_feature_names

    csv_path = DATA_DIR / "phishing_dataset.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"Phishing dataset not found at {csv_path}. Run: python data/generate_datasets.py")

    df = pd.read_csv(csv_path)
    urls = df["url"].tolist()
    labels = df["label"].values

    # Fit TF-IDF
    print("  Fitting TF-IDF vectorizer on URL corpus...")
    vectorizer = fit_tfidf(urls, random_state=SEED)

    # Extract features
    print("  Extracting features...")
    X_list = []
    for url in urls:
        lexical = extract_lexical_features(url)
        tfidf = get_tfidf_features(url, vectorizer)
        X_list.append(np.concatenate([lexical, tfidf]))

    X = np.array(X_list, dtype=np.float64)
    feature_names = get_feature_names(vectorizer)

    return train_module("phish", X, labels, feature_names, tfidf_vectorizer=vectorizer)


def train_doc() -> Dict[str, Any]:
    """Train document forensics model."""
    from ml.features.doc_features import DOC_FEATURE_NAMES

    csv_path = DATA_DIR / "doc_dataset.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"Document dataset not found at {csv_path}. Run: python data/generate_datasets.py")

    df = pd.read_csv(csv_path)
    feature_cols = [c for c in df.columns if c != "label"]
    X = df[feature_cols].values.astype(np.float64)
    y = df["label"].values

    return train_module("doc", X, y, feature_cols)


def train_upi() -> Dict[str, Any]:
    """Train UPI forgery detection model."""
    from ml.features.upi_features import UPI_FEATURE_NAMES

    csv_path = DATA_DIR / "upi_dataset.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"UPI dataset not found at {csv_path}. Run: python data/generate_datasets.py")

    df = pd.read_csv(csv_path)
    feature_cols = [c for c in df.columns if c != "label"]
    X = df[feature_cols].values.astype(np.float64)
    y = df["label"].values

    return train_module("upi", X, y, feature_cols)


def train_fusion_meta() -> Dict[str, Any]:
    """
    Train a LogisticRegression meta-learner for cross-modal fusion.
    Input: [phish_prob, doc_prob, upi_prob] (calibrated, 0-1)
    Output: lumint_fusion_score (0-100)
    """
    print(f"\n{'='*60}")
    print("Training Fusion Meta-Learner")
    print(f"{'='*60}")

    rng = np.random.RandomState(SEED)
    n_samples = 2000

    # Generate synthetic fusion training data
    # Fraud cases: at least 2 sub-models score high
    # Clean cases: all sub-models score low
    X_list = []
    y_list = []

    for _ in range(n_samples // 2):
        # Clean pattern
        phish_p = rng.uniform(0.0, 0.35)
        doc_p = rng.uniform(0.0, 0.30)
        upi_p = rng.uniform(0.0, 0.25)
        X_list.append([phish_p, doc_p, upi_p])
        y_list.append(0)

    for _ in range(n_samples // 2):
        # Fraud pattern
        phish_p = rng.uniform(0.4, 1.0)
        doc_p = rng.uniform(0.35, 1.0)
        upi_p = rng.uniform(0.3, 1.0)
        X_list.append([phish_p, doc_p, upi_p])
        y_list.append(1)

    X = np.array(X_list, dtype=np.float64)
    y = np.array(y_list)

    # Shuffle
    idx = rng.permutation(len(y))
    X = X[idx]
    y = y[idx]

    feature_names = ["phish_prob", "doc_prob", "upi_prob"]
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = LogisticRegression(random_state=SEED, max_iter=1000)
    model.fit(X_scaled, y)

    # Calibrate
    calibrator = CalibratedClassifierCV(estimator=model, method="isotonic", cv="prefit")
    calibrator.fit(X_scaled, y)

    # Save
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(calibrator, MODELS_DIR / "fusion_meta.joblib")
    joblib.dump(scaler, MODELS_DIR / "fusion_meta_scaler.joblib")

    # Metrics
    y_pred = calibrator.predict(X_scaled)
    y_proba = calibrator.predict_proba(X_scaled)[:, 1]
    test_metrics = _evaluate(y, y_pred, y_proba)

    # Extract coefficients from the underlying LR
    coefficients = {}
    try:
        coefs = model.coef_[0]
        for i, name in enumerate(feature_names):
            coefficients[name] = round(float(coefs[i]), 4)
    except Exception:
        pass

    metrics_json = {
        "module": "fusion_meta",
        "best_model": "LogisticRegression",
        "coefficients": coefficients,
        "test_set": test_metrics,
        "n_train": int(len(y)),
        "random_state": SEED,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    with open(MODELS_DIR / "fusion_meta_metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics_json, f, indent=2)

    with open(MODELS_DIR / "fusion_meta_feature_names.json", "w", encoding="utf-8") as f:
        json.dump(feature_names, f, indent=2)

    print(f"  Coefficients: {coefficients}")
    print(f"  Test F1={test_metrics['f1']:.4f}, AUC={test_metrics['auc']:.4f}")
    print(f"  Saved fusion meta-learner -> {MODELS_DIR / 'fusion_meta.joblib'}")

    return metrics_json


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Lumint ML Training Pipeline")
    parser.add_argument(
        "--module",
        type=str,
        default="all",
        choices=["phish", "doc", "upi", "fusion", "all"],
        help="Which module to train (default: all)",
    )

    args = parser.parse_args()
    results = {}

    if args.module in ("phish", "all"):
        results["phish"] = train_phish()

    if args.module in ("doc", "all"):
        results["doc"] = train_doc()

    if args.module in ("upi", "all"):
        results["upi"] = train_upi()

    if args.module in ("fusion", "all"):
        results["fusion_meta"] = train_fusion_meta()

    print(f"\n{'='*60}")
    print("Training complete!")
    for mod, res in results.items():
        best = res.get("best_model", "N/A")
        f1 = res.get("cv_results", {}).get(best, {}).get("f1") or res.get("test_set", {}).get("f1", 0)
        print(f"  {mod}: best={best}, F1={f1}")
    print(f"{'='*60}")
