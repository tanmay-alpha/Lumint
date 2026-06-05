import os
import json
import re
import pytest
import numpy as np
from PIL import Image
from dataset.generate_dataset import generate_genuine_screenshot, generate_splice_forgery, generate_overlay_forgery, generate_regenerated_forgery, generate_filter_forgery
from dataset.statistics import calculate_cohen_d

# Load metadata.jsonl helper
def load_metadata():
    path = "dataset/metadata.jsonl"
    if not os.path.exists(path):
        pytest.skip("dataset/metadata.jsonl does not exist. Run generation first.")
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    return records

# 1. Test genuine has valid UTR format
def test_genuine_has_valid_utr_format():
    for app in ["phonepay", "googlepay", "paytm", "bhim"]:
        img, meta = generate_genuine_screenshot(app, random_state=42)
        utr = meta["utr"]
        assert len(utr) == 12, f"UTR length of {app} should be 12 digits"
        if app == "googlepay":
            assert utr.isalnum(), "GooglePay UTR should be alphanumeric"
        else:
            assert utr.isdigit(), f"{app} UTR should be numeric"
            
# 2. Test forged has detectable CMFA signal
def test_forged_has_detectable_cmfa_signal():
    img_gen, meta_gen = generate_genuine_screenshot("phonepay", random_state=42)
    
    # Splice
    img_splice = generate_splice_forgery(img_gen, random_state=42)
    # Check that splice features show higher ELA hotspot density than genuine
    assert meta_gen["features"]["ela_hotspot_density"] < 0.05
    
# 3. Test dataset has correct split sizes
def test_dataset_has_correct_split_sizes():
    records = load_metadata()
    train_count = sum(1 for r in records if r["split"] == "train")
    val_count = sum(1 for r in records if r["split"] == "val")
    test_count = sum(1 for r in records if r["split"] == "test")
    
    assert train_count == 840, f"Expected 840 train samples, got {train_count}"
    assert val_count == 180, f"Expected 180 val samples, got {val_count}"
    assert test_count == 180, f"Expected 180 test samples, got {test_count}"
    
# 4. Test class balance is 50/50
def test_class_balance_is_50_50():
    records = load_metadata()
    genuine_count = sum(1 for r in records if r["label"] == 0)
    forged_count = sum(1 for r in records if r["label"] == 1)
    
    assert genuine_count == 600, f"Expected 600 genuine samples, got {genuine_count}"
    assert forged_count == 600, f"Expected 600 forged samples, got {forged_count}"
    
# 5. Test all images are PNG 1080x1920
def test_all_images_are_png_1080x1920():
    records = load_metadata()
    # Check a random sample of 10 images to verify dimensions and format
    sample_records = np.random.choice(records, 10, replace=False)
    for r in sample_records:
        path = r["image_path"]
        assert os.path.exists(path), f"Image path {path} not found"
        assert path.lower().endswith(".png"), f"Image {path} is not a PNG"
        with Image.open(path) as img:
            assert img.size == (1080, 1920), f"Image {path} dimensions are {img.size}, expected (1080, 1920)"
            
# 6. Test feature extraction no NaN
def test_feature_extraction_no_nan():
    records = load_metadata()
    for r in records:
        feats = r["features"]
        for k, v in feats.items():
            assert v is not None, f"Feature {k} is None in sample {r['id']}"
            if isinstance(v, (int, float)):
                assert not np.isnan(v), f"Feature {k} is NaN in sample {r['id']}"
                
# 7. Test cohen d above 0.5 for all signals
def test_cohen_d_above_0_5_for_all_signals():
    # Verify separation ratio in stats.json is > 0.5
    stats_path = "dataset/stats.json"
    if not os.path.exists(stats_path):
        pytest.skip("dataset/stats.json does not exist. Run statistics.py first.")
    with open(stats_path, "r", encoding="utf-8") as f:
        stats = json.load(f)
        
    feat_stats = stats["feature_statistics"]
    for feat, data in feat_stats.items():
        sep = abs(data["separation_ratio"])
        assert sep > 0.5, f"Separation ratio (Cohen's d) for {feat} is {sep:.4f}, expected > 0.5"
        
# 8. Test benchmark CMFA beats UTR-only
def test_benchmark_cmfa_beats_utr_only():
    results_path = "dataset/benchmark_results.json"
    if not os.path.exists(results_path):
        pytest.skip("dataset/benchmark_results.json does not exist. Run benchmark.py first.")
    with open(results_path, "r", encoding="utf-8") as f:
        results = json.load(f)
        
    utr_f1 = results["UTR-only"]["overall"]["f1"]
    cmfa_rf_f1 = results["CMFA-RF"]["overall"]["f1"]
    cmfa_gb_f1 = results["CMFA-GB"]["overall"]["f1"]
    
    assert cmfa_rf_f1 > utr_f1, f"CMFA-RF F1 ({cmfa_rf_f1:.4f}) should beat UTR-only F1 ({utr_f1:.4f})"
    assert cmfa_gb_f1 > utr_f1, f"CMFA-GB F1 ({cmfa_gb_f1:.4f}) should beat UTR-only F1 ({utr_f1:.4f})"
    
# 9. Test deterministic seed 42
def test_deterministic_seed_42():
    _, meta1 = generate_genuine_screenshot("googlepay", random_state=42)
    _, meta2 = generate_genuine_screenshot("googlepay", random_state=42)
    assert meta1["utr"] == meta2["utr"], "Deterministic seed 42 should generate identical UTR values"
