"""
Simulates concept drift in fraud data stream.
Used to verify drift detectors work correctly.
Paper experiment: inject known drift at t=1000,
verify each detector catches it.
"""

import numpy as np
from ml.drift.monitor import LumintDriftMonitor, DriftStatus

def simulate_phishing_drift(
    n_samples: int = 3000,
    drift_point: int = 1000,
    random_state: int = 42
) -> dict:
    """
    Phase 1 (t=0 to t=999): stable distribution
      URL features from legit+phish balanced set (low error rate)
    Phase 2 (t=1000+): drifted distribution
      New phishing pattern (different URL structure)
      Model accuracy drops suddenly (high error rate)
    """
    rng = np.random.RandomState(random_state)
    monitor = LumintDriftMonitor(module="phish", random_state=random_state)
    
    adwin_detection = -1
    ph_detection = -1
    ddm_detection = -1
    majority_vote_detection = -1
    
    false_alarms = {
        "adwin": 0,
        "ph": 0,
        "ddm": 0
    }
    
    for t in range(1, n_samples + 1):
        # Determine error probability based on phase
        if t < drift_point:
            p_error = 0.05
        else:
            p_error = 0.40
            
        error = 1 if rng.rand() < p_error else 0
        
        # Feed prediction: y_true=error, y_pred=0 (meaning error=1 if y_true != y_pred else 0)
        signal = monitor.update(y_true=error, y_pred=0)
        
        # Check individual votes
        votes = signal.detector_votes
        
        if t < drift_point:
            if votes["adwin"]:
                false_alarms["adwin"] += 1
            if votes["ph"]:
                false_alarms["ph"] += 1
            if votes["ddm"]:
                false_alarms["ddm"] += 1
        else:
            if votes["adwin"] and adwin_detection == -1:
                adwin_detection = t
            if votes["ph"] and ph_detection == -1:
                ph_detection = t
            if votes["ddm"] and ddm_detection == -1:
                ddm_detection = t
            if signal.status == DriftStatus.DRIFT and majority_vote_detection == -1:
                majority_vote_detection = t

    # Compute delays
    adwin_delay = adwin_detection - drift_point if adwin_detection != -1 else -1
    ph_delay = ph_detection - drift_point if ph_detection != -1 else -1
    ddm_delay = ddm_detection - drift_point if ddm_detection != -1 else -1
    majority_delay = majority_vote_detection - drift_point if majority_vote_detection != -1 else -1
    
    return {
        "true_drift_point": drift_point,
        "adwin_detection": adwin_detection,
        "ph_detection": ph_detection,
        "ddm_detection": ddm_detection,
        "adwin_delay": adwin_delay,
        "ph_delay": ph_delay,
        "ddm_delay": ddm_delay,
        "false_alarms_before_drift": false_alarms,
        "majority_vote_detection": majority_vote_detection,
        "majority_delay": majority_delay
    }

def simulate_gradual_drift(
    n_samples: int = 5000,
    drift_start: int = 1000,
    drift_end: int = 2000,
    random_state: int = 42
) -> dict:
    """
    Gradual drift: distribution shifts slowly between
    drift_start and drift_end.
    Tests detector sensitivity vs false alarm tradeoff.
    """
    rng = np.random.RandomState(random_state)
    monitor = LumintDriftMonitor(module="phish", random_state=random_state)
    
    adwin_detection = -1
    ph_detection = -1
    ddm_detection = -1
    majority_vote_detection = -1
    
    false_alarms = {
        "adwin": 0,
        "ph": 0,
        "ddm": 0
    }
    
    for t in range(1, n_samples + 1):
        if t < drift_start:
            p_error = 0.05
        elif t <= drift_end:
            # Linear interpolation from 0.05 to 0.40
            p_error = 0.05 + (0.40 - 0.05) * (t - drift_start) / (drift_end - drift_start)
        else:
            p_error = 0.40
            
        error = 1 if rng.rand() < p_error else 0
        
        signal = monitor.update(y_true=error, y_pred=0)
        votes = signal.detector_votes
        
        if t < drift_start:
            if votes["adwin"]:
                false_alarms["adwin"] += 1
            if votes["ph"]:
                false_alarms["ph"] += 1
            if votes["ddm"]:
                false_alarms["ddm"] += 1
        else:
            if votes["adwin"] and adwin_detection == -1:
                adwin_detection = t
            if votes["ph"] and ph_detection == -1:
                ph_detection = t
            if votes["ddm"] and ddm_detection == -1:
                ddm_detection = t
            if signal.status == DriftStatus.DRIFT and majority_vote_detection == -1:
                majority_vote_detection = t

    adwin_delay = adwin_detection - drift_start if adwin_detection != -1 else -1
    ph_delay = ph_detection - drift_start if ph_detection != -1 else -1
    ddm_delay = ddm_detection - drift_start if ddm_detection != -1 else -1
    majority_delay = majority_vote_detection - drift_start if majority_vote_detection != -1 else -1
    
    return {
        "true_drift_point": drift_start,
        "adwin_detection": adwin_detection,
        "ph_detection": ph_detection,
        "ddm_detection": ddm_detection,
        "adwin_delay": adwin_delay,
        "ph_delay": ph_delay,
        "ddm_delay": ddm_delay,
        "false_alarms_before_drift": false_alarms,
        "majority_vote_detection": majority_vote_detection,
        "majority_delay": majority_delay
    }

if __name__ == "__main__":
    print("Running abrupt drift simulation...")
    abrupt_res = simulate_phishing_drift()
    print("Abrupt Results:", abrupt_res)
    print("\nRunning gradual drift simulation...")
    gradual_res = simulate_gradual_drift()
    print("Gradual Results:", gradual_res)
