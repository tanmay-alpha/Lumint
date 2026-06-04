"""
Lumint Concept Drift Detection Engine
Monitors prediction error streams for distribution shift.
Three detectors run in parallel — majority vote for drift signal.
"""

import datetime
import numpy as np
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Optional, List, Dict, Any
from river import drift as river_drift

class DriftStatus(str, Enum):
    STABLE    = "stable"
    WARNING   = "warning"
    DRIFT     = "drift"

@dataclass
class DriftSignal:
    status: DriftStatus
    detector_votes: dict      # {adwin: bool, ph: bool, ddm: bool}
    drift_detected_at: Optional[int]  # sample index
    error_rate_current: float
    error_rate_baseline: float
    delta: float              # change magnitude
    recommended_action: str  # "monitor" | "retrain" | "alert"
    timestamp: str

    def to_dict(self) -> dict:
        return asdict(self)

class LumintDriftMonitor:
    """
    Runs 3 drift detectors in parallel on prediction error stream.
    Majority vote: 2/3 detectors agree = drift confirmed.
    
    Usage:
        monitor = LumintDriftMonitor(module="phish")
        signal = monitor.update(y_true=1, y_pred=0)
        if signal.status == DriftStatus.DRIFT:
            trigger_retraining()
    """
    
    def __init__(
        self,
        module: str,
        adwin_delta: float = 0.002,
        ph_delta: float = 0.005,
        ph_lambda: float = 50,
        window_size: int = 500,
        random_state: int = 42
    ):
        self.module = module
        self.adwin_delta = adwin_delta
        self.ph_delta = ph_delta
        self.ph_lambda = ph_lambda
        self.window_size = window_size
        self.random_state = random_state
        
        self.adwin = river_drift.ADWIN(delta=self.adwin_delta)
        self.page_hinkley = river_drift.PageHinkley(delta=self.ph_delta, threshold=self.ph_lambda)
        self.ddm = river_drift.binary.DDM()
        
        self.n_samples = 0
        self.errors = []
        self.baseline_errors = []
        self.last_drift_at = None
        self.drift_history = []
        
        # Track last detection sample for ensemble voting
        self.last_adwin_drift = None
        self.last_ph_drift = None
        self.last_ddm_drift = None

    def update(self, y_true: int, y_pred: int) -> DriftSignal:
        """
        Feed one prediction result.
        error = 1 if y_true != y_pred else 0
        Update all 3 detectors with error.
        Check drift status from each.
        Return DriftSignal with majority vote.
        """
        error = 1 if y_true != y_pred else 0
        self.n_samples += 1
        
        # Track errors in sliding window
        self.errors.append(error)
        if len(self.errors) > self.window_size:
            self.errors.pop(0)
            
        # Track errors for baseline calculation
        if self.n_samples <= self.window_size:
            self.baseline_errors.append(error)
            
        # Update detectors
        self.adwin.update(error)
        self.page_hinkley.update(error)
        self.ddm.update(error)
        
        # Collect drift votes
        adwin_vote = bool(self.adwin.drift_detected)
        ph_vote = bool(self.page_hinkley.drift_detected)
        ddm_vote = bool(self.ddm.drift_detected)
        
        if adwin_vote:
            self.last_adwin_drift = self.n_samples
        if ph_vote:
            self.last_ph_drift = self.n_samples
        if ddm_vote:
            self.last_ddm_drift = self.n_samples
            
        votes = {
            "adwin": adwin_vote,
            "ph": ph_vote,
            "ddm": ddm_vote
        }
        
        # Active status checks (agreement within a 200-sample window)
        adwin_active = adwin_vote or (self.last_adwin_drift is not None and self.n_samples - self.last_adwin_drift <= 200)
        ph_active = ph_vote or (self.last_ph_drift is not None and self.n_samples - self.last_ph_drift <= 200)
        ddm_active = ddm_vote or (self.last_ddm_drift is not None and self.n_samples - self.last_ddm_drift <= 200)
        
        active_votes = {
            "adwin": adwin_active,
            "ph": ph_active,
            "ddm": ddm_active
        }
        
        vote_count_instant = sum(1 for v in votes.values() if v)
        vote_count_active = sum(1 for v in active_votes.values() if v)
        
        vote_count = max(vote_count_instant, vote_count_active)
        
        # Determine status
        if vote_count >= 2:
            status = DriftStatus.DRIFT
            recommended_action = "retrain"
            if self.last_drift_at is None:
                self.last_drift_at = self.n_samples
        elif vote_count == 1 or bool(self.ddm.warning_detected):
            status = DriftStatus.WARNING
            recommended_action = "alert"
        else:
            status = DriftStatus.STABLE
            recommended_action = "monitor"
            
        # Compute metrics
        error_rate_current = float(np.mean(self.errors)) if self.errors else 0.0
        error_rate_baseline = float(np.mean(self.baseline_errors)) if self.baseline_errors else 0.0
        delta = error_rate_current - error_rate_baseline
        
        timestamp = datetime.datetime.utcnow().isoformat() + "Z"
        
        signal = DriftSignal(
            status=status,
            detector_votes=votes,
            drift_detected_at=self.last_drift_at,
            error_rate_current=error_rate_current,
            error_rate_baseline=error_rate_baseline,
            delta=delta,
            recommended_action=recommended_action,
            timestamp=timestamp
        )
        
        # Record to history if warning or drift
        if status != DriftStatus.STABLE:
            self.drift_history.append({
                "sample_index": self.n_samples,
                "status": status.value,
                "votes": votes,
                "error_rate_current": error_rate_current,
                "delta": delta,
                "timestamp": timestamp
            })
            
        return signal

    def get_current_signal(self) -> DriftSignal:
        """Get the current status signal without feeding a new prediction."""
        adwin_vote = bool(self.adwin.drift_detected)
        ph_vote = bool(self.page_hinkley.drift_detected)
        ddm_vote = bool(self.ddm.drift_detected)
        
        votes = {
            "adwin": adwin_vote,
            "ph": ph_vote,
            "ddm": ddm_vote
        }
        
        adwin_active = adwin_vote or (self.last_adwin_drift is not None and self.n_samples - self.last_adwin_drift <= 200)
        ph_active = ph_vote or (self.last_ph_drift is not None and self.n_samples - self.last_ph_drift <= 200)
        ddm_active = ddm_vote or (self.last_ddm_drift is not None and self.n_samples - self.last_ddm_drift <= 200)
        
        active_votes = {
            "adwin": adwin_active,
            "ph": ph_active,
            "ddm": ddm_active
        }
        
        vote_count_instant = sum(1 for v in votes.values() if v)
        vote_count_active = sum(1 for v in active_votes.values() if v)
        
        vote_count = max(vote_count_instant, vote_count_active)
        
        if vote_count >= 2:
            status = DriftStatus.DRIFT
            recommended_action = "retrain"
        elif vote_count == 1 or bool(self.ddm.warning_detected):
            status = DriftStatus.WARNING
            recommended_action = "alert"
        else:
            status = DriftStatus.STABLE
            recommended_action = "monitor"
            
        error_rate_current = float(np.mean(self.errors)) if self.errors else 0.0
        error_rate_baseline = float(np.mean(self.baseline_errors)) if self.baseline_errors else 0.0
        delta = error_rate_current - error_rate_baseline
        
        timestamp = datetime.datetime.utcnow().isoformat() + "Z"
        
        return DriftSignal(
            status=status,
            detector_votes=votes,
            drift_detected_at=self.last_drift_at,
            error_rate_current=error_rate_current,
            error_rate_baseline=error_rate_baseline,
            delta=delta,
            recommended_action=recommended_action,
            timestamp=timestamp
        )

    def reset(self) -> None:
        """Reset all detectors after retraining."""
        self.adwin = river_drift.ADWIN(delta=self.adwin_delta)
        self.page_hinkley = river_drift.PageHinkley(delta=self.ph_delta, threshold=self.ph_lambda)
        self.ddm = river_drift.binary.DDM()
        self.n_samples = 0
        self.errors = []
        self.baseline_errors = []
        self.last_drift_at = None
        self.drift_history = []
        self.last_adwin_drift = None
        self.last_ph_drift = None
        self.last_ddm_drift = None

    def get_error_rate(self) -> float:
        """Rolling error rate over last window_size samples."""
        return float(np.mean(self.errors)) if self.errors else 0.0

    def get_drift_history(self) -> list[dict]:
        """Return list of all past drift events."""
        return self.drift_history

    def serialize_state(self) -> dict:
        """Serialize monitor state for storage/API."""
        return {
            "module": self.module,
            "n_samples": self.n_samples,
            "error_rate_current": self.get_error_rate(),
            "drift_history": self.get_drift_history(),
            "last_drift_at": self.last_drift_at,
            "parameters": {
                "adwin_delta": self.adwin_delta,
                "ph_delta": self.ph_delta,
                "ph_lambda": self.ph_lambda,
                "window_size": self.window_size
            }
        }
