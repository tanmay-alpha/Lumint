"""
Tests for global SHAP analysis.
"""

from pathlib import Path
import json
import pytest
from ml.ablation.shap_analysis import run_global_shap

BACKEND_ROOT = Path(__file__).resolve().parents[3]


def test_run_global_shap():
    """Verify that global SHAP analysis runs correctly for phish, doc, and upi."""
    for module in ["phish", "doc", "upi"]:
        res = run_global_shap(module)
        assert isinstance(res, dict)
        assert res["module"] == module
        assert "top_features" in res
        assert isinstance(res["top_features"], list)
        
        # Verify first top feature
        if len(res["top_features"]) > 0:
            feat = res["top_features"][0]
            assert "rank" in feat
            assert "name" in feat
            assert "mean_abs_shap" in feat
            assert "direction" in feat
            assert "interpretation" in feat
            assert "beeswarm" in feat
            assert isinstance(feat["beeswarm"], list)

        # Verify output report
        report_path = BACKEND_ROOT / "reports" / f"r11_{module}_shap_global.json"
        assert report_path.exists()
        with open(report_path, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        assert loaded["module"] == module
