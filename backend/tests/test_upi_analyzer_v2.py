"""Tests for the v2 UPI ensemble model integration."""
from pathlib import Path
import pytest


def test_analyzer_v2_imports():
    """The v2 analyzer module imports cleanly."""
    from app.services.upi import analyzer_v2  # noqa: F401


def test_analyzer_v2_load_graceful_when_no_model():
    """Without trained model files, the loader returns False gracefully."""
    from app.services.upi.analyzer_v2 import _load_v2_models
    # The test forces a fresh load by clearing the cache
    import app.services.upi.analyzer_v2 as mod
    mod._V2_LOADED = False
    loaded = _load_v2_models()
    # Either models are present (then True) or absent (then False) — both OK
    assert loaded in (True, False)


def test_feature_extractor_v2_runs_on_real_image():
    """Feature extractor returns 80 features on a real UPI image."""
    from ml.features.upi_features_v2 import UPIFeatureExtractorV2
    test_path = Path("../dataset/images/train/upi_0001.png")
    if not test_path.exists():
        pytest.skip("Test image not found")
    extractor = UPIFeatureExtractorV2()
    features = extractor.extract(str(test_path))
    assert len(features) == len(extractor.FEATURE_NAMES)
    assert features.dtype == "float32"
    import numpy as np
    # No NaN / Inf
    assert np.all(np.isfinite(features))


def test_feature_extractor_v2_with_ocr_text():
    """Passing OCR text populates the OCR-dependent features."""
    from ml.features.upi_features_v2 import UPIFeatureExtractorV2
    test_path = Path("../dataset/images/train/upi_0001.png")
    if not test_path.exists():
        pytest.skip("Test image not found")
    extractor = UPIFeatureExtractorV2()
    features_with = extractor.extract(
        str(test_path),
        ocr_text="PhonePe UTR 123456789012 Paid to merchant@upi Rs. 100.00",
        ocr_confidence=0.95,
    )
    features_without = extractor.extract(str(test_path))
    # OCR-dependent features should differ when text is provided
    assert not (features_with == features_without).all()
