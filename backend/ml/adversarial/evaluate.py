"""
Lumint Adversarial Robustness Evaluator
Computes Attack Success Rate (ASR) and evaluates models under evasion attacks.
"""

import os
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.metrics import f1_score

from ml.registry import get_registry
from ml.adversarial.attacks import TabularFGSM, HopSkipJumpAttack

# Paths
BACKEND_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = BACKEND_ROOT / "data"

def compute_attack_success_rate(
    model,
    X_original: np.ndarray,
    X_adversarial: np.ndarray,
    y_true: np.ndarray
) -> float:
    """
    ASR = count(pred flipped from fraud to legit) /
          count(originally correctly classified fraud)
    Lower ASR = more robust model.
    """
    y_pred_orig = model.predict(X_original)
    y_pred_adv = model.predict(X_adversarial)
    
    # Originally correctly classified fraud (true == 1 and pred == 1)
    orig_fraud_mask = (y_true == 1) & (y_pred_orig == 1)
    orig_fraud_count = np.sum(orig_fraud_mask)
    
    if orig_fraud_count == 0:
        return 0.0
        
    # Flipped to legit (pred == 0)
    flipped_mask = orig_fraud_mask & (y_pred_adv == 0)
    flipped_count = np.sum(flipped_mask)
    
    return float(flipped_count / orig_fraud_count)

def compute_robustness_score(
    model,
    X_test: np.ndarray,
    y_test: np.ndarray,
    epsilons: list = [0.01, 0.05, 0.10, 0.20]
) -> dict:
    """
    Run FGSM at multiple epsilon values.
    Returns robustness curve: {epsilon: ASR}
    Perfect robustness: all ASR = 0.
    Zero robustness: all ASR = 1.
    Lumint goal: ASR < 0.15 at epsilon=0.10
    """
    curve = {}
    for eps in epsilons:
        attacker = TabularFGSM(epsilon=eps)
        X_adv = attacker.generate(X_test, y_test, model, n_samples=len(X_test))
        asr = compute_attack_success_rate(model, X_test[:len(X_adv)], X_adv, y_test[:len(X_adv)])
        curve[eps] = asr
    return curve

def load_module_data(module: str):
    """Load evaluation data for a specific module."""
    registry = get_registry()
    if module == "phish":
        from ml.features.url_features import extract_lexical_features, get_tfidf_features
        csv_path = DATA_DIR / "phishing_dataset.csv"
        df = pd.read_csv(csv_path)
        urls = df["url"].tolist()
        y = df["label"].values
        tfidf_vec = registry.get_tfidf("phish")
        
        X_list = []
        for url in urls:
            lexical = extract_lexical_features(url)
            tfidf = get_tfidf_features(url, tfidf_vec)
            X_list.append(np.concatenate([lexical, tfidf]))
        X = np.array(X_list, dtype=np.float64)
        return X, y
    elif module == "doc":
        csv_path = DATA_DIR / "doc_dataset.csv"
        df = pd.read_csv(csv_path)
        feature_cols = [c for c in df.columns if c != "label"]
        X = df[feature_cols].values.astype(np.float64)
        y = df["label"].values
        return X, y
    elif module == "upi":
        csv_path = DATA_DIR / "upi_dataset.csv"
        df = pd.read_csv(csv_path)
        feature_cols = [c for c in df.columns if c != "label"]
        X = df[feature_cols].values.astype(np.float64)
        y = df["label"].values
        return X, y
    else:
        raise ValueError(f"Unknown module: {module}")

def evaluate_module_robustness(
    module: str,
    model_override=None,
    n_samples_fgsm: int = 500,
    n_samples_hsj: int = 100
) -> dict:
    """
    Full robustness evaluation for one module.
    """
    X, y = load_module_data(module)
    
    # Determine model pipeline
    if model_override is not None:
        pipeline = model_override
    else:
        registry = get_registry()
        if not registry.is_available(module):
            raise ValueError(f"Model not trained/available for module: {module}")
        scaler = registry._scalers[module]
        model = registry._models[module]
        pipeline = Pipeline([
            ("scaler", scaler),
            ("model", model)
        ])
        
    # Baseline F1 score on the same sample size
    n_fgsm = min(len(X), n_samples_fgsm)
    y_pred_baseline = pipeline.predict(X[:n_fgsm])
    baseline_f1 = float(f1_score(y[:n_fgsm], y_pred_baseline, zero_division=0))
    
    # FGSM evaluation
    epsilons = [0.01, 0.05, 0.10, 0.20]
    fgsm_results = {}
    
    for eps in epsilons:
        attacker = TabularFGSM(epsilon=eps)
        X_adv = attacker.generate(X, y, pipeline, n_samples=n_fgsm)
        
        asr = compute_attack_success_rate(pipeline, X[:len(X_adv)], X_adv, y[:len(X_adv)])
        y_pred_adv = pipeline.predict(X_adv)
        f1_adv = float(f1_score(y[:len(X_adv)], y_pred_adv, zero_division=0))
        
        eps_key = f"epsilon_{eps:.2f}"
        fgsm_results[eps_key] = {
            "asr": asr,
            "f1_under_attack": f1_adv
        }
        
    # HopSkipJump evaluation
    n_hsj = min(len(X), n_samples_hsj)
    # HSJ is slow, set max_iter to 10 for reasonable execution time
    hsj_attacker = HopSkipJumpAttack(max_iter=10)
    X_adv_hsj = hsj_attacker.generate(X, pipeline, n_samples=n_hsj)
    
    hsj_asr = compute_attack_success_rate(pipeline, X[:len(X_adv_hsj)], X_adv_hsj, y[:len(X_adv_hsj)])
    
    # Compute robustness score: 1 - mean(ASR) across epsilons
    mean_asr = np.mean([fgsm_results[f"epsilon_{eps:.2f}"]["asr"] for eps in epsilons])
    robustness_score = float(1.0 - mean_asr)
    
    # Verdict
    if robustness_score >= 0.80:
        verdict = "ROBUST"
    elif robustness_score >= 0.55:
        verdict = "MODERATE"
    else:
        verdict = "VULNERABLE"
        
    return {
        "module": module,
        "baseline_f1": baseline_f1,
        "fgsm_results": fgsm_results,
        "hopskipjump_asr": hsj_asr,
        "robustness_score": robustness_score,
        "verdict": verdict
    }
