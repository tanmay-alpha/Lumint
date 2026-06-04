import numpy as np
from ml.stats.mcnemar_test import mcnemar_test


def test_mcnemar_identical():
    y_true = np.array([0, 1, 0, 1, 0, 1])
    y_pred_a = np.array([0, 1, 0, 1, 0, 1])
    y_pred_b = np.array([0, 1, 0, 1, 0, 1])

    res = mcnemar_test(y_true, y_pred_a, y_pred_b)
    assert res["b"] == 0
    assert res["c"] == 0
    assert res["p_value"] == 1.0
    assert not res["significant"]


def test_mcnemar_exact():
    # b + c < 25
    y_true = np.array([1] * 10 + [0] * 10)
    # A has 2 errors, B has 0 errors
    y_pred_a = np.array([1] * 8 + [0] * 2 + [0] * 10)  # 8/10 correct for class 1
    y_pred_b = np.array([1] * 10 + [0] * 10)          # 10/10 correct

    res = mcnemar_test(y_true, y_pred_a, y_pred_b)
    # A correct B wrong: A got no prediction right where B was wrong (B was perfect)
    # B correct A wrong: B was correct on the 2 where A was wrong
    assert res["b"] == 0
    assert res["c"] == 2
    # Should use exact binomial mid-p
    assert res["p_value"] < 1.0


def test_mcnemar_chi2():
    # b + c >= 25
    y_true = np.array([1] * 50)
    # A is correct on first 40
    y_pred_a = np.array([1] * 40 + [0] * 10)
    # B is correct on last 40
    y_pred_b = np.array([0] * 10 + [1] * 40)

    # correct A & wrong B = A correct on 10 where B is incorrect (first 10) -> b = 10
    # correct B & wrong A = B correct on 10 where A is incorrect (last 10) -> c = 10
    # Wait, b+c = 20 < 25. Let's make it larger:
    # A is correct on first 70, B is correct on last 70
    y_true = np.array([1] * 100)
    y_pred_a = np.array([1] * 70 + [0] * 30)
    y_pred_b = np.array([0] * 30 + [1] * 70)
    # b: A correct first 30, B incorrect first 30 -> b = 40?
    # Let's count explicitly:
    # correct_a = [True]*70 + [False]*30
    # correct_b = [False]*30 + [True]*70
    # correct_a & ~correct_b = [True]*30 + [True]*40 & [True]*30 + [False]*70
    # Let's construct a cleaner example where b and c are large
    y_pred_a = np.array([1] * 80 + [0] * 20)  # correct on 80
    y_pred_b = np.array([0] * 40 + [1] * 60)  # correct on last 60
    # correct_a: 0-79 are correct
    # correct_b: 40-99 are correct
    # b (A correct, B wrong): 0-39 are correct for A and wrong for B (40 samples)
    # c (B correct, A wrong): 80-99 are correct for B and wrong for A (20 samples)
    # b + c = 60 >= 25
    res = mcnemar_test(y_true, y_pred_a, y_pred_b)
    assert res["b"] == 40
    assert res["c"] == 20
    assert res["p_value"] < 0.05
    assert res["significant"]
    assert "better" in res["interpretation"]
