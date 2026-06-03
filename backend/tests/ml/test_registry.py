"""
Tests for ModelRegistry — R9 ML Baseline.
All deterministic, no network calls, random_state=42.
"""

import sys
from pathlib import Path

import numpy as np
import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from ml.registry import ModelRegistry


class TestRegistry:
    def setup_method(self):
        """Reset singleton before each test."""
        ModelRegistry.reset()

    def test_registry_initializes(self):
        registry = ModelRegistry()
        assert registry is not None
        assert registry._initialized is True

    def test_singleton_pattern(self):
        r1 = ModelRegistry()
        r2 = ModelRegistry()
        assert r1 is r2

    def test_fallback_returns_heuristic_when_no_model(self):
        registry = ModelRegistry()
        # nonexistent module should trigger fallback
        result = registry.fallback_to_heuristic("nonexistent_module", 75.0)
        assert result == 0.75

    def test_fallback_clamps_to_0_1(self):
        registry = ModelRegistry()
        assert registry.fallback_to_heuristic("x", 150) == 1.0
        assert registry.fallback_to_heuristic("x", -50) == 0.0

    def test_is_available_false_for_missing(self):
        registry = ModelRegistry()
        assert registry.is_available("nonexistent") is False

    def test_feature_importances_empty_for_missing(self):
        registry = ModelRegistry()
        assert registry.get_feature_importances("nonexistent") == []

    def test_get_metrics_empty_for_missing(self):
        registry = ModelRegistry()
        assert registry.get_metrics("nonexistent") == {}
