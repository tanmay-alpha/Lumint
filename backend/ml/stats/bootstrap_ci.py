"""
Stratified Bootstrap Confidence Interval Engine.
"""

import numpy as np
from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    matthews_corrcoef,
)


def bootstrap_ci(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_proba: np.ndarray,
    metric: str,
    n_replicates: int = 2000,
    confidence: float = 0.95,
    random_state: int = 42,
) -> dict:
    """
    Stratified bootstrap confidence interval.
    Preserves class prevalence in each resample.
    Returns:
    {
      "metric": "f1",
      "point_estimate": 0.xx,
      "ci_lower": 0.xx,
      "ci_upper": 0.xx,
      "confidence": 0.95,
      "n_replicates": 2000,
      "method": "stratified_bootstrap_percentile"
    }
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    y_proba = np.asarray(y_proba)

    metric = metric.lower()

    def calc_metric(yt: np.ndarray, yp: np.ndarray, ypr: np.ndarray) -> float:
        if metric == "f1":
            return float(f1_score(yt, yp, zero_division=0))
        elif metric == "precision":
            return float(precision_score(yt, yp, zero_division=0))
        elif metric == "recall":
            return float(recall_score(yt, yp, zero_division=0))
        elif metric == "auc":
            if len(np.unique(yt)) < 2:
                return 0.5
            return float(roc_auc_score(yt, ypr))
        elif metric == "mcc":
            return float(matthews_corrcoef(yt, yp))
        else:
            raise ValueError(f"Unknown metric: {metric}")

    point_estimate = calc_metric(y_true, y_pred, y_proba)

    # Stratify by class labels
    pos_idx = np.where(y_true == 1)[0]
    neg_idx = np.where(y_true == 0)[0]

    n_pos = len(pos_idx)
    n_neg = len(neg_idx)

    # Use NumPy Generator for deterministic random state
    rng = np.random.default_rng(seed=random_state)
    replicates = []

    for _ in range(n_replicates):
        if n_pos > 0:
            resampled_pos = rng.choice(pos_idx, size=n_pos, replace=True)
        else:
            resampled_pos = np.array([], dtype=int)

        if n_neg > 0:
            resampled_neg = rng.choice(neg_idx, size=n_neg, replace=True)
        else:
            resampled_neg = np.array([], dtype=int)

        resampled_idx = np.concatenate([resampled_pos, resampled_neg])

        yt_res = y_true[resampled_idx]
        yp_res = y_pred[resampled_idx]
        ypr_res = y_proba[resampled_idx]

        val = calc_metric(yt_res, yp_res, ypr_res)
        replicates.append(val)

    replicates = np.sort(replicates)

    # Percentile method
    alpha = 1.0 - confidence
    lower_pct = alpha / 2.0
    upper_pct = 1.0 - lower_pct

    lower_idx = int(np.floor(lower_pct * n_replicates))
    upper_idx = int(np.floor(upper_pct * n_replicates))

    lower_idx = max(0, min(lower_idx, n_replicates - 1))
    upper_idx = max(0, min(upper_idx, n_replicates - 1))

    ci_lower = replicates[lower_idx]
    ci_upper = replicates[upper_idx]

    return {
        "metric": metric,
        "point_estimate": round(float(point_estimate), 4),
        "ci_lower": round(float(ci_lower), 4),
        "ci_upper": round(float(ci_upper), 4),
        "confidence": confidence,
        "n_replicates": n_replicates,
        "method": "stratified_bootstrap_percentile",
    }


def compute_all_cis(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_proba: np.ndarray,
    n_replicates: int = 2000,
    confidence: float = 0.95,
    random_state: int = 42,
) -> dict:
    """Run bootstrap_ci for all 5 metrics at once."""
    metrics = ["f1", "precision", "recall", "auc", "mcc"]
    return {
        m: bootstrap_ci(
            y_true,
            y_pred,
            y_proba,
            metric=m,
            n_replicates=n_replicates,
            confidence=confidence,
            random_state=random_state,
        )
        for m in metrics
    }
