"""
Tests for feature group ablation.
"""

from pathlib import Path
import json
import pytest
from ml.ablation.feature_ablation import run_feature_ablation

BACKEND_ROOT = Path(__file__).resolve().parents[3]


def test_run_feature_ablation():
    """Verify that feature group ablation runs correctly for phish and doc."""
    # Run for phish
    phish_res = run_feature_ablation("phish")
    assert isinstance(phish_res, dict)
    for group in ["group_a_lexical", "group_b_tfidf", "group_c_combined"]:
        assert group in phish_res
        assert "f1" in phish_res[group]
        assert "delta_f1" in phish_res[group]

    # Run for doc
    doc_res = run_feature_ablation("doc")
    assert isinstance(doc_res, dict)
    for group in ["group_a_ela", "group_b_metadata", "group_c_combined"]:
        assert group in doc_res
        assert "f1" in doc_res[group]
        assert "delta_f1" in doc_res[group]

    # Verify output report
    report_path = BACKEND_ROOT / "reports" / "r11_feature_ablation.json"
    assert report_path.exists()
    with open(report_path, "r", encoding="utf-8") as f:
        loaded = json.load(f)
    assert "phish" in loaded
    assert "doc" in loaded
