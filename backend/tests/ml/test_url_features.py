"""
Tests for URL feature extraction — R9 ML Baseline.
All deterministic, no network calls, random_state=42.
"""

import sys
from pathlib import Path
import numpy as np
import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from ml.features.url_features import (
    extract_lexical_features,
    extract_full_features,
    fit_tfidf,
    get_tfidf_features,
    get_feature_names,
)


class TestLexicalFeatures:
    def test_feature_length_is_25(self):
        features = extract_lexical_features("https://example.com/login")
        assert features.shape == (25,)

    def test_no_nan_or_inf(self):
        urls = [
            "https://example.com",
            "http://192.168.1.1/phish/login",
            "",
            "https://secure-paypal-login.tk/verify/account?id=123&ref=456",
            "ftp://weird-protocol.net",
        ]
        for url in urls:
            features = extract_lexical_features(url)
            assert not np.any(np.isnan(features)), f"NaN in features for: {url}"
            assert not np.any(np.isinf(features)), f"Inf in features for: {url}"

    def test_ip_url_gets_has_ip_flag(self):
        features = extract_lexical_features("http://192.168.1.1/login")
        assert features[8] == 1.0, "has_ip_address should be 1 for IP-based URL"

    def test_non_ip_url_has_no_ip_flag(self):
        features = extract_lexical_features("https://google.com")
        assert features[8] == 0.0, "has_ip_address should be 0 for domain-based URL"

    def test_brand_url_triggers_brand_keyword(self):
        features = extract_lexical_features("http://paypal-secure.tk/login")
        assert features[22] == 1.0, "contains_brand_keyword should be 1"

    def test_no_brand_in_normal_url(self):
        features = extract_lexical_features("https://example.com")
        assert features[22] == 0.0, "contains_brand_keyword should be 0"

    def test_free_keyword_detection(self):
        features = extract_lexical_features("http://free-prize.tk/win")
        assert features[23] == 1.0, "contains_free_keyword should be 1"

    def test_suspicious_tld(self):
        features = extract_lexical_features("http://scam.tk/phish")
        assert features[11] == 1.0, "tld_suspicious should be 1 for .tk"

    def test_https_flag(self):
        features_https = extract_lexical_features("https://example.com")
        features_http = extract_lexical_features("http://example.com")
        assert features_https[12] == 1.0
        assert features_http[12] == 0.0

    def test_empty_url(self):
        features = extract_lexical_features("")
        assert features.shape == (25,)
        assert np.all(features == 0.0)


class TestFullFeatures:
    def test_feature_length_is_2025_without_tfidf(self):
        features = extract_full_features("https://example.com")
        assert features.shape == (2025,)

    def test_feature_length_is_2025_with_tfidf(self):
        urls = ["https://example.com", "http://evil.tk/login", "https://bank.org"]
        vectorizer = fit_tfidf(urls)
        features = extract_full_features("https://example.com", vectorizer)
        assert features.shape == (2025,)

    def test_no_nan_in_full(self):
        features = extract_full_features("http://192.168.1.1/paypal/login?q=1&x=2")
        assert not np.any(np.isnan(features))
        assert not np.any(np.isinf(features))

    def test_feature_names_length(self):
        names = get_feature_names()
        assert len(names) == 2025
