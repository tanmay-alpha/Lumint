"""
Test suite for cross-dataset generalization experiments.
Verifies logic, file saving, and metric constraints.
"""

import os
import json
import pytest
from unittest.mock import patch
import pandas as pd
from pathlib import Path
from ml.experiments.cross_dataset_eval import main as run_cross_dataset

def test_cross_dataset_evaluation(tmp_path):
    # Setup small mock datasets
    mock_real_csv = tmp_path / "phishing_uci.csv"
    mock_synth_csv = tmp_path / "phishing_dataset.csv"
    
    mock_json = tmp_path / "r12_cross_dataset_results.json"
    mock_md = tmp_path / "r12_cross_dataset_table.md"

    # Minimal balanced dataset for training/testing
    urls = [
        "http://example.com/login",
        "https://secure-bank.com/signin",
        "http://malicious-site.net/verify",
        "https://google.com",
        "http://paypal-verification-update.org/home",
        "https://github.com",
        "http://amazon-account-support.com",
        "https://netflix.com",
        "http://yahoo-check.net",
        "https://microsoft.com",
        "http://linkedin.com",
        "http://twitter.com"
    ]
    labels = [0, 1, 1, 0, 1, 0, 1, 0, 1, 0, 0, 1]  # 6 zeros, 6 ones

    df = pd.DataFrame({"url": urls, "label": labels})
    df.to_csv(mock_real_csv, index=False)
    df.to_csv(mock_synth_csv, index=False)

    # Patch file paths
    with patch("ml.experiments.cross_dataset_eval.REAL_DATA_CSV", mock_real_csv), \
         patch("ml.experiments.cross_dataset_eval.SYNTH_DATA_CSV", mock_synth_csv), \
         patch("ml.experiments.cross_dataset_eval.OUTPUT_JSON", mock_json), \
         patch("ml.experiments.cross_dataset_eval.OUTPUT_MD", mock_md):
        
        run_cross_dataset()

    # Assert outputs were successfully created
    assert mock_json.exists()
    assert mock_md.exists()

    # Assert JSON metrics validity
    with open(mock_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    expected_keys = [
        "same_distribution_real",
        "same_distribution_synth",
        "synth_train_real_test",
        "real_train_synth_test"
    ]
    
    for key in expected_keys:
        assert key in data
        metrics = data[key]
        for m in ["precision", "recall", "f1", "auc", "mcc"]:
            assert m in metrics
            val = metrics[m]
            assert isinstance(val, float)
            assert -1.0 <= val <= 1.0
