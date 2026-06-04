from typing import Dict
from app.models.models import UPIShieldEvent # just in case
from ml.drift.monitor import LumintDriftMonitor, DriftSignal

class DriftRegistry:
    """
    Singleton. Holds one LumintDriftMonitor per module.
    Modules: phish, doc, upi, fusion
    """
    _monitors: Dict[str, LumintDriftMonitor] = {}

    @classmethod
    def get(cls, module: str) -> LumintDriftMonitor:
        """Get or create monitor for module."""
        if module not in cls._monitors:
            cls._monitors[module] = LumintDriftMonitor(module=module)
        return cls._monitors[module]

    @classmethod
    def update_all(cls, module: str, y_true: int, y_pred: int) -> DriftSignal:
        """Feed result to correct module monitor."""
        monitor = cls.get(module)
        return monitor.update(y_true, y_pred)

    @classmethod
    def get_all_status(cls) -> Dict[str, DriftSignal]:
        """Return current status for all modules."""
        # Ensure default modules are initialized
        for module in ["phish", "doc", "upi", "fusion"]:
            cls.get(module)
        return {
            module: monitor.get_current_signal()
            for module, monitor in cls._monitors.items()
        }

    @classmethod
    def reset_module(cls, module: str) -> None:
        """Reset after retraining."""
        monitor = cls.get(module)
        monitor.reset()
