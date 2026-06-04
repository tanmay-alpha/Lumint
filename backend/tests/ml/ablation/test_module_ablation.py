"""
Tests for module ablation.
"""

from pathlib import Path
import json
import pytest
from ml.ablation.module_ablation import run_module_ablation

BACKEND_ROOT = Path(__file__).resolve().parents[3]


def test_run_module_ablation():
    """Verify that module ablation runs and returns correct configurations."""
    results = run_module_ablation()
    
    # Assert return types and structures
    assert isinstance(results, dict)
    expected_configs = ["full", "no_doc", "no_phish", "no_upi", "phish_only", "doc_only", "upi_only"]
    for config in expected_configs:
        assert config in results
        metrics = results[config]
        assert "f1" in metrics
        assert "auc" in metrics
        assert "mcc" in metrics
        assert "delta_f1" in metrics

    # Verify report is written
    report_path = BACKEND_ROOT / "reports" / "r11_module_ablation.json"
    assert report_path.exists()
    with open(report_path, "r", encoding="utf-8") as f:
        loaded = json.load(f)
    assert "full" in loaded
