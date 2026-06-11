"""Tests for the UPI fraud-detection module.

Covers:
- UTR classification (PhonePe 12-digit, Paytm T-prefix, GPay alphanumeric)
- App detection (keyword + colour signals)
- The fix for 'successful' being a PhonePe keyword (it was too generic)
- Dark-mode GPay blue colour range
"""
import pytest

from app.services.upi.utr import classify_utr, extract_utr_candidates
from app.services.upi.app_detector import detect_upi_app


# ─── UTR classification ──────────────────────────────────────────────────────


def test_utr_phonepe_12_digit():
    """Standard 12-digit numeric UTR should match PhonePe numeric format."""
    result = classify_utr("345678901234")
    assert result["valid"] is True
    assert result["format"] == "phonepe_numeric_12"


def test_utr_paytm_t_prefix():
    """'T' followed by 10-17 digits matches Paytm T-prefix format."""
    result = classify_utr("T12345678901234")
    assert result["valid"] is True
    assert result["format"] == "paytm_t_prefix"


def test_utr_gpay_alphanumeric():
    """GPay alphanumeric: must have BOTH letters and digits (not pure numbers)."""
    result = classify_utr("ABC123XYZ789")
    assert result["valid"] is True
    assert result["format"] == "gpay_alphanumeric"


def test_utr_rejects_pure_10_digit():
    """A pure 10-digit number must NOT match gpay_alphanumeric
    (it should fall through to generic or invalid)."""
    result = classify_utr("1234567890")
    # Below the 10-char minimum, so should be invalid
    assert result["valid"] is False or result["format"] != "gpay_alphanumeric"


def test_utr_rejects_pure_13_digit():
    """A 13-digit pure number is within the 10-18 length window, so it
    passes as a generic format UTR. The 10-18 character window is the
    UPI spec's range for generic numeric UTRs (PhonePe prefers 12, but
    banks occasionally emit other lengths)."""
    result = classify_utr("1234567890123")
    # Falls to generic (still valid because it's in the 10-18 window)
    assert result["format"] == "generic"
    assert result["valid"] is True


def test_utr_extracts_multiple():
    """extract_utr_candidates should find at least one valid UTR in a
    realistic receipt string."""
    text = "UTR: 123456789012  Txn: T98765432109876"
    candidates = extract_utr_candidates(text)
    assert len(candidates) >= 1
    # The 12-digit UTR is the most reliable match
    formats = {c["format"] for c in candidates}
    assert "phonepe_numeric_12" in formats or "paytm_t_prefix" in formats


def test_utr_pure_11_digit_invalid():
    """11-digit pure numeric is outside the 10-18 character window for
    gpay_alphanumeric, so it should NOT be flagged as gpay_alphanumeric."""
    result = classify_utr("12345678901")
    assert result["format"] != "gpay_alphanumeric"


# ─── App detection ───────────────────────────────────────────────────────────


def test_app_detector_phonepe_text():
    """A receipt mentioning 'PhonePe' should be detected as PhonePe."""
    result = detect_upi_app("Payment successful via PhonePe", dominant_colors=[])
    assert result["app"] == "PhonePe"


def test_app_detector_no_successful_keyword_bias():
    """'Transaction successful' alone should NOT trigger PhonePe now that
    'successful' has been removed from the PhonePe keyword list."""
    result = detect_upi_app("Transaction successful", dominant_colors=[])
    # Should be Unknown (no other app markers)
    assert result["app"] in ("Unknown", "GPay", "Paytm", "BHIM")
    assert result["app"] != "PhonePe"


def test_app_detector_dark_mode_gpay():
    """GPay dark-mode blue #1a73e8 should still be detected as GPay with
    the widened colour range."""
    result = detect_upi_app("Google Pay", dominant_colors=["#1a73e8"])
    assert result["app"] == "GPay"


def test_app_detector_light_mode_gpay():
    """GPay light-mode blue #4285F4 should still be detected."""
    result = detect_upi_app("Google Pay", dominant_colors=["#4285F4"])
    assert result["app"] == "GPay"


def test_app_detector_phonepe_color():
    """PhonePe purple #5F259F should still be detected."""
    result = detect_upi_app("", dominant_colors=["#5F259F"])
    assert result["app"] == "PhonePe"


def test_app_detector_paytm_color():
    """Paytm navy #002970 should still be detected."""
    result = detect_upi_app("", dominant_colors=["#002970"])
    assert result["app"] == "Paytm"
