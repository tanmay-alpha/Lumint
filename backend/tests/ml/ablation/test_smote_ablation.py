"""
Tests for SMOTE ablation.
"""

from pathlib import Path
import json
import pytest
from ml.ablation.smote_ablation import run_smote_ablation

BACKEND_ROOT = Path(__file__).resolve().parents[3]


def test_run_smote_ablation():
    """Verify that SMOTE ablation runs correctly for phish, doc, and upi."""
    for module in ["phish", "doc", "upi"]:
        res = run_smote_ablation(module)
        assert isinstance(res, dict)
        for strategy in ["without_smote", "with_smote", "class_weight_balanced"]:
            assert strategy in res
            metrics = res[strategy]
            assert "precision" in metrics
            assert "recall" in metrics
            assert "f1" in metrics
            assert "auc" in metrics

    # Verify output report
    report_path = BACKEND_ROOT / "reports" / "r11_smote_ablation.json"
    assert report_path.exists()
    with open(report_path, "r", encoding="utf-8") as f:
        loaded = json.load(f)
    assert "phish" in loaded
    assert "doc" in loaded
    assert "upi" in loaded
