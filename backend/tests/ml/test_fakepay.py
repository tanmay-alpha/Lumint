"""
Unit tests for the FakePay Baseline implementation.
Verifies feature extraction, tabular mapping, and model fitting/prediction.
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd
from PIL import Image
import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from ml.baselines.fakepay_baseline import FakePayBaseline


def test_fakepay_ocr_feature_extraction():
    baseline = FakePayBaseline()
    
    # Genuine/Standard text
    text_1 = "Paid to John Doe ₹500 Transaction Successful UTR: 312345678901"
    features_1 = baseline.extract_ocr_features(text_1, 0.95)
    
    assert features_1[0] == 1.0  # UTR extracted
    assert features_1[1] == 1.0  # Amount extracted
    assert features_1[2] == 1.0  # Recipient extracted
    assert features_1[3] == 1.0  # UTR format valid
    assert features_1[4] == 1.0  # Amount format valid
    assert features_1[5] == 0.95 # OCR confidence

    # Missing fields
    text_2 = "Failed payment screen with no info"
    features_2 = baseline.extract_ocr_features(text_2, 0.5)
    
    assert features_2[0] == 0.0
    assert features_2[1] == 0.0
    assert features_2[2] == 0.0
    assert features_2[3] == 0.0
    assert features_2[5] == 0.5


def test_fakepay_cnn_feature_extraction():
    baseline = FakePayBaseline()
    
    # Create simple 100x100 RGB image
    img = Image.new("RGB", (100, 100), color=(73, 109, 137))
    cnn_feats = baseline.extract_cnn_features(img)
    
    assert len(cnn_feats) == 512
    assert isinstance(cnn_feats, np.ndarray)


def test_fakepay_tabular_mapping():
    baseline = FakePayBaseline()
    
    # Construct mock pandas DataFrame mimicking upi_dataset.csv
    data = {
        "forgery_score_heuristic": [10.0, 85.0],
        "utr_valid": [1, 0],
        "utr_length": [12, 0],
        "ela_tamper_regions": [0.01, 0.75],
        "font_consistent": [1.0, 0.0],
        "color_authentic": [1.0, 0.0],
        "ocr_confidence": [0.98, 0.40],
        "app_detected_encoded": [1, 2],
        "label": [0, 1]
    }
    df = pd.DataFrame(data)
    
    X, y = baseline.map_tabular_to_fakepay(df)
    
    assert X.shape == (2, 518)
    assert np.array_equal(y, np.array([0, 1]))
    
    # Validate feature properties
    # Genuine row (idx=0) should have clean visual cnn features
    # Forged row (idx=1) should have visual features corresponding to tamper
    assert X[0, 3] == 1.0  # utr_valid
    assert X[1, 3] == 0.0  # utr_valid
    assert X[0, 5] == 0.98 # ocr_confidence
    assert X[1, 5] == 0.40 # ocr_confidence


def test_fakepay_model_fit_predict():
    baseline = FakePayBaseline()
    
    # Create synthetic dataset of 10 samples
    X = np.random.randn(10, 518)
    y = np.array([0, 0, 0, 0, 0, 1, 1, 1, 1, 1])
    
    baseline.fit(X, y)
    assert baseline.is_fitted
    
    y_pred = baseline.predict(X)
    assert len(y_pred) == 10
    
    y_prob = baseline.predict_proba(X)
    assert y_prob.shape == (10, 2)
    assert np.all(y_prob >= 0.0) and np.all(y_prob <= 1.0)
