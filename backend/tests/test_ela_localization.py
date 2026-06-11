"""
Tests for the adaptive ELA tamper localisation feature.

Key behaviors tested:
  1. Adaptive 95th-percentile threshold instead of a global pixel threshold
  2. Contour detection returns per-region bbox, polygon, area_ratio, confidence
  3. Dark-mode images don't trigger false positives
  4. The return shape is stable for existing callers
"""
import pytest
from pathlib import Path
from PIL import Image
import numpy as np

from app.services.upi.screenshot_forensics import run_image_ela


class TestELATamperLocalization:
    """Test suite for ELA region detection."""

    @pytest.fixture
    def tmp_image_dir(self, tmp_path):
        """Provide a temporary directory that auto-cleans."""
        return tmp_path

    def test_ela_returns_tamper_regions(self, tmp_image_dir):
        """ELA should return tamper_regions as a list of dicts with bbox + polygon."""
        # Create a white image with a clearly different color block.
        # The red block should be detected as a tamper region.
        img = Image.new("RGB", (800, 600), color="white")
        pixels = img.load()
        for x in range(200, 400):
            for y in range(150, 350):
                pixels[x, y] = (255, 0, 0)  # Red square in middle

        test_path = tmp_image_dir / "white_red_block.jpg"
        img.save(test_path, "JPEG")

        result = run_image_ela(test_path)

        # Response must contain tamper_regions key with a list
        assert "tamper_regions" in result
        assert isinstance(result["tamper_regions"], list)

        # At least one region should be detected (the red block)
        # Note: we surface regions even when tamper_suspected is False, so we can have
        # regions list populated.
        assert len(result["tamper_regions"]) >= 1, "Expected at least one tamper region"

        region = result["tamper_regions"][0]
        assert "bbox" in region, "Region must have bbox"
        assert "polygon" in region, "Region must have polygon"
        assert "area_ratio" in region, "Region must have area_ratio"
        assert "confidence" in region, "Region must have confidence"
        assert len(region["bbox"]) == 4, "bbox must be [x, y, w, h]"

    def test_ela_adaptive_threshold_dark_mode(self, tmp_image_dir):
        """Adaptive threshold should not flag entire dark-mode image as tampered."""
        # Simulate a dark-mode screenshot (e.g. GPay dark, AMOLED).
        # The previous global threshold (25) would flag most pixels because
        # recompression noise exceeds it across the whole image.
        img = Image.new("RGB", (800, 600), color=(20, 20, 20))

        test_path = tmp_image_dir / "dark_mode.jpg"
        img.save(test_path, "JPEG")

        result = run_image_ela(test_path)

        # With adaptive threshold, the whole image should not be flagged.
        assert result["hotspot_ratio"] < 0.5, (
            "Dark-mode images should not have massive hotspot ratios"
        )
        # Should NOT be suspected as tampered.
        assert result["tamper_suspected"] is False, (
            "Dark-mode images should not be flagged as tampered"
        )

    def test_ela_bright_image_baseline(self, tmp_image_dir):
        """Bright but otherwise clean image should have near-zero hotspot ratio."""
        img = Image.new("RGB", (800, 600), color=(240, 240, 240))

        test_path = tmp_image_dir / "bright_clean.jpg"
        img.save(test_path, "JPEG")

        result = run_image_ela(test_path)

        # Bright, clean images compress very consistently.
        assert result["hotspot_ratio"] < 0.01
        assert result["tamper_suspected"] is False

    def test_ela_region_bbox_approximates_location(self, tmp_image_dir):
        """The detected region bbox should roughly contain the edited area."""
        # Create an image with a single edited rectangle in the top-left.
        img = Image.new("RGB", (800, 600), color="white")
        pixels = img.load()
        for x in range(50, 200):
            for y in range(50, 200):
                pixels[x, y] = (0, 255, 0)  # Green top-left square

        test_path = tmp_image_dir / "top_left_edit.jpg"
        img.save(test_path, "JPEG")

        result = run_image_ela(test_path)

        if result["tamper_regions"]:
            region = result["tamper_regions"][0]
            bbox = region["bbox"]
            x, y, w, h = bbox

            # The region should overlap with the edit area [50, 50, 150, 150]
            # We're not asserting exact equality because of dilation + contour shape,
            # but approximate containment.
            assert x < 250, "Region x should be near the edit"
            assert y < 250, "Region y should be near the edit"
            assert w > 10, "Region width should be non-trivial"
            assert h > 10, "Region height should be non-trivial"

    def test_ela_response_shape_stable(self, tmp_image_dir):
        """The return dict shape must stay stable for existing consumers."""
        img = Image.new("RGB", (100, 100), color="white")
        test_path = tmp_image_dir / "stable.jpg"
        img.save(test_path, "JPEG")

        result = run_image_ela(test_path)

        # These keys must always be present.
        expected_keys = {
            "ela_score",
            "tamper_suspected",
            "hotspot_ratio",
            "mean_difference",
            "max_difference",
            "tamper_regions",
            "warnings",
        }
        assert expected_keys == set(result.keys()), "Response shape must be stable"

    def test_ela_handles_missing_file(self):
        """Should return a stable error response for missing files."""
        result = run_image_ela(Path("/does/not/exist.jpg"))

        assert result["ela_score"] == 0
        assert result["tamper_suspected"] is False
        assert result["tamper_regions"] == []
        assert "does not exist" in result["warnings"][0].lower()