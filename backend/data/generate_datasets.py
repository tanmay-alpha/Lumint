"""
Synthetic Dataset Generator for Lumint ML Layer.

Generates reproducible synthetic datasets for training ML models when
real-world data (e.g., PhishTank CSV) is not available.
All random generation uses numpy random_state=42 for full determinism.

NOTE: Synthetic dataset for reproducibility. Replace with real
PhishTank CSV / real UPI datasets for publication results.
"""

import os
import sys
import string
from pathlib import Path

import numpy as np
import pandas as pd

# Ensure backend is importable
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

DATA_DIR = Path(__file__).resolve().parent


# ── URL Dataset ────────────────────────────────────────────────────

COMMON_TLDS = [".com", ".org", ".net", ".co", ".io", ".in", ".edu"]
SUSPICIOUS_TLDS = [".tk", ".ml", ".ga", ".cf", ".gq", ".xyz", ".click", ".top"]
LEGIT_DOMAINS = [
    "google", "microsoft", "apple", "amazon", "github",
    "stackoverflow", "wikipedia", "linkedin", "twitter", "reddit",
    "facebook", "instagram", "youtube", "netflix", "spotify",
    "medium", "quora", "dropbox", "slack", "zoom",
]
BRAND_WORDS = [
    "paypal", "secure", "login", "verify", "bank", "update",
    "account", "free", "prize", "confirm", "support", "service",
]
PATH_WORDS = [
    "index", "page", "auth", "signin", "dashboard", "profile",
    "settings", "api", "v1", "checkout", "verify", "reset",
]


def _random_string(rng: np.random.RandomState, min_len: int = 3, max_len: int = 12) -> str:
    """Generate a random lowercase alphanumeric string."""
    length = rng.randint(min_len, max_len + 1)
    chars = list(string.ascii_lowercase + string.digits)
    return "".join(rng.choice(chars) for _ in range(length))


def _generate_legit_url(rng: np.random.RandomState) -> str:
    """Generate a realistic-looking legitimate URL."""
    domain = rng.choice(LEGIT_DOMAINS)
    tld = rng.choice(COMMON_TLDS)

    # Occasional subdomain
    subdomain = ""
    if rng.random() < 0.3:
        subdomain = rng.choice(["www", "app", "mail", "docs", "api"]) + "."

    # Path
    path_depth = rng.randint(0, 4)
    path_parts = [rng.choice(PATH_WORDS) for _ in range(path_depth)]
    path = "/".join(path_parts)

    # Occasional query params
    query = ""
    if rng.random() < 0.2:
        query = f"?id={rng.randint(1, 10000)}"

    url = f"https://{subdomain}{domain}{tld}/{path}{query}"
    return url


def _generate_phish_url(rng: np.random.RandomState) -> str:
    """Generate a phishing-looking URL with suspicious patterns."""
    strategy = rng.choice(["ip_based", "typosquat", "suspicious_tld", "long_random", "brand_stuff"])

    if strategy == "ip_based":
        ip = f"{rng.randint(1,255)}.{rng.randint(0,255)}.{rng.randint(0,255)}.{rng.randint(0,255)}"
        path = "/".join([rng.choice(BRAND_WORDS) for _ in range(rng.randint(2, 5))])
        scheme = rng.choice(["http", "https"])
        return f"{scheme}://{ip}/{path}"

    elif strategy == "typosquat":
        base = rng.choice(LEGIT_DOMAINS)
        # Insert typo
        mutations = [
            lambda s: s + _random_string(rng, 1, 3),
            lambda s: s[:len(s)//2] + "-" + s[len(s)//2:],
            lambda s: s.replace("o", "0") if "o" in s else s + "s",
            lambda s: s + "-login",
        ]
        mutated = rng.choice(mutations)(base)
        tld = rng.choice(SUSPICIOUS_TLDS)
        path = "/".join([rng.choice(BRAND_WORDS) for _ in range(rng.randint(1, 4))])
        return f"http://{mutated}{tld}/{path}"

    elif strategy == "suspicious_tld":
        domain = _random_string(rng, 5, 15)
        tld = rng.choice(SUSPICIOUS_TLDS)
        brand = rng.choice(BRAND_WORDS)
        return f"http://{brand}-{domain}{tld}/login/verify"

    elif strategy == "long_random":
        parts = [_random_string(rng, 4, 10) for _ in range(rng.randint(3, 6))]
        domain = ".".join(parts) + rng.choice(SUSPICIOUS_TLDS)
        path = "/".join([_random_string(rng, 5, 15) for _ in range(rng.randint(3, 8))])
        return f"http://{domain}/{path}"

    else:  # brand_stuff
        brand = rng.choice(["paypal", "google", "amazon", "apple", "microsoft"])
        filler = _random_string(rng, 3, 8)
        tld = rng.choice(SUSPICIOUS_TLDS + COMMON_TLDS[:2])
        path = f"login/verify/update/{_random_string(rng, 8, 20)}"
        return f"http://{brand}-{filler}{tld}/{path}"


def generate_phishing_dataset(n_legit: int = 3000, n_phish: int = 1500, seed: int = 42) -> pd.DataFrame:
    """
    Generate synthetic phishing URL dataset.
    Columns: url, label (0=legit, 1=phish)

    NOTE: Synthetic dataset for reproducibility.
    Replace with PhishTank CSV for publication.
    """
    rng = np.random.RandomState(seed)

    urls = []
    labels = []

    for _ in range(n_legit):
        urls.append(_generate_legit_url(rng))
        labels.append(0)

    for _ in range(n_phish):
        urls.append(_generate_phish_url(rng))
        labels.append(1)

    df = pd.DataFrame({"url": urls, "label": labels})

    # Shuffle deterministically
    df = df.sample(frac=1, random_state=seed).reset_index(drop=True)

    return df


# ── Document Dataset ───────────────────────────────────────────────

def generate_doc_dataset(n_genuine: int = 2000, n_fraud: int = 1000, seed: int = 42) -> pd.DataFrame:
    """
    Generate synthetic document forensics dataset.
    Columns: 13 feature columns + label (0=genuine, 1=fraud).

    Fraudulent documents have statistically different feature distributions
    to ensure models can learn meaningful decision boundaries.
    """
    from ml.features.doc_features import DOC_FEATURE_NAMES

    rng = np.random.RandomState(seed)
    rows = []

    for _ in range(n_genuine):
        row = {
            "ela_mean": rng.uniform(10, 60),
            "ela_std": rng.uniform(5, 25),
            "ela_max": rng.uniform(50, 150),
            "ela_high_pixel_ratio": rng.uniform(0.0, 0.15),
            "metadata_anomaly_score": rng.choice([0, 0, 0, 1], p=[0.5, 0.2, 0.2, 0.1]),
            "file_size_kb": rng.uniform(50, 5000),
            "page_count": rng.randint(1, 30),
            "font_count": rng.randint(1, 10),
            "image_count": rng.randint(0, 15),
            "creation_to_mod_delta_days": rng.uniform(0, 365),
            "has_javascript": 0.0,
            "has_encryption": float(rng.random() < 0.1),
            "text_extraction_failed": 0.0,
            "label": 0,
        }
        rows.append(row)

    for _ in range(n_fraud):
        row = {
            "ela_mean": rng.uniform(80, 220),       # Higher ELA in forgeries
            "ela_std": rng.uniform(30, 80),          # More variance
            "ela_max": rng.uniform(180, 255),        # Higher max
            "ela_high_pixel_ratio": rng.uniform(0.2, 0.85),  # Many hot pixels
            "metadata_anomaly_score": rng.choice([2, 3, 4, 5], p=[0.3, 0.3, 0.25, 0.15]),
            "file_size_kb": rng.uniform(10, 800),    # Smaller (re-saved)
            "page_count": rng.randint(1, 5),
            "font_count": rng.randint(0, 3),
            "image_count": rng.randint(0, 5),
            "creation_to_mod_delta_days": rng.choice([-1, 0, 1, 2], p=[0.4, 0.3, 0.2, 0.1]),
            "has_javascript": float(rng.random() < 0.3),
            "has_encryption": float(rng.random() < 0.05),
            "text_extraction_failed": float(rng.random() < 0.25),
            "label": 1,
        }
        rows.append(row)

    df = pd.DataFrame(rows)
    df = df.sample(frac=1, random_state=seed).reset_index(drop=True)

    return df


# ── UPI Dataset ────────────────────────────────────────────────────

def generate_upi_dataset(n_genuine: int = 1500, n_fake: int = 750, seed: int = 42) -> pd.DataFrame:
    """
    Generate synthetic UPI receipt forensics dataset.
    Columns: 8 feature columns + label (0=genuine, 1=fake).

    Fake receipts have statistically different feature distributions
    to ensure models can learn meaningful decision boundaries.
    """
    from ml.features.upi_features import UPI_FEATURE_NAMES

    rng = np.random.RandomState(seed)
    rows = []

    for _ in range(n_genuine):
        row = {
            "forgery_score_heuristic": rng.uniform(0.0, 0.25),
            "utr_valid": 1.0,
            "utr_length": 12.0,
            "ela_tamper_regions": rng.uniform(0.0, 0.1),
            "font_consistent": 1.0,
            "color_authentic": 1.0,
            "ocr_confidence": rng.uniform(0.7, 1.0),
            "app_detected_encoded": float(rng.choice([0, 1, 2])),
            "label": 0,
        }
        rows.append(row)

    for _ in range(n_fake):
        row = {
            "forgery_score_heuristic": rng.uniform(0.4, 1.0),   # Higher forgery
            "utr_valid": float(rng.random() < 0.3),              # Usually invalid
            "utr_length": float(rng.choice([0, 8, 10, 11, 12], p=[0.3, 0.2, 0.2, 0.15, 0.15])),
            "ela_tamper_regions": rng.uniform(0.15, 0.8),        # Tampered
            "font_consistent": float(rng.random() < 0.3),        # Usually inconsistent
            "color_authentic": float(rng.random() < 0.25),       # Usually wrong colors
            "ocr_confidence": rng.uniform(0.2, 0.65),            # Lower OCR
            "app_detected_encoded": float(rng.choice([0, 1, 2, 3], p=[0.15, 0.15, 0.1, 0.6])),
            "label": 1,
        }
        rows.append(row)

    df = pd.DataFrame(rows)
    df = df.sample(frac=1, random_state=seed).reset_index(drop=True)

    return df


# ── CLI Entry Point ────────────────────────────────────────────────

if __name__ == "__main__":
    print("Generating synthetic datasets...")
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Phishing URL dataset
    phish_df = generate_phishing_dataset()
    phish_path = DATA_DIR / "phishing_dataset.csv"
    phish_df.to_csv(phish_path, index=False)
    print(f"  Phishing: {len(phish_df)} rows -> {phish_path}")
    print(f"    Class distribution: {dict(phish_df['label'].value_counts())}")

    # Document forensics dataset
    doc_df = generate_doc_dataset()
    doc_path = DATA_DIR / "doc_dataset.csv"
    doc_df.to_csv(doc_path, index=False)
    print(f"  Document: {len(doc_df)} rows -> {doc_path}")
    print(f"    Class distribution: {dict(doc_df['label'].value_counts())}")

    # UPI receipts dataset
    upi_df = generate_upi_dataset()
    upi_path = DATA_DIR / "upi_dataset.csv"
    upi_df.to_csv(upi_path, index=False)
    print(f"  UPI:      {len(upi_df)} rows -> {upi_path}")
    print(f"    Class distribution: {dict(upi_df['label'].value_counts())}")

    print("\nAll datasets generated successfully.")
