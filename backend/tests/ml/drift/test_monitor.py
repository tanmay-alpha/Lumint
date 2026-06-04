import pytest
import datetime
from ml.drift.monitor import LumintDriftMonitor, DriftStatus, DriftSignal

def test_drift_signal_has_all_fields():
    monitor = LumintDriftMonitor(module="test")
    signal = monitor.update(y_true=0, y_pred=0)
    
    assert isinstance(signal, DriftSignal)
    assert signal.status in [DriftStatus.STABLE, DriftStatus.WARNING, DriftStatus.DRIFT]
    assert isinstance(signal.detector_votes, dict)
    assert "adwin" in signal.detector_votes
    assert "ph" in signal.detector_votes
    assert "ddm" in signal.detector_votes
    assert signal.drift_detected_at is None or isinstance(signal.drift_detected_at, int)
    assert isinstance(signal.error_rate_current, float)
    assert isinstance(signal.error_rate_baseline, float)
    assert isinstance(signal.delta, float)
    assert isinstance(signal.recommended_action, str)
    assert isinstance(signal.timestamp, str)
    assert signal.timestamp.endswith("Z")

def test_error_rate_is_float_in_0_1():
    monitor = LumintDriftMonitor(module="test", window_size=10)
    for _ in range(5):
        monitor.update(y_true=1, y_pred=0) # errors
    for _ in range(5):
        monitor.update(y_true=0, y_pred=0) # no errors
        
    error_rate = monitor.get_error_rate()
    assert isinstance(error_rate, float)
    assert 0.0 <= error_rate <= 1.0
    assert abs(error_rate - 0.5) < 1e-9

def test_stable_stream_no_false_alarms():
    monitor = LumintDriftMonitor(module="test", random_state=42)
    # Feed 300 clean samples (low error probability)
    for _ in range(300):
        # 5% error rate
        import random
        random.seed(42)
        error = 1 if random.random() < 0.05 else 0
        signal = monitor.update(y_true=error, y_pred=0)
        assert signal.status != DriftStatus.DRIFT

def test_abrupt_drift_detected_within_100_samples():
    monitor = LumintDriftMonitor(module="test", random_state=42)
    
    # 200 stable samples
    for _ in range(200):
        monitor.update(y_true=0, y_pred=0)
        
    # Suddenly introduce high errors
    detected = False
    for step in range(100):
        signal = monitor.update(y_true=1, y_pred=0)
        if signal.status == DriftStatus.DRIFT:
            detected = True
            break
            
    assert detected, "Drift was not detected within 100 samples after injection"

def test_majority_vote_requires_2_of_3():
    monitor = LumintDriftMonitor(module="test")
    
    # Manually trigger detectors to test majority vote counting
    # Rather than mocking, we verify using the status logic with active/instant votes.
    # If only 1 detector detects drift, the ensemble should not report DRIFT (should be WARNING).
    # If 2 detectors detect drift, the ensemble should report DRIFT.
    
    # Let's verify by setting the last detection steps directly
    monitor.n_samples = 300
    
    # Case A: Only ADWIN active
    monitor.last_adwin_drift = 300
    monitor.last_ph_drift = None
    monitor.last_ddm_drift = None
    signal = monitor.get_current_signal()
    assert signal.status == DriftStatus.WARNING
    
    # Case B: ADWIN and DDM active
    monitor.last_ddm_drift = 250
    signal = monitor.get_current_signal()
    assert signal.status == DriftStatus.DRIFT

def test_reset_clears_state():
    monitor = LumintDriftMonitor(module="test")
    # Feed some errors
    for _ in range(50):
        monitor.update(y_true=1, y_pred=0)
        
    assert monitor.n_samples == 50
    assert len(monitor.errors) > 0
    
    monitor.reset()
    assert monitor.n_samples == 0
    assert len(monitor.errors) == 0
    assert monitor.last_drift_at is None
    assert len(monitor.get_drift_history()) == 0

def test_serialize_state_is_json_serializable():
    import json
    monitor = LumintDriftMonitor(module="test")
    monitor.update(y_true=1, y_pred=0)
    state = monitor.serialize_state()
    
    # Assert it is JSON serializable without crashing
    serialized = json.dumps(state)
    assert isinstance(serialized, str)
    assert "test" in serialized
