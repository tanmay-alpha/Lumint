import numpy as np
from ml.stats.bootstrap_ci import bootstrap_ci, compute_all_cis


def test_bootstrap_ci_perfect():
    y_true = np.array([0, 0, 0, 1, 1, 1])
    y_pred = np.array([0, 0, 0, 1, 1, 1])
    y_proba = np.array([0.1, 0.2, 0.15, 0.8, 0.9, 0.85])

    res = bootstrap_ci(y_true, y_pred, y_proba, metric="f1", n_replicates=50, random_state=42)
    assert res["point_estimate"] == 1.0
    assert res["ci_lower"] == 1.0
    assert res["ci_upper"] == 1.0


def test_bootstrap_ci_all_metrics():
    y_true = np.array([0, 0, 1, 1, 0, 1])
    y_pred = np.array([0, 1, 1, 0, 0, 1])
    y_proba = np.array([0.2, 0.7, 0.8, 0.4, 0.3, 0.9])

    res = compute_all_cis(y_true, y_pred, y_proba, n_replicates=50, random_state=42)
    assert "f1" in res
    assert "precision" in res
    assert "recall" in res
    assert "auc" in res
    assert "mcc" in res

    for m in res:
        assert -1.0 <= res[m]["point_estimate"] <= 1.0
        assert -1.0 <= res[m]["ci_lower"] <= res[m]["ci_upper"] <= 1.0
        if m != "mcc":
            assert 0.0 <= res[m]["point_estimate"] <= 1.0
            assert 0.0 <= res[m]["ci_lower"] <= res[m]["ci_upper"] <= 1.0

