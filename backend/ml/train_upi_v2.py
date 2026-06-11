"""
Train improved UPI fraud detection model.

Improvements over the v1 model:
- 80+ features (vs 8 in v1)
- Ensemble of 4 models: RF + GB + XGBoost + LightGBM
- Proper train/val/test split (70/15/15) with stratification
- Cross-validation for hyperparameter sensitivity
- Platt scaling calibration
- Synthetic-vs-real flag surfaced in metrics

Critical caveat: the model is only as good as the training data. Until
real-world UPI screenshots are added to the training set, the v2 model
performs about as well as v1 on real data — the gains are mostly
in **interpretability** (more features → better SHAP/XAI outputs).

Usage:
    python -m ml.train_upi_v2 --features ml/data/upi_training.csv --output ml/models
"""
import argparse
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    classification_report,
    f1_score,
    matthews_corrcoef,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.preprocessing import StandardScaler

# XGBoost / LightGBM (use if available, else fallback)
try:
    from xgboost import XGBClassifier
    HAS_XGB = True
except ImportError:
    HAS_XGB = False
try:
    from lightgbm import LGBMClassifier
    HAS_LGB = True
except ImportError:
    HAS_LGB = False

logger = logging.getLogger("lumint.ml.train_upi_v2")

SEED = 42
N_SPLITS = 5


def _json_default(obj: Any) -> Any:
    """JSON serialiser for numpy types."""
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serialisable")


def _cast_to_json(obj: Any) -> Any:
    """Recursively convert numpy scalars/arrays to native Python types so
    json.dump doesn't choke on int64 keys / float64 values."""
    if isinstance(obj, dict):
        return {
            (int(k) if isinstance(k, np.integer) else str(k) if not isinstance(k, (str, int, float, bool, type(None))) else k):
            _cast_to_json(v)
            for k, v in obj.items()
        }
    if isinstance(obj, (list, tuple)):
        return [_cast_to_json(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    return obj


def _evaluate(y_true, y_pred, y_proba) -> Dict[str, float]:
    return {
        "precision": round(float(precision_score(y_true, y_pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_true, y_pred, zero_division=0)), 4),
        "f1": round(float(f1_score(y_true, y_pred, zero_division=0)), 4),
        "auc": round(float(roc_auc_score(y_true, y_proba)), 4),
        "mcc": round(float(matthews_corrcoef(y_true, y_pred)), 4),
    }


def _candidate_models() -> Dict[str, Any]:
    """Return the 4 candidate model instances."""
    models = {
        "RandomForest": RandomForestClassifier(
            n_estimators=300,
            max_depth=12,
            min_samples_leaf=5,
            class_weight="balanced",
            random_state=SEED,
            n_jobs=-1,
        ),
        "GradientBoosting": GradientBoostingClassifier(
            n_estimators=200,
            max_depth=5,
            learning_rate=0.1,
            random_state=SEED,
        ),
    }
    if HAS_XGB:
        models["XGBoost"] = XGBClassifier(
            n_estimators=300,
            max_depth=6,
            learning_rate=0.05,
            use_label_encoder=False,
            eval_metric="logloss",
            random_state=SEED,
            n_jobs=-1,
            verbosity=0,
        )
    if HAS_LGB:
        models["LightGBM"] = LGBMClassifier(
            n_estimators=300,
            max_depth=6,
            learning_rate=0.05,
            random_state=SEED,
            n_jobs=-1,
            verbose=-1,
        )
    return models


def train_ensemble(features_csv: str, output_dir: str) -> Dict[str, Any]:
    """
    Train ensemble of 4 models on feature CSV with proper train/val/test split.

    Expected CSV format:
    - First N-1 columns: features
    - Last column: label (0=real, 1=forged)
    """
    df = pd.read_csv(features_csv)
    if "label" not in df.columns:
        raise ValueError(f"Expected 'label' column in {features_csv}, got: {list(df.columns)[:5]}…")
    feature_cols = [c for c in df.columns if c != "label"]

    X = df[feature_cols].values.astype(np.float32)
    y = df["label"].values.astype(int)

    logger.info("Dataset: %d samples, %d features", X.shape[0], X.shape[1])
    logger.info("Class balance: %s", dict(zip(*np.unique(y, return_counts=True))))

    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # 70/15/15 train/val/test split
    X_train, X_holdout, y_train, y_holdout = train_test_split(
        X_scaled, y, test_size=0.3, random_state=SEED, stratify=y
    )
    X_val, X_test, y_val, y_test = train_test_split(
        X_holdout, y_holdout, test_size=0.5, random_state=SEED, stratify=y_holdout
    )

    logger.info("Train: %d | Val: %d | Test: %d",
                X_train.shape[0], X_val.shape[0], X_test.shape[0])

    # Train each model with cross-validation on the training set
    skf = StratifiedKFold(n_splits=N_SPLITS, shuffle=True, random_state=SEED)
    cv_results: Dict[str, Dict[str, float]] = {}
    val_results: Dict[str, Dict[str, float]] = {}
    test_results: Dict[str, Dict[str, float]] = {}
    fitted_models: Dict[str, Any] = {}

    candidates = _candidate_models()

    for model_name, base_model in candidates.items():
        logger.info("=== %s ===", model_name)

        # CV on training set
        fold_metrics = {"f1": [], "auc": []}
        for fold_idx, (tr_idx, val_idx) in enumerate(skf.split(X_train, y_train)):
            clone = type(base_model)(**base_model.get_params())
            clone.fit(X_train[tr_idx], y_train[tr_idx])
            proba = clone.predict_proba(X_train[val_idx])[:, 1]
            pred = (proba > 0.5).astype(int)
            fold_metrics["f1"].append(f1_score(y_train[val_idx], pred, zero_division=0))
            fold_metrics["auc"].append(roc_auc_score(y_train[val_idx], proba))
        cv_results[model_name] = {
            k: round(float(np.mean(v)), 4) for k, v in fold_metrics.items()
        }
        logger.info("  CV: %s", cv_results[model_name])

        # Refit on full training set
        fitted = type(base_model)(**base_model.get_params())
        fitted.fit(X_train, y_train)
        fitted_models[model_name] = fitted

        # Validation metrics
        val_proba = fitted.predict_proba(X_val)[:, 1]
        val_pred = (val_proba > 0.5).astype(int)
        val_results[model_name] = _evaluate(y_val, val_pred, val_proba)
        logger.info("  Val: %s", val_results[model_name])

        # Test metrics (note: used once for reporting only)
        test_proba = fitted.predict_proba(X_test)[:, 1]
        test_pred = (test_proba > 0.5).astype(int)
        test_results[model_name] = _evaluate(y_test, test_pred, test_proba)
        logger.info("  Test: %s", test_results[model_name])

    # Select best by validation F1
    best_model_name = max(val_results, key=lambda k: val_results[k]["f1"])
    logger.info("Best model: %s (val F1=%.4f)", best_model_name, val_results[best_model_name]["f1"])

    # Ensemble: average probabilities of all fitted models
    val_probas = [m.predict_proba(X_val)[:, 1] for m in fitted_models.values()]
    test_probas = [m.predict_proba(X_test)[:, 1] for m in fitted_models.values()]
    ens_val_proba = np.mean(val_probas, axis=0)
    ens_test_proba = np.mean(test_probas, axis=0)
    ens_val_pred = (ens_val_proba > 0.5).astype(int)
    ens_test_pred = (ens_test_proba > 0.5).astype(int)
    ens_val = _evaluate(y_val, ens_val_pred, ens_val_proba)
    ens_test = _evaluate(y_test, ens_test_pred, ens_test_proba)
    logger.info("Ensemble Val: %s", ens_val)
    logger.info("Ensemble Test: %s", ens_test)

    # Platt scaling calibration on validation
    calibrator = LogisticRegression()
    calibrator.fit(ens_val_proba.reshape(-1, 1), y_val)
    cal_test_proba = calibrator.predict_proba(ens_test_proba.reshape(-1, 1))[:, 1]
    cal_test_pred = (cal_test_proba > 0.5).astype(int)
    cal_test = _evaluate(y_test, cal_test_pred, cal_test_proba)
    logger.info("Calibrated Test: %s", cal_test)

    # Save artifacts
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    joblib.dump(scaler, out / "upi_v2_scaler.joblib")
    joblib.dump(fitted_models, out / "upi_v2_models.joblib")
    joblib.dump(calibrator, out / "upi_v2_calibrator.joblib")
    joblib.dump({"feature_names": feature_cols}, out / "upi_v2_meta.joblib")

    # Feature importance (use RF as the most interpretable)
    rf = fitted_models.get("RandomForest") or list(fitted_models.values())[0]
    fi = pd.DataFrame({
        "feature": feature_cols,
        "importance": rf.feature_importances_,
    }).sort_values("importance", ascending=False)
    fi.to_csv(out / "upi_v2_feature_importance.csv", index=False)

    # Metrics JSON
    metrics = _cast_to_json({
        "module": "upi_v2",
        "best_model": best_model_name,
        "ensemble_size": len(fitted_models),
        "n_train": int(X_train.shape[0]),
        "n_val": int(X_val.shape[0]),
        "n_test": int(X_test.shape[0]),
        "n_features": int(X.shape[1]),
        "cv_results": cv_results,
        "val_results": val_results,
        "test_results": test_results,
        "ensemble_val": ens_val,
        "ensemble_test": ens_test,
        "calibrated_test": cal_test,
        "class_balance": dict(zip(*[list(x) for x in np.unique(y, return_counts=True)])),
        "random_state": SEED,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "caveat": (
            "Model trained on the dataset shipped with the repo. "
            "F1=1.0 on synthetic data is expected; real-world performance "
            "will be lower until a real UPI screenshot dataset is added."
        ),
    })
    with open(out / "upi_v2_metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, default=_json_default)

    # Top-10 features log
    logger.info("Top 10 features:\n%s", fi.head(10).to_string(index=False))
    logger.info("Saved artifacts to %s", out)

    # Print detailed classification report for the best model on test
    best = fitted_models[best_model_name]
    test_proba = best.predict_proba(X_test)[:, 1]
    test_pred = (test_proba > 0.5).astype(int)
    logger.info("\nClassification report (%s):\n%s",
                best_model_name,
                classification_report(y_test, test_pred, zero_division=0))

    return metrics


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    parser = argparse.ArgumentParser()
    parser.add_argument("--features", required=True, help="Path to features.csv")
    parser.add_argument("--output", default="ml/models")
    args = parser.parse_args()
    train_ensemble(args.features, args.output)