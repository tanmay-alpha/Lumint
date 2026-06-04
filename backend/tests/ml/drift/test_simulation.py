import pytest
from ml.drift.simulate_drift import simulate_phishing_drift, simulate_gradual_drift

def test_simulation_detects_injected_drift():
    # Run phishing (abrupt) drift simulation
    res = simulate_phishing_drift(random_state=42)
    assert res["majority_vote_detection"] != -1
    assert res["majority_delay"] >= 0

def test_detection_delay_under_200_samples():
    res = simulate_phishing_drift(random_state=42)
    # The delay should be under 200 samples
    assert res["majority_delay"] < 200

def test_false_alarm_rate_below_0_05():
    res = simulate_phishing_drift(random_state=42)
    drift_point = res["true_drift_point"]
    
    # Calculate false alarm rate for each detector
    for detector, fa_count in res["false_alarms_before_drift"].items():
        fa_rate = fa_count / drift_point
        assert fa_rate < 0.05

def test_gradual_drift_detected_before_drift_end():
    res = simulate_gradual_drift(random_state=42)
    # Drift starts at 1000, ends at 2000
    # Majority vote detection should happen before step 2000
    assert res["majority_vote_detection"] != -1
    assert res["majority_vote_detection"] <= 2000
    assert res["majority_delay"] < 1000
