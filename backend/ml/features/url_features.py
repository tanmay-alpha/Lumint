"""
URL Feature Extractor for Lumint PhishShield ML Layer.

Extracts exactly 25 lexical/structural features from a URL string,
plus optional TF-IDF character n-gram features (2000 dims).
Full feature vector = concat(lexical_25, tfidf_2000) = 2025 dims.

All outputs are numeric numpy arrays with no NaN or Inf values.
"""

import math
import re
from urllib.parse import urlparse
from typing import List, Optional

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

# ── Constants ──────────────────────────────────────────────────────

SUSPICIOUS_TLDS = {".tk", ".ml", ".ga", ".cf", ".gq"}

BRAND_KEYWORDS = [
    "paypal", "google", "amazon", "apple", "microsoft",
    "facebook", "instagram", "bank", "secure", "login", "verify",
]

FREE_KEYWORDS = ["free", "win", "prize", "bonus", "gift", "lucky"]

CONSONANTS = set("bcdfghjklmnpqrstvwxyz")

SPECIAL_CHARS = set("%=&+@#")

LEXICAL_FEATURE_NAMES = [
    "url_length",
    "num_dots",
    "num_hyphens",
    "num_underscores",
    "num_slashes",
    "num_at_signs",
    "num_digits",
    "digit_ratio",
    "has_ip_address",
    "subdomain_depth",
    "path_depth",
    "tld_suspicious",
    "has_https",
    "domain_length",
    "path_length",
    "query_length",
    "num_params",
    "has_port",
    "url_entropy",
    "char_ratio_upper",
    "num_special_chars",
    "hostname_digit_ratio",
    "contains_brand_keyword",
    "contains_free_keyword",
    "longest_consecutive_consonants",
]


def _shannon_entropy(s: str) -> float:
    """Compute Shannon entropy of a string."""
    if not s:
        return 0.0
    freq = {}
    for c in s:
        freq[c] = freq.get(c, 0) + 1
    length = len(s)
    entropy = 0.0
    for count in freq.values():
        p = count / length
        if p > 0:
            entropy -= p * math.log2(p)
    return entropy


def _is_ip_address(hostname: str) -> bool:
    """Check if hostname is an IP address (v4 or v6)."""
    # IPv4 pattern
    ipv4 = re.match(
        r"^(\d{1,3}\.){3}\d{1,3}$", hostname
    )
    if ipv4:
        return True
    # IPv6 pattern (simplified)
    if ":" in hostname and all(
        c in "0123456789abcdefABCDEF:" for c in hostname
    ):
        return True
    return False


def _longest_consecutive_consonants(s: str) -> int:
    """Find length of the longest run of consecutive consonants."""
    s_lower = s.lower()
    max_run = 0
    current_run = 0
    for c in s_lower:
        if c in CONSONANTS:
            current_run += 1
            max_run = max(max_run, current_run)
        else:
            current_run = 0
    return max_run


def extract_lexical_features(url: str) -> np.ndarray:
    """
    Extract exactly 25 lexical/structural features from a URL string.
    Returns numpy array of shape (25,), all numeric, no NaN.
    """
    url = (url or "").strip()
    if not url:
        return np.zeros(25, dtype=np.float64)

    # Ensure scheme present for urlparse
    url_for_parse = url
    if not url_for_parse.startswith(("http://", "https://")):
        url_for_parse = "http://" + url_for_parse

    parsed = urlparse(url_for_parse)
    hostname = (parsed.hostname or "").lower()
    path = parsed.path or ""
    query = parsed.query or ""
    url_lower = url.lower()
    total_chars = max(len(url), 1)

    features = np.zeros(25, dtype=np.float64)

    # 0: url_length
    features[0] = len(url)

    # 1: num_dots
    features[1] = url.count(".")

    # 2: num_hyphens
    features[2] = url.count("-")

    # 3: num_underscores
    features[3] = url.count("_")

    # 4: num_slashes
    features[4] = url.count("/")

    # 5: num_at_signs
    features[5] = url.count("@")

    # 6: num_digits
    digit_count = sum(1 for c in url if c.isdigit())
    features[6] = digit_count

    # 7: digit_ratio
    features[7] = digit_count / total_chars

    # 8: has_ip_address
    features[8] = 1.0 if _is_ip_address(hostname) else 0.0

    # 9: subdomain_depth (count of dots in hostname)
    features[9] = hostname.count(".")

    # 10: path_depth (count of slashes in path, excluding leading)
    features[10] = max(0, path.count("/") - 1)

    # 11: tld_suspicious
    tld = ""
    if "." in hostname:
        tld = "." + hostname.rsplit(".", 1)[-1]
    features[11] = 1.0 if tld in SUSPICIOUS_TLDS else 0.0

    # 12: has_https
    features[12] = 1.0 if url_lower.startswith("https") else 0.0

    # 13: domain_length
    features[13] = len(hostname)

    # 14: path_length
    features[14] = len(path)

    # 15: query_length
    features[15] = len(query)

    # 16: num_params (count of & in query + 1 if query exists, else 0)
    features[16] = query.count("&") if query else 0

    # 17: has_port
    features[17] = 1.0 if parsed.port is not None else 0.0

    # 18: url_entropy
    features[18] = _shannon_entropy(url)

    # 19: char_ratio_upper
    upper_count = sum(1 for c in url if c.isupper())
    features[19] = upper_count / total_chars

    # 20: num_special_chars
    features[20] = sum(1 for c in url if c in SPECIAL_CHARS)

    # 21: hostname_digit_ratio
    hostname_len = max(len(hostname), 1)
    hostname_digits = sum(1 for c in hostname if c.isdigit())
    features[21] = hostname_digits / hostname_len

    # 22: contains_brand_keyword
    features[22] = 1.0 if any(kw in url_lower for kw in BRAND_KEYWORDS) else 0.0

    # 23: contains_free_keyword
    features[23] = 1.0 if any(kw in url_lower for kw in FREE_KEYWORDS) else 0.0

    # 24: longest_consecutive_consonants
    features[24] = _longest_consecutive_consonants(url)

    # Safety: replace any NaN/Inf with 0
    features = np.nan_to_num(features, nan=0.0, posinf=0.0, neginf=0.0)

    return features


def fit_tfidf(urls: List[str], random_state: int = 42) -> TfidfVectorizer:
    """
    Fit a TF-IDF vectorizer on a list of URL strings.
    Uses character n-grams (2-4) with max 2000 features.
    """
    vectorizer = TfidfVectorizer(
        analyzer="char_wb",
        ngram_range=(2, 4),
        max_features=2000,
        sublinear_tf=True,
    )
    vectorizer.fit(urls)
    return vectorizer


def get_tfidf_features(url: str, vectorizer: Optional[TfidfVectorizer]) -> np.ndarray:
    """
    Transform a single URL into TF-IDF feature vector.
    Returns array of shape (2000,) — zero-padded if vectorizer is None.
    """
    if vectorizer is None:
        return np.zeros(2000, dtype=np.float64)

    tfidf_matrix = vectorizer.transform([url])
    vec = tfidf_matrix.toarray().flatten()

    # Ensure exactly 2000 dims
    if len(vec) < 2000:
        vec = np.pad(vec, (0, 2000 - len(vec)), constant_values=0.0)
    elif len(vec) > 2000:
        vec = vec[:2000]

    return vec.astype(np.float64)


def extract_full_features(
    url: str, vectorizer: Optional[TfidfVectorizer] = None
) -> np.ndarray:
    """
    Extract full feature vector: 25 lexical + 2000 TF-IDF = 2025 dims.
    """
    lexical = extract_lexical_features(url)
    tfidf = get_tfidf_features(url, vectorizer)
    full = np.concatenate([lexical, tfidf])
    return np.nan_to_num(full, nan=0.0, posinf=0.0, neginf=0.0)


def get_feature_names(vectorizer: Optional[TfidfVectorizer] = None) -> List[str]:
    """Return ordered feature name list for the full 2025-dim vector."""
    names = list(LEXICAL_FEATURE_NAMES)
    if vectorizer is not None:
        names.extend(
            [f"tfidf_{name}" for name in vectorizer.get_feature_names_out()]
        )
    else:
        names.extend([f"tfidf_{i}" for i in range(2000)])
    return names
