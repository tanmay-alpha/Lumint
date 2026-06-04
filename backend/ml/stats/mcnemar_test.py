"""
McNemar's test for comparing predictions of two classifiers.
"""

import numpy as np
from scipy.stats import binom, chi2


def mcnemar_test(
    y_true: np.ndarray,
    y_pred_a: np.ndarray,
    y_pred_b: np.ndarray,
    alpha: float = 0.05,
) -> dict:
    """
    Tests if model A and model B are significantly different.
    Uses exact McNemar (mid-p correction when b+c < 25).
    """
    y_true = np.asarray(y_true)
    y_pred_a = np.asarray(y_pred_a)
    y_pred_b = np.asarray(y_pred_b)

    correct_a = y_pred_a == y_true
    correct_b = y_pred_b == y_true

    # Contingency matrix values
    # b: A correct, B wrong
    # c: B correct, A wrong
    b = int(np.sum(correct_a & ~correct_b))
    c = int(np.sum(~correct_a & correct_b))

    n = b + c

    if n == 0:
        p_value = 1.0
        statistic = 0.0
    elif n < 25:
        # Exact McNemar with mid-p correction
        k = min(b, c)
        # mid-p = 2 * (P(X < k) + 0.5 * P(X = k)) under binomial(n, 0.5)
        # CDF(k-1) calculates P(X <= k-1) which is P(X < k)
        if k == 0:
            p_value = 2.0 * (0.5 * binom.pmf(0, n, 0.5))
        else:
            p_value = 2.0 * (binom.cdf(k - 1, n, 0.5) + 0.5 * binom.pmf(k, n, 0.5))
        p_value = min(1.0, float(p_value))
        statistic = float(k)
    else:
        # Chi-squared approximation with continuity correction
        statistic = float((abs(b - c) - 1.0) ** 2) / float(b + c)
        p_value = float(chi2.sf(statistic, df=1))

    significant = p_value < alpha

    if significant:
        if b > c:
            interpretation = "Model A is significantly better than Model B"
        else:
            interpretation = "Model A is significantly worse than Model B"
    else:
        interpretation = "Model A is not significantly different from Model B"

    return {
        "statistic": round(statistic, 4),
        "p_value": round(p_value, 4),
        "significant": bool(significant),
        "alpha": alpha,
        "interpretation": interpretation,
        "b": b,
        "c": c,
    }
