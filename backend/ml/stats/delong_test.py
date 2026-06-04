"""
DeLong's method for calculating AUC confidence interval and comparing two AUCs.
"""

import numpy as np
import scipy.stats as stats


def delong_auc_ci(
    y_true: np.ndarray,
    y_proba: np.ndarray,
    alpha: float = 0.05,
) -> dict:
    """
    DeLong et al. (1988) method for AUC confidence interval.
    No bootstrap needed — analytical solution.
    """
    y_true = np.asarray(y_true)
    y_proba = np.asarray(y_proba)

    pos_idx = y_true == 1
    neg_idx = y_true == 0

    x = y_proba[pos_idx]
    y = y_proba[neg_idx]

    m = len(x)
    n = len(y)

    if m == 0 or n == 0:
        return {
            "auc": 0.5,
            "ci_lower": 0.5,
            "ci_upper": 0.5,
            "se": 0.0,
            "confidence": 1.0 - alpha,
        }

    # Vectorized placement values via broadcasting
    diff = x[:, None] - y[None, :]
    psi = (diff > 0).astype(float) + 0.5 * (diff == 0).astype(float)

    auc = float(np.mean(psi))

    V10 = np.mean(psi, axis=1)
    V01 = np.mean(psi, axis=0)

    s10 = np.sum((V10 - auc) ** 2) / (m - 1) if m > 1 else 0.0
    s01 = np.sum((V01 - auc) ** 2) / (n - 1) if n > 1 else 0.0

    var_auc = s10 / m + s01 / n
    se = np.sqrt(var_auc)

    z = stats.norm.ppf(1.0 - alpha / 2.0)
    ci_lower = max(0.0, auc - z * se)
    ci_upper = min(1.0, auc + z * se)

    return {
        "auc": round(auc, 4),
        "ci_lower": round(float(ci_lower), 4),
        "ci_upper": round(float(ci_upper), 4),
        "se": round(float(se), 4),
        "confidence": 1.0 - alpha,
    }


def delong_compare(
    y_true: np.ndarray,
    y_proba_a: np.ndarray,
    y_proba_b: np.ndarray,
) -> dict:
    """
    Test if AUC of model A significantly differs from model B.
    Returns p-value and z-statistic.
    """
    y_true = np.asarray(y_true)
    y_proba_a = np.asarray(y_proba_a)
    y_proba_b = np.asarray(y_proba_b)

    pos_idx = y_true == 1
    neg_idx = y_true == 0

    m = np.sum(pos_idx)
    n = np.sum(neg_idx)

    if m == 0 or n == 0:
        return {
            "z_statistic": 0.0,
            "p_value": 1.0,
            "auc_a": 0.5,
            "auc_b": 0.5,
        }

    x_a = y_proba_a[pos_idx]
    y_a = y_proba_a[neg_idx]
    x_b = y_proba_b[pos_idx]
    y_b = y_proba_b[neg_idx]

    # Model A placement values
    diff_a = x_a[:, None] - y_a[None, :]
    psi_a = (diff_a > 0).astype(float) + 0.5 * (diff_a == 0).astype(float)
    auc_a = np.mean(psi_a)
    V10_a = np.mean(psi_a, axis=1)
    V01_a = np.mean(psi_a, axis=0)

    # Model B placement values
    diff_b = x_b[:, None] - y_b[None, :]
    psi_b = (diff_b > 0).astype(float) + 0.5 * (diff_b == 0).astype(float)
    auc_b = np.mean(psi_b)
    V10_b = np.mean(psi_b, axis=1)
    V01_b = np.mean(psi_b, axis=0)

    # Variances and Covariances
    s10_a = np.sum((V10_a - auc_a) ** 2) / (m - 1) if m > 1 else 0.0
    s10_b = np.sum((V10_b - auc_b) ** 2) / (m - 1) if m > 1 else 0.0
    s10_ab = np.sum((V10_a - auc_a) * (V10_b - auc_b)) / (m - 1) if m > 1 else 0.0

    s01_a = np.sum((V01_a - auc_a) ** 2) / (n - 1) if n > 1 else 0.0
    s01_b = np.sum((V01_b - auc_b) ** 2) / (n - 1) if n > 1 else 0.0
    s01_ab = np.sum((V01_a - auc_a) * (V01_b - auc_b)) / (n - 1) if n > 1 else 0.0

    var_a = s10_a / m + s01_a / n
    var_b = s10_b / m + s01_b / n
    cov_ab = s10_ab / m + s01_ab / n

    var_diff = var_a + var_b - 2.0 * cov_ab

    if var_diff <= 0.0:
        z_stat = 0.0
        p_value = 1.0
    else:
        z_stat = (auc_a - auc_b) / np.sqrt(var_diff)
        p_value = 2.0 * stats.norm.sf(abs(z_stat))

    return {
        "z_statistic": round(float(z_stat), 4),
        "p_value": round(float(p_value), 4),
        "auc_a": round(float(auc_a), 4),
        "auc_b": round(float(auc_b), 4),
    }
