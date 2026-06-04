import numpy as np
from ml.stats.delong_test import delong_auc_ci, delong_compare


def test_delong_auc_ci_perfect():
    y_true = np.array([0, 0, 0, 1, 1, 1])
    y_proba = np.array([0.1, 0.2, 0.15, 0.8, 0.9, 0.85])

    res = delong_auc_ci(y_true, y_proba)
    assert res["auc"] == 1.0
    assert res["ci_lower"] == 1.0
    assert res["ci_upper"] == 1.0


def test_delong_compare_identical():
    y_true = np.array([0, 0, 1, 1, 0, 1])
    y_proba = np.array([0.2, 0.3, 0.8, 0.7, 0.4, 0.9])

    res = delong_compare(y_true, y_proba, y_proba)
    assert res["auc_a"] == res["auc_b"]
    assert res["p_value"] == 1.0
    assert res["z_statistic"] == 0.0


def test_delong_compare_difference():
    # Make a larger dataset with non-perfect AUCs to have non-zero variance
    y_true = np.array([0]*10 + [1]*10)
    # y_proba_a is mostly correct
    y_proba_a = np.array([0.1, 0.2, 0.3, 0.4, 0.2, 0.1, 0.3, 0.2, 0.1, 0.4] + 
                         [0.6, 0.7, 0.8, 0.9, 0.7, 0.6, 0.8, 0.7, 0.6, 0.9])
    # y_proba_b is random-ish/worse
    y_proba_b = np.array([0.5, 0.6, 0.4, 0.5, 0.6, 0.4, 0.5, 0.6, 0.4, 0.5] +
                         [0.4, 0.5, 0.6, 0.4, 0.5, 0.6, 0.4, 0.5, 0.6, 0.4])

    res = delong_compare(y_true, y_proba_a, y_proba_b)
    assert res["auc_a"] > res["auc_b"]
    assert res["p_value"] < 0.05

