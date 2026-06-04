"""
Lumint Adversarial Training Defense
Augments the training dataset with FGSM adversarial examples and retrains the model.
Saves the hardened model as a Pipeline.
"""

import os
import json
from pathlib import Path
import joblib
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.calibration import CalibratedClassifierCV
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import f1_score

from ml.registry import get_registry
from ml.adversarial.attacks import TabularFGSM
from ml.adversarial.evaluate import load_module_data, compute_attack_success_rate

# Paths
BACKEND_ROOT = Path(__file__).resolve().parents[2]
MODELS_DIR = BACKEND_ROOT / "ml" / "models"

def _apply_smote(X: np.ndarray, y: np.ndarray, random_state: int = 42) -> tuple:
    try:
        from imblearn.over_sampling import SMOTE
        smote = SMOTE(random_state=random_state)
        X_res, y_res = smote.fit_resample(X, y)
        return X_res, y_res
    except Exception:
        return X, y

def get_base_classifier(model_name: str, random_state: int = 42):
    """Instantiate a base model classifier matching the original selection."""
    if model_name == "LogisticRegression":
        return LogisticRegression(
            max_iter=1000, random_state=random_state, solver="lbfgs", C=1.0
        )
    elif model_name == "RandomForest":
        return RandomForestClassifier(
            n_estimators=200, max_depth=15, random_state=random_state, n_jobs=-1
        )
    elif model_name == "GradientBoosting":
        return GradientBoostingClassifier(
            n_estimators=200, max_depth=5, learning_rate=0.1, random_state=random_state
        )
    else:
        # Default to RandomForest if unrecognized
        return RandomForestClassifier(
            n_estimators=200, max_depth=15, random_state=random_state, n_jobs=-1
        )

def adversarial_training(
    module: str,
    epsilon: float = 0.05,
    augmentation_ratio: float = 0.3,
    random_state: int = 42,
    n_samples_eval: int = 500
) -> dict:
    """
    Augment training set with adversarial examples.
    Retrain model on augmented set.
    Evaluate: ASR before vs after adversarial training.
    """
    # 1. Load original data
    X, y = load_module_data(module)
    
    # 2. Get original registry model and scaler
    registry = get_registry()
    if not registry.is_available(module):
        raise ValueError(f"Original model not trained/available for module: {module}")
    
    scaler_orig = registry._scalers[module]
    model_orig = registry._models[module]
    pipeline_orig = Pipeline([
        ("scaler", scaler_orig),
        ("model", model_orig)
    ])
    
    # 3. Read best model type from metrics
    best_model_name = "RandomForest"
    metrics_path = MODELS_DIR / f"{module}_metrics.json"
    if metrics_path.exists():
        try:
            with open(metrics_path, "r", encoding="utf-8") as f:
                metrics_json = json.load(f)
                best_model_name = metrics_json.get("best_model", "RandomForest")
        except Exception:
            pass
            
    # 4. Generate adversarial examples for augmentation
    rng = np.random.RandomState(random_state)
    n_aug = int(len(X) * augmentation_ratio)
    n_aug = max(1, min(n_aug, len(X)))
    
    # Select subset of indices to perturb
    aug_indices = rng.choice(len(X), size=n_aug, replace=False)
    X_to_perturb = X[aug_indices]
    y_to_perturb = y[aug_indices]
    
    # Find binary feature indices
    binary_indices = []
    for col in range(X.shape[1]):
        unique_vals = np.unique(X[:, col])
        if len(unique_vals) <= 2 and all(v in [0.0, 1.0] for v in unique_vals):
            binary_indices.append(col)
            
    attacker = TabularFGSM(epsilon=epsilon, binary_feature_indices=binary_indices)
    X_adv = attacker.generate(X_to_perturb, y_to_perturb, pipeline_orig, n_samples=n_aug)
    
    # 5. Build augmented training set
    X_augmented = np.concatenate([X, X_adv])
    y_augmented = np.concatenate([y, y_to_perturb])
    
    # 6. Train hardened model pipeline
    scaler_hardened = StandardScaler()
    X_aug_scaled = scaler_hardened.fit_transform(X_augmented)
    
    # Balance with SMOTE
    X_aug_res, y_aug_res = _apply_smote(X_aug_scaled, y_augmented, random_state=random_state)
    
    clf = get_base_classifier(best_model_name, random_state=random_state)
    clf.fit(X_aug_res, y_aug_res)
    
    # Calibrate model
    calibrator = CalibratedClassifierCV(estimator=clf, method="isotonic", cv="prefit")
    calibrator.fit(X_aug_scaled, y_augmented)
    
    pipeline_hardened = Pipeline([
        ("scaler", scaler_hardened),
        ("model", calibrator)
    ])
    
    # 7. Save hardened pipeline
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    hardened_path = MODELS_DIR / f"{module}_hardened_model.joblib"
    joblib.dump(pipeline_hardened, hardened_path)
    
    # 8. Evaluate original vs hardened
    n_eval = min(len(X), n_samples_eval)
    
    # Original performance
    y_pred_orig = pipeline_orig.predict(X[:n_eval])
    f1_orig = float(f1_score(y[:n_eval], y_pred_orig, zero_division=0))
    
    # Original ASR under attack
    X_adv_orig_eval = attacker.generate(X[:n_eval], y[:n_eval], pipeline_orig, n_samples=n_eval)
    asr_orig = compute_attack_success_rate(pipeline_orig, X[:len(X_adv_orig_eval)], X_adv_orig_eval, y[:len(X_adv_orig_eval)])
    
    # Hardened performance
    y_pred_hard = pipeline_hardened.predict(X[:n_eval])
    f1_hard = float(f1_score(y[:n_eval], y_pred_hard, zero_division=0))
    
    # Hardened ASR under attack
    X_adv_hard_eval = attacker.generate(X[:n_eval], y[:n_eval], pipeline_hardened, n_samples=n_eval)
    asr_hard = compute_attack_success_rate(pipeline_hardened, X[:len(X_adv_hard_eval)], X_adv_hard_eval, y[:len(X_adv_hard_eval)])
    
    # Metrics
    f1_cost = float(f1_orig - f1_hard)
    if asr_orig > 0:
        asr_reduction_pct = float((asr_orig - asr_hard) / asr_orig * 100.0)
    else:
        asr_reduction_pct = 0.0
        
    return {
        "module": module,
        "original_asr_epsilon_0.05": asr_orig,
        "hardened_asr_epsilon_0.05": asr_hard,
        "asr_reduction_pct": asr_reduction_pct,
        "f1_original": f1_orig,
        "f1_hardened": f1_hard,
        "f1_cost": f1_cost
    }
