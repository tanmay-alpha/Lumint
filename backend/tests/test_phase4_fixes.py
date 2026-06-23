"""Regression tests for Phase 4 audit fixes.

P4.2: UPI analyzer must not emit fake sentinel VPA strings like
"unknown@upi" or "unknown@merchant" when no VPA is parseable.
Downstream consumers must be able to distinguish "no VPA detected" from
a real VPA, otherwise an attacker could craft a screenshot that omits
the VPA to make the real sender/receiver harder to find.

P4.7: Font-consistency threshold is per-app. PhonePe and Google Pay
legitimately use a large amount line + small body labels, so the
height-variance cutoff must be relaxed to 160.0 for those apps. Paytm,
BHIM, and unknown apps keep the conservative 110.0 cutoff.
"""

import re
import sys
import types
from pathlib import Path
from unittest.mock import patch

import numpy as np

from app.services.upi.analyzer import (
    _extract_metadata,
    parse_vpas,
    select_payee_vpa,
)
from app.services.upi.font_consistency import (
    DEFAULT_HEIGHT_VARIANCE_THRESHOLD,
    HIGH_VARIANCE_HEIGHT_VARIANCE_THRESHOLD,
    _resolve_threshold,
    check_font_consistency,
)


# A screenshot-like payload that contains *no* parseable VPA.
NO_VPA_TEXT = (
    "Transaction successful\n"
    "Amount: Rs. 499.00\n"
    "UTR: 123456789012\n"
    "Date: 2026-06-19\n"
    "To: Some Merchant\n"
    "Status: Completed\n"
)

# Regex to detect any leftover "unknown*" sentinel in serialized output.
_SENTINEL_RE = re.compile(r"^unknown", re.IGNORECASE)


def _stringify(value):
    """Recursively collect every string in a nested response structure."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for v in value.values():
            yield from _stringify(v)
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            yield from _stringify(item)


def test_parse_vpas_returns_empty_list_for_no_vpa_text():
    """No VPA-shaped tokens are present, so parse_vpas must return []."""
    assert parse_vpas(NO_VPA_TEXT) == []


def test_select_payee_vpa_returns_none_when_no_vpa():
    """No payee VPA is detectable, so select_payee_vpa must return None."""
    vpas = parse_vpas(NO_VPA_TEXT)
    assert select_payee_vpa(NO_VPA_TEXT, vpas) is None


def test_extract_metadata_emits_none_sender_when_no_vpa():
    """_extract_metadata must return sender_vpa=None, not a sentinel string."""
    metadata = _extract_metadata(NO_VPA_TEXT)
    assert metadata["sender_vpa"] is None
    assert metadata["payee_vpa"] is None


def test_response_shape_with_no_vpa_has_no_sentinel_strings():
    """The built response (mirroring analyzer._build_response contract) must:
    - have sender_upi_id is None
    - have receiver_upi_id is None
    - contain no string starting with "unknown"
    """
    metadata = _extract_metadata(NO_VPA_TEXT)
    payee_vpa = metadata["payee_vpa"]
    vpas = parse_vpas(NO_VPA_TEXT)

    response = {
        "sender_upi_id": metadata["sender_vpa"],
        "receiver_upi_id": payee_vpa if payee_vpa else (vpas[1] if len(vpas) > 1 else None),
        "amount_extracted": metadata["amount"],
        "payee_vpa": payee_vpa,
    }

    # Both VPA fields must be None, not a sentinel string.
    assert response["sender_upi_id"] is None
    assert response["receiver_upi_id"] is None

    # No string in the response may start with "unknown" (case-insensitive).
    leaked = [s for s in _stringify(response) if _SENTINEL_RE.match(s.strip())]
    assert leaked == [], f"Unexpected sentinel strings leaked: {leaked}"


def test_vpa_omission_screenshot_response_has_no_unknown_strings():
    """End-to-end: feed a screenshot-like payload with no VPA and assert that
    the full response-shaped dict contains no string starting with 'unknown'.
    This guards against the attacker scenario: omitting the VPA to make
    downstream consumers fall back to a fake address.
    """
    metadata = _extract_metadata(NO_VPA_TEXT)
    payee_vpa = metadata["payee_vpa"]
    vpas = parse_vpas(NO_VPA_TEXT)

    response = {
        "analysis_status": "completed",
        "app_detected": "unknown",
        "utr": {"value": metadata["primary_utr"], "is_valid": True},
        "amount_extracted": metadata["amount"],
        "payee_vpa": payee_vpa,
        "sender_upi_id": metadata["sender_vpa"],
        "receiver_upi_id": payee_vpa if payee_vpa else (vpas[1] if len(vpas) > 1 else None),
        "warnings": [],
    }

    # Allow 'unknown' as a literal *value of app_detected* (an app name), but
    # forbid *any string starting with "unknown"* as a VPA / address.
    leaked = [s for s in _stringify(response) if _SENTINEL_RE.match(s.strip())]
    # Filter out the legitimate 'unknown' app label — we are only concerned
    # with VPA-shaped sentinels.
    leaked = [s for s in leaked if "@" in s]
    assert leaked == [], f"VPA sentinel strings leaked: {leaked}"

    assert response["sender_upi_id"] is None
    assert response["receiver_upi_id"] is None


# ──────────────────────────────────────────────────────────────────────
# P4.7: Per-app font-consistency threshold
# ──────────────────────────────────────────────────────────────────────

# A variance value that sits between the two thresholds (110 < v < 160).
# At this value the function must report forgery under the default
# threshold but pass under the relaxed PhonePe/GPay threshold.
INTERMEDIATE_VARIANCE = 135.0


def _fake_image_path() -> Path:
    """Return a dummy Path object (we never actually read from disk —
    cv2.imread is mocked)."""
    return Path("dummy.png")


def _heights_for_target_variance(target_variance: float, n: int = 20) -> list:
    """Build a list of `n` integer heights whose numpy population variance
    is approximately ``target_variance``.

    We split the list in half and put one half at ``mean + d`` and the
    other at ``mean - d``. For a symmetric ±d pair over n elements,
    ``np.var == d ** 2``. Solving for ``d`` gives ``d = sqrt(target)``.

    The integer-rounding step can perturb the final variance by a few
    units; tests use a tolerance band around the target value.
    """
    if target_variance <= 0:
        return [10] * n
    d = target_variance ** 0.5
    mean = 20
    half = n // 2
    heights = [mean + d] * half + [mean - d] * (n - half)
    # Clip into the [6, 45] acceptance band so the function counts them.
    clipped = [max(6, min(45, int(round(h)))) for h in heights]
    return clipped


def _make_fake_cv2(heights: list):
    """Return a ``cv2`` module stub whose ``findContours`` returns one
    contour per height in ``heights``, with boundingRect h=height and w=10.
    """
    fake = types.ModuleType("cv2")
    fake.IMREAD_GRAYSCALE = 0
    fake.ADAPTIVE_THRESH_GAUSSIAN_C = 1
    fake.THRESH_BINARY_INV = 2
    fake.MORPH_CLOSE = 3
    fake.RETR_EXTERNAL = 4
    fake.CHAIN_APPROX_SIMPLE = 5

    img = np.zeros((200, 200), dtype=np.uint8)

    fake.imread = lambda *_a, **_k: img
    fake.adaptiveThreshold = lambda *_a, **_k: img
    fake.morphologyEx = lambda *_a, **_k: img

    contours = [((0, 0, 10, h),) for h in heights]
    fake.findContours = lambda *_a, **_k: (contours, None)
    fake.boundingRect = lambda c: (0, 0, 10, c[0][3])

    return fake


def _run_with_variance(variance: float, *, app_hint, tmp_path: Path):
    """Drive ``check_font_consistency`` with a stubbed cv2 pipeline whose
    produced heights have approximately the target variance.

    Writes a real (empty) image file to ``tmp_path`` so the function's
    ``Path.exists()`` guard passes; the contents are irrelevant because
    ``cv2.imread`` is mocked.
    """
    heights = _heights_for_target_variance(variance)
    fake_cv2 = _make_fake_cv2(heights)
    image_path = tmp_path / "dummy.png"
    image_path.write_bytes(b"\x00")

    with patch.dict(sys.modules, {"cv2": fake_cv2}):
        return check_font_consistency(
            image_path, ocr_text=None, app_hint=app_hint
        )


def test_resolve_threshold_defaults_to_110_when_no_hint():
    """Backward-compat: app_hint=None keeps the historical 110.0 cutoff."""
    assert _resolve_threshold(None) == DEFAULT_HEIGHT_VARIANCE_THRESHOLD
    assert DEFAULT_HEIGHT_VARIANCE_THRESHOLD == 110.0


def test_resolve_threshold_uses_160_for_phonepe_and_gpay():
    """PhonePe and Google Pay (case-insensitive) get the relaxed 160.0 cutoff."""
    assert _resolve_threshold("phonepe") == HIGH_VARIANCE_HEIGHT_VARIANCE_THRESHOLD
    assert _resolve_threshold("PhonePe") == HIGH_VARIANCE_HEIGHT_VARIANCE_THRESHOLD
    assert _resolve_threshold("gpay") == HIGH_VARIANCE_HEIGHT_VARIANCE_THRESHOLD
    assert _resolve_threshold("GPay") == HIGH_VARIANCE_HEIGHT_VARIANCE_THRESHOLD
    assert HIGH_VARIANCE_HEIGHT_VARIANCE_THRESHOLD == 160.0


def test_resolve_threshold_uses_110_for_paytm_and_bhim():
    """Paytm and BHIM keep the conservative 110.0 cutoff."""
    assert _resolve_threshold("paytm") == DEFAULT_HEIGHT_VARIANCE_THRESHOLD
    assert _resolve_threshold("bhim") == DEFAULT_HEIGHT_VARIANCE_THRESHOLD
    assert _resolve_threshold("unknown") == DEFAULT_HEIGHT_VARIANCE_THRESHOLD


def test_check_font_consistency_default_threshold_flags_intermediate_variance(tmp_path):
    """With app_hint=None and variance≈135, the default 110 cutoff flags
    the receipt as font-inconsistent (existing behaviour preserved)."""
    result = _run_with_variance(INTERMEDIATE_VARIANCE, app_hint=None, tmp_path=tmp_path)
    assert result["font_consistent"] is False
    # Variance can shift slightly due to int rounding of the synthetic
    # heights; the tolerance is well within the (110, 160) band that
    # distinguishes the two thresholds, so the assertion stays meaningful.
    assert result["height_variance"] is not None
    assert abs(result["height_variance"] - INTERMEDIATE_VARIANCE) <= 15.0, (
        f"Variance drifted too far: got {result['height_variance']}, "
        f"target {INTERMEDIATE_VARIANCE}"
    )


def test_check_font_consistency_phonepe_passes_intermediate_variance(tmp_path):
    """With app_hint='phonepe' and variance≈135, the relaxed 160 cutoff
    must report the receipt as font-consistent. This is the bug fix."""
    result = _run_with_variance(INTERMEDIATE_VARIANCE, app_hint="phonepe", tmp_path=tmp_path)
    assert result["font_consistent"] is True
    assert result["height_variance"] is not None
    assert abs(result["height_variance"] - INTERMEDIATE_VARIANCE) <= 15.0


def test_check_font_consistency_gpay_passes_intermediate_variance(tmp_path):
    """With app_hint='gpay' and variance≈135, the relaxed 160 cutoff
    must report the receipt as font-consistent."""
    result = _run_with_variance(INTERMEDIATE_VARIANCE, app_hint="gpay", tmp_path=tmp_path)
    assert result["font_consistent"] is True
    assert result["height_variance"] is not None
    assert abs(result["height_variance"] - INTERMEDIATE_VARIANCE) <= 15.0


def test_check_font_consistency_paytm_flags_intermediate_variance(tmp_path):
    """With app_hint='paytm' and variance=135, the conservative 110 cutoff
    still flags the receipt (Paytm does not get the relaxed threshold)."""
    result = _run_with_variance(INTERMEDIATE_VARIANCE, app_hint="paytm", tmp_path=tmp_path)
    assert result["font_consistent"] is False


def test_check_font_consistency_extreme_variance_flagged_for_all_apps(tmp_path):
    """A truly extreme variance (e.g. 500) must still flag forgery even on
    PhonePe / GPay, otherwise the relaxed threshold could let real
    forgeries through."""
    extreme = 500.0
    for hint in (None, "phonepe", "gpay", "paytm", "bhim"):
        result = _run_with_variance(extreme, app_hint=hint, tmp_path=tmp_path)
        assert result["font_consistent"] is False, (
            f"Expected forgery flag for extreme variance under app_hint={hint!r}, "
            f"got font_consistent={result['font_consistent']}"
        )


def test_check_font_consistency_low_variance_passes_for_all_apps(tmp_path):
    """A low variance (e.g. 30) must always pass, regardless of app."""
    low = 30.0
    for hint in (None, "phonepe", "gpay", "paytm", "bhim"):
        result = _run_with_variance(low, app_hint=hint, tmp_path=tmp_path)
        assert result["font_consistent"] is True, (
            f"Expected genuine flag for low variance under app_hint={hint!r}, "
            f"got font_consistent={result['font_consistent']}"
        )


# ────────────────────────────────────────────────────────────────────
# P4.8: color_profile multi-anchor palette
# ────────────────────────────────────────────────────────────────────


def test_color_profile_palette_contains_primary_and_text():
    """Each app's palette must contain the primary brand color and a
    white text/accent anchor. A single-anchor palette would misclassify
    legitimate PhonePe (purple bg + white text) and BHIM (saffron +
    white) screenshots as forgeries.
    """
    from app.services.upi.color_profile import REFERENCE_COLORS, _palette_for

    for app in ("PhonePe", "GPay", "Paytm", "BHIM"):
        assert app in REFERENCE_COLORS, f"{app} missing from REFERENCE_COLORS"
        palette = _palette_for(app)
        assert len(palette) >= 2, (
            f"{app} palette must contain at least the primary color and a "
            f"white text anchor; got {len(palette)} entries"
        )
        # The primary color must be in the palette.
        assert REFERENCE_COLORS[app]["rgb"] in palette, (
            f"{app}'s primary color {REFERENCE_COLORS[app]['rgb']} missing "
            f"from its own palette {palette}"
        )
        # White must be in the palette (legitimate text/accent).
        assert (255, 255, 255) in palette, (
            f"{app}'s palette is missing the white text anchor; this will "
            f"false-flag legitimate screenshots whose dominant color is white"
        )


def test_color_profile_palette_matches_white_dominant(monkeypatch):
    """A screenshot whose dominant colors are white AND the app's primary
    color must be classified as authentic. This is the case the multi-
    anchor palette was added to fix: PhonePe receipts are purple +
    white; without the white anchor, the purple-only reference would
    accept the image but the white-only check would fail. With the
    palette, both dominant colors are within threshold of the palette
    AND at least one is within threshold of the primary.
    """
    from app.services.upi import color_profile
    from app.services.upi.color_profile import check_color_authenticity

    # Mock extract_dominant_colors to return PhonePe purple + white
    # (the standard PhonePe receipt layout). monkeypatch.setattr
    # restores the original function after the test.
    monkeypatch.setattr(
        color_profile,
        "extract_dominant_colors",
        lambda *a, **k: [
            {"hex": "#5f259f", "rgb": (95, 37, 159), "pct": 0.6},
            {"hex": "#ffffff", "rgb": (255, 255, 255), "pct": 0.4},
        ],
    )
    result = check_color_authenticity(image_path=None, app_detected="PhonePe")
    assert result["color_authentic"] is True, (
        f"PhonePe purple+white receipt must be authentic; got "
        f"color_authentic={result['color_authentic']}, distance={result['distance']}"
    )


def test_color_profile_pure_white_image_is_rejected(monkeypatch):
    """A pure-white image (no brand color at all) must NOT pass
    authenticity for any app — the primary-color guard prevents the
    white anchor from masking the absence of the brand color.
    """
    from app.services.upi import color_profile
    from app.services.upi.color_profile import check_color_authenticity

    monkeypatch.setattr(
        color_profile,
        "extract_dominant_colors",
        lambda *a, **k: [
            {"hex": "#ffffff", "rgb": (255, 255, 255), "pct": 1.0}
        ],
    )
    for app in ("PhonePe", "GPay", "Paytm", "BHIM"):
        result = check_color_authenticity(image_path=None, app_detected=app)
        assert result["color_authentic"] is False, (
            f"Pure-white image must NOT be authentic for {app}; the "
            f"primary-color guard should catch the missing brand color. "
            f"Got color_authentic={result['color_authentic']}, "
            f"distance={result['distance']}"
        )


def test_color_profile_phonepe_image_rejected_as_paytm(monkeypatch):
    """A PhonePe purple+white image, when claimed to be Paytm, must be
    flagged as inauthentic. Paytm's primary is navy (0, 41, 112); the
    PhonePe purple (95, 37, 159) is far from that, so the primary-color
    guard must trip.
    """
    from app.services.upi import color_profile
    from app.services.upi.color_profile import check_color_authenticity

    monkeypatch.setattr(
        color_profile,
        "extract_dominant_colors",
        lambda *a, **k: [
            {"hex": "#5f259f", "rgb": (95, 37, 159), "pct": 0.6},
            {"hex": "#ffffff", "rgb": (255, 255, 255), "pct": 0.4},
        ],
    )
    result = check_color_authenticity(image_path=None, app_detected="Paytm")
    assert result["color_authentic"] is False, (
        f"PhonePe purple+white image must NOT be authentic as Paytm; "
        f"got color_authentic={result['color_authentic']}, "
        f"distance={result['distance']}"
    )


def test_color_profile_unknown_app_returns_neutral(monkeypatch):
    """An unknown/unsupported app must return color_authentic=True
    (we don't false-flag unknown apps) with a confidence of 0.50.
    """
    from app.services.upi import color_profile
    from app.services.upi.color_profile import check_color_authenticity

    monkeypatch.setattr(
        color_profile,
        "extract_dominant_colors",
        lambda *a, **k: [
            {"hex": "#ff00ff", "rgb": (255, 0, 255), "pct": 1.0}
        ],
    )
    result = check_color_authenticity(image_path=None, app_detected="UnknownApp")
    assert result["color_authentic"] is True
    assert result["confidence"] == 0.50
