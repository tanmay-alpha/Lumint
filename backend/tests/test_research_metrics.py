import pytest
from research.metrics import (
    safe_divide,
    to_bool,
    compute_binary_classification_metrics,
    compute_latency_metrics
)

def test_safe_divide():
    assert safe_divide(10, 2) == 5.0
    assert safe_divide(10, 0) == 0.0
    assert safe_divide(10, 0, default=1.0) == 1.0

def test_to_bool():
    assert to_bool(True) is True
    assert to_bool(False) is False
    assert to_bool(1) is True
    assert to_bool(0) is False
    assert to_bool("HIGH") is True
    assert to_bool("SUSPICIOUS") is True
    assert to_bool("CLEAN") is False
    assert to_bool("UNKNOWN") is False

def test_compute_binary_classification_metrics():
    # 2 TP, 1 FP, 1 FN, 2 TN
    y_true = ["HIGH", "CLEAN", "SUSPICIOUS", "HIGH", "CLEAN", "CLEAN"]
    y_pred = ["HIGH", "HIGH", "CLEAN", "SUSPICIOUS", "CLEAN", "CLEAN"]
    
    metrics = compute_binary_classification_metrics(y_true, y_pred)
    assert metrics["TP"] == 2
    assert metrics["FP"] == 1
    assert metrics["FN"] == 1
    assert metrics["TN"] == 2
    
    assert metrics["accuracy"] == pytest.approx(4/6)
    assert metrics["precision"] == pytest.approx(2/3)
    assert metrics["recall"] == pytest.approx(2/3)
    assert metrics["f1"] == pytest.approx(2/3)
    assert metrics["fpr"] == pytest.approx(1/3)
    assert metrics["fnr"] == pytest.approx(1/3)
    assert metrics["support"] == 6

def test_compute_binary_classification_metrics_empty_mismatch():
    with pytest.raises(ValueError):
        compute_binary_classification_metrics([True], [True, False])

def test_compute_latency_metrics():
    latencies = [10.0, 20.0, 30.0, 40.0, 50.0]
    metrics = compute_latency_metrics(latencies)
    
    assert metrics["mean"] == 30.0
    assert metrics["median"] == 30.0
    assert metrics["min"] == 10.0
    assert metrics["max"] == 50.0
    assert metrics["p95"] == pytest.approx(48.0)
    assert metrics["p99"] == pytest.approx(49.6)

def test_compute_latency_metrics_empty():
    metrics = compute_latency_metrics([])
    assert metrics["mean"] == 0.0
    assert metrics["median"] == 0.0
    assert metrics["p95"] == 0.0
    assert metrics["p99"] == 0.0
