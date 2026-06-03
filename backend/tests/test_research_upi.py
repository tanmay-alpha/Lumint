import tempfile
from pathlib import Path
import pytest
from PIL import Image, ImageDraw

from app.services.upi.ocr_adapter import extract_text_from_image
from app.services.upi.app_detector import detect_upi_app
from app.services.upi.utr import validate_utr, extract_utr_candidates
from app.services.upi.color_profile import check_color_authenticity, extract_dominant_colors
from app.services.upi.screenshot_forensics import run_image_ela, estimate_tamper_regions
from app.services.upi.font_consistency import check_font_consistency
from app.services.upi.analyzer import analyze_upi_screenshot

@pytest.fixture
def dummy_image_path():
    """Create a dummy image to test image forensic logic."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
        # Create a simple 200x200 purple image (PhonePe color)
        img = Image.new("RGB", (200, 200), color=(95, 37, 159))
        draw = ImageDraw.Draw(img)
        # Add some text-like stripes to simulate text boxes for font checker
        for y in range(20, 180, 20):
            draw.rectangle([20, y, 180, y + 10], fill=(255, 255, 255))
        img.save(tmp.name)
        tmp_path = Path(tmp.name)
        
    yield tmp_path
    
    try:
        tmp_path.unlink()
    except Exception:
        pass

def test_ocr_adapter_fallback():
    # If file doesn't exist, it should return fallback text
    res = extract_text_from_image(Path("non_existent_file.png"), fallback_text="Test fallback text")
    assert res["text"] == "Test fallback text"
    assert res["confidence"] == 1.0

def test_detect_upi_app():
    # Test text-based matching
    ph_res = detect_upi_app("This is a phonepe txn with ybl@upi handle.")
    assert ph_res["app"] == "PhonePe"
    assert ph_res["confidence"] > 0.50
    
    # Test color matching (PhonePe purple)
    color_ph = detect_upi_app("Unknown receipt", dominant_colors=["#5f259f"])
    assert color_ph["app"] == "PhonePe"
    assert color_ph["confidence"] > 0.50
    
    # Test unknown app
    unk_res = detect_upi_app("Random text without matches")
    assert unk_res["app"] == "Unknown"
    assert unk_res["confidence"] == 0.20

def test_utr_validation():
    # PhonePe UTR starts with '3' or '4' (12 digits)
    ph_utr = validate_utr("318273645192", app_hint="PhonePe")
    assert ph_utr["valid"] is True
    
    # Invalid length
    invalid_len = validate_utr("3182736", app_hint="PhonePe")
    assert invalid_len["valid"] is False
    
    # PhonePe with non-12-digit UTR is suspicious/invalid
    ph_invalid_res = validate_utr("T24060212345", app_hint="PhonePe")
    assert ph_invalid_res["valid"] is False

def test_extract_utr_candidates():
    text = "Payment reference UTR: 418273645192 or alternate 318273645192"
    candidates = extract_utr_candidates(text)
    assert len(candidates) >= 2
    assert candidates[0]["value"] == "418273645192"

def test_color_authenticity(dummy_image_path):
    # Test with PhonePe
    res = check_color_authenticity(dummy_image_path, "PhonePe")
    assert res["color_authentic"] is True
    assert res["distance"] is not None
    
    # Test Paytm brand mismatch
    res_mismatch = check_color_authenticity(dummy_image_path, "Paytm")
    assert res_mismatch["color_authentic"] is False

def test_screenshot_ela(dummy_image_path):
    res = run_image_ela(dummy_image_path)
    assert "ela_score" in res
    assert "tamper_suspected" in res
    assert isinstance(res["tamper_regions"], list)

def test_font_consistency(dummy_image_path):
    res = check_font_consistency(dummy_image_path)
    assert "font_consistent" in res
    assert "height_variance" in res

def test_pipeline_analyzer(dummy_image_path):
    res = analyze_upi_screenshot(
        dummy_image_path,
        custom_ocr_text="PhonePe UPI Payment Successful. UTR Ref: 318273645192. Amount Rs. 15,200.00"
    )
    assert res["analysis_status"] == "completed"
    assert res["app_detected"] == "PhonePe"
    assert res["utr"]["valid"] is True
    assert res["amount_extracted"] == "15,200.00"
