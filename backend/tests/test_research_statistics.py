import pytest
from research.statistics import (
    safe_mean,
    safe_percentile,
    bootstrap_confidence_interval,
    bootstrap_metric_ci,
    paired_difference
)

def test_safe_mean():
    assert safe_mean([]) == 0.0
    assert safe_mean([1, 2, 3]) == 2.0

def test_safe_percentile():
    assert safe_percentile([], 0.95) == 0.0
    assert safe_percentile([1, 2, 3, 4, 5], 0.5) == 3.0

def test_bootstrap_confidence_interval():
    data = [10.0, 12.0, 11.0, 13.0, 9.0]
    lower, mean_val, upper = bootstrap_confidence_interval(data, n_resamples=50)
    assert lower <= mean_val <= upper
    assert 9.0 <= mean_val <= 13.0

def test_bootstrap_metric_ci():
    y_true = ["HIGH", "HIGH", "SAFE", "SAFE", "HIGH", "SAFE"]
    y_pred = ["HIGH", "SAFE", "SAFE", "SAFE", "HIGH", "HIGH"]
    
    lower, mean_val, upper = bootstrap_metric_ci(y_true, y_pred, "accuracy", n_resamples=50)
    assert 0.0 <= lower <= mean_val <= upper <= 1.0
    assert abs(mean_val - 4/6) < 0.2
    
    lower_f, mean_f, upper_f = bootstrap_metric_ci(y_true, y_pred, "f1", n_resamples=50)
    assert 0.0 <= lower_f <= mean_f <= upper_f <= 1.0

def test_paired_difference():
    scores_a = [0.8, 0.9, 0.7, 0.85]
    scores_b = [0.75, 0.85, 0.65, 0.8]
    diffs = paired_difference(scores_a, scores_b)
    # Check that they match element-wise difference
    assert len(diffs) == 4
    for d in diffs:
        assert abs(d - 0.05) < 1e-7
