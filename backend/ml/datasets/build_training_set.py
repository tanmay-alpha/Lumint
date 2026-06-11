"""
Walk through a directory of UPI screenshots, extract features, save to CSV.

Usage:
    python -m ml.datasets.build_training_set \
        --real-dir dataset/images/train \
        --forged-dir dataset/images/train \
        --output ml/data/upi_v2_training.csv

The CSV is compatible with `ml.train_upi_v2`. The last column is the
binary label (0=real/genuine, 1=forged).
"""
import argparse
import csv
import json
import logging
import sys
from pathlib import Path
from typing import List, Optional

import numpy as np

# Allow running as script from backend dir
BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from ml.features.upi_features_v2 import UPIFeatureExtractorV2  # noqa: E402

logger = logging.getLogger("lumint.ml.datasets.build_training_set")


def _iter_images(root: Path):
    """Yield image paths in sorted order, filtering for common UPI image types."""
    if not root.exists():
        logger.warning("Directory does not exist: %s", root)
        return
    for ext in ("*.png", "*.jpg", "*.jpeg", "*.webp"):
        for p in sorted(root.glob(ext)):
            yield p


def build_csv(
    real_dir: Path,
    forged_dir: Path,
    output_csv: Path,
    max_per_class: Optional[int] = None,
) -> dict:
    """Extract features for all images, write CSV."""
    extractor = UPIFeatureExtractorV2()
    n_features = len(extractor.FEATURE_NAMES)
    rows: List[list] = []
    failures: dict = {"real": [], "forged": []}

    # Real (label 0)
    real_paths = list(_iter_images(real_dir))
    if max_per_class:
        real_paths = real_paths[:max_per_class]
    logger.info("Extracting real features from %d images in %s", len(real_paths), real_dir)
    for i, img in enumerate(real_paths):
        if i % 50 == 0:
            logger.info("  real %d/%d", i, len(real_paths))
        try:
            features = extractor.extract(str(img))
            if not np.any(features):
                failures["real"].append(str(img))
                continue
            rows.append([float(v) for v in features] + [0])
        except Exception as e:
            logger.warning("Failed to extract features from %s: %s", img, e)
            failures["real"].append(str(img))

    # Forged (label 1)
    forged_paths = list(_iter_images(forged_dir))
    if max_per_class:
        forged_paths = forged_paths[:max_per_class]
    logger.info("Extracting forged features from %d images in %s", len(forged_paths), forged_dir)
    for i, img in enumerate(forged_paths):
        if i % 50 == 0:
            logger.info("  forged %d/%d", i, len(forged_paths))
        try:
            features = extractor.extract(str(img))
            if not np.any(features):
                failures["forged"].append(str(img))
                continue
            rows.append([float(v) for v in features] + [1])
        except Exception as e:
            logger.warning("Failed to extract features from %s: %s", img, e)
            failures["forged"].append(str(img))

    # Write CSV
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(output_csv, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(extractor.FEATURE_NAMES + ["label"])
        writer.writerows(rows)

    n_real = sum(1 for r in rows if r[-1] == 0)
    n_forged = sum(1 for r in rows if r[-1] == 1)
    summary = {
        "output_csv": str(output_csv),
        "n_features": n_features,
        "n_real": n_real,
        "n_forged": n_forged,
        "n_total": len(rows),
        "n_failures": {
            "real": len(failures["real"]),
            "forged": len(failures["forged"]),
        },
        "failure_paths": failures,
    }
    logger.info(
        "Wrote %d rows to %s (real=%d, forged=%d, features=%d)",
        len(rows), output_csv, n_real, n_forged, n_features
    )
    return summary


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    parser = argparse.ArgumentParser(description="Build UPI training CSV from image directories")
    parser.add_argument(
        "--real-dir", required=True, help="Directory of real/genuine UPI screenshots"
    )
    parser.add_argument(
        "--forged-dir", required=True, help="Directory of forged UPI screenshots"
    )
    parser.add_argument(
        "--output", default="ml/data/upi_v2_training.csv", help="Output CSV path"
    )
    parser.add_argument(
        "--max-per-class",
        type=int,
        default=None,
        help="Cap on images per class (useful for quick iteration)",
    )
    parser.add_argument(
        "--summary",
        default=None,
        help="Optional JSON summary file path",
    )
    args = parser.parse_args()

    real_dir = Path(args.real_dir)
    forged_dir = Path(args.forged_dir)
    output_csv = Path(args.output)

    summary = build_csv(real_dir, forged_dir, output_csv, max_per_class=args.max_per_class)

    if args.summary:
        with open(args.summary, "w") as f:
            json.dump(summary, f, indent=2)
        logger.info("Wrote summary to %s", args.summary)

    print(json.dumps({k: v for k, v in summary.items() if k != "failure_paths"}, indent=2))


if __name__ == "__main__":
    main()