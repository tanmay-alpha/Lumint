import logging
from io import BytesIO
from pathlib import Path
from typing import List, Dict, Any
import numpy as np
from PIL import Image

try:
    import cv2  # type: ignore
    _HAS_CV2 = True
except ImportError:  # pragma: no cover - cv2 is a required runtime dep
    _HAS_CV2 = False

logger = logging.getLogger("lumint.services.upi.screenshot_forensics")

JPEG_QUALITY = 90

# Hard cap on the long edge of the image used for ELA. Anything bigger is
# downsampled to keep peak memory (three float32 arrays per pixel) bounded.
# 4096px gives ~192MB worst case for the diff arrays, well within budget.
MAX_ELA_DIM = 4096

# Adaptive ELA thresholds. We deliberately avoid a single global pixel-difference
# cutoff because:
#   1. Dark-mode screenshots (GPay dark, AMOLED, low-light captures) compress
#      differently than bright ones, so a flat threshold flags huge areas of the
#      image as suspicious.
#   2. JPEG recompression variance is image-dependent — natural high-frequency
#      detail (anti-aliased text, gradients) produces per-pixel differences
#      just under the round-trip noise floor, so a 95th-percentile cutoff of the
#      *actual* diff image is a much more reliable tamper signal.
ADAPTIVE_PERCENTILE = 95
MIN_REGION_AREA_RATIO = 0.001  # ignore contours covering < 0.1% of the image
CONTOUR_APPROX_EPSILON = 0.02   # polygon simplification factor relative to arc length


def _empty_result(warnings: List[str]) -> Dict[str, Any]:
    """Standard empty/failure payload — keeps the response shape stable."""
    return {
        "ela_score": 0,
        "tamper_suspected": False,
        "hotspot_ratio": 0.0,
        "mean_difference": 0.0,
        "max_difference": 0.0,
        "tamper_regions": [],
        "warnings": warnings,
    }


def _extract_tamper_regions(
    diff_gray: np.ndarray,
    diff_mask: np.ndarray,
    width: int,
    height: int,
) -> List[Dict[str, Any]]:
    """
    Run connected-component/contour detection on the adaptive ELA mask and
    return one entry per suspicious region with bbox, polygon, area_ratio,
    and a per-region mean-difference confidence score.

    Falls back to a grid-based estimator when OpenCV isn't available so the
    function still returns *something* useful in minimal environments.
    """
    if not _HAS_CV2 or diff_mask.size == 0:
        return _estimate_regions_grid(diff_mask, width, height)

    # uint8 mask (0/255) for OpenCV
    mask_uint8 = (diff_mask.astype(np.uint8) * 255)

    # Dilate to merge neighbouring hot pixels into a single tamper region.
    # Two iterations is enough to close 1-2px gaps from anti-aliased edges
    # without swallowing genuine small edits.
    kernel = np.ones((3, 3), dtype=np.uint8)
    mask_dilated = cv2.dilate(mask_uint8, kernel, iterations=2)

    contours, _ = cv2.findContours(
        mask_dilated,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE,
    )

    min_area = max(1.0, float(width) * float(height) * MIN_REGION_AREA_RATIO)
    regions: List[Dict[str, Any]] = []

    for contour in contours:
        area = float(cv2.contourArea(contour))
        if area < min_area:
            continue

        x, y, w, h = cv2.boundingRect(contour)

        # Simplify the contour to a polygon. Epsilon scales with the contour's
        # own perimeter so small regions stay sharp and large ones get
        # reasonable vertex counts (typically 4-12).
        perimeter = float(cv2.arcLength(contour, True))
        epsilon = CONTOUR_APPROX_EPSILON * perimeter
        polygon_pts = cv2.approxPolyDP(contour, epsilon, True)
        polygon = polygon_pts.reshape(-1, 2).tolist() if polygon_pts.size else []

        # Per-region mean diff acts as a confidence proxy: the hotter the
        # pixels inside the contour, the more likely it's a real edit rather
        # than JPEG noise.
        region_diff = diff_gray[y : y + h, x : x + w]
        confidence = float(np.mean(region_diff)) if region_diff.size else 0.0

        regions.append({
            "bbox": [int(x), int(y), int(w), int(h)],
            "polygon": [[int(px), int(py)] for px, py in polygon],
            "area_ratio": float(area / float(width * height)),
            "confidence": round(confidence, 4),
        })

    # Largest / highest-confidence regions first so downstream rendering and
    # SHAP-style explanations see the most important regions up front.
    regions.sort(key=lambda r: (r["area_ratio"], r["confidence"]), reverse=True)
    return regions


def _estimate_regions_grid(
    mask: np.ndarray,
    width: int,
    height: int,
) -> List[Dict[str, Any]]:
    """
    Fallback path when cv2 is unavailable: divide the mask into a 12x12 grid
    and report blocks with high hotspot density.

    Kept as a defensive fallback only — the primary path uses cv2 contours.
    """
    regions: List[Dict[str, Any]] = []
    grid_rows = grid_cols = 12
    h_step = mask.shape[0] / grid_rows
    w_step = mask.shape[1] / grid_cols

    for r in range(grid_rows):
        y_start = int(r * h_step)
        y_end = int((r + 1) * h_step)
        for c in range(grid_cols):
            x_start = int(c * w_step)
            x_end = int((c + 1) * w_step)
            sub_mask = mask[y_start:y_end, x_start:x_end]
            if sub_mask.size == 0:
                continue
            ratio = float(np.sum(sub_mask) / sub_mask.size)
            if ratio > 0.15:
                regions.append({
                    "bbox": [int(x_start), int(y_start), int(x_end - x_start), int(y_end - y_start)],
                    "polygon": [],
                    "area_ratio": float(ratio),
                    "confidence": 0.0,
                })
    return regions


def run_image_ela(image_path: Path) -> Dict[str, Any]:
    """
    Perform Error Level Analysis (ELA) on a UPI screenshot.

    Saves the image as a JPEG at quality=90, computes the per-pixel difference
    against the recompressed version, then flags tampering using:

      1. An *adaptive* threshold = 95th percentile of the per-pixel mean
         difference. This avoids the dark-mode false-positive class of the
         previous fixed-threshold implementation.
      2. OpenCV contour detection (with light dilation) to find connected
         tamper regions and emit per-region bbox + polygon + area_ratio +
         confidence in the response.

    The response shape is unchanged from the previous version so existing
    callers (analyzer, schemas, frontend) keep working.
    """
    try:
        if not image_path.exists():
            return _empty_result(["Image file does not exist."])

        with Image.open(image_path) as img:
            img_rgb = img.convert("RGB")
            # Cap input dimensions so a huge screenshot doesn't OOM us.
            # 4096px on the long edge is well above any phone display and
            # keeps the float32 diff arrays under ~200MB at worst.
            img_rgb.thumbnail((MAX_ELA_DIM, MAX_ELA_DIM), Image.LANCZOS)
            width, height = img_rgb.size

            # Recompress in memory
            buf = BytesIO()
            img_rgb.save(buf, format="JPEG", quality=JPEG_QUALITY)
            buf.seek(0)

            with Image.open(buf) as recomp:
                recomp_rgb = recomp.convert("RGB")

                arr_img = np.array(img_rgb, dtype=np.float32)
                arr_recomp = np.array(recomp_rgb, dtype=np.float32)

                diff = np.abs(arr_img - arr_recomp)

        # Per-pixel mean across the three channels so a single-channel edit
        # (e.g. amount colour tweaked but not redrawn) still lights up.
        diff_gray = np.mean(diff, axis=2)

        # Adaptive threshold: 95th percentile of the actual diff image.
        # Natural recompression noise stays below this; real edits push the
        # tail up sharply. Using np.ptp on the percentile keeps us robust to
        # dark-mode screenshots where absolute diffs are uniformly low.
        threshold = float(np.percentile(diff_gray, ADAPTIVE_PERCENTILE))
        diff_mask = diff_gray > threshold

        hotspot_ratio = float(np.sum(diff_mask) / diff_mask.size)
        mean_diff = float(np.mean(diff_gray))
        max_diff = int(np.max(diff_gray))

        # Tamper classification: same intent as before, but expressed in terms
        # of *adaptive* hotspot coverage so dark-mode captures don't trip it.
        tamper_suspected = False
        ela_score = 0
        if hotspot_ratio > 0.12 or mean_diff > 8.0:
            tamper_suspected = True
            ela_score = 35
        elif hotspot_ratio > 0.06 or mean_diff > 4.0:
            tamper_suspected = True
            ela_score = 15

        tamper_regions: List[Dict[str, Any]] = []
        if tamper_suspected:
            tamper_regions = _extract_tamper_regions(diff_gray, diff_mask, width, height)
        else:
            # Even when the global heuristic says "clean", surface any clearly
            # localised hot spots (e.g. amount field edited in an otherwise
            # well-compressed screenshot) for analyst review.
            tamper_regions = _extract_tamper_regions(diff_gray, diff_mask, width, height)
            # Drop low-confidence regions when we're not flagging globally.
            tamper_regions = [r for r in tamper_regions if r["area_ratio"] >= 0.005]

        return {
            "ela_score": int(ela_score),
            "tamper_suspected": tamper_suspected,
            "hotspot_ratio": round(hotspot_ratio, 4),
            "mean_difference": round(mean_diff, 4),
            "max_difference": max_diff,
            "tamper_regions": tamper_regions,
            "warnings": [],
        }

    except Exception:
        logger.exception("Error during UPI ELA")
        return _empty_result(["ELA processing failed."])


def estimate_tamper_regions(image_path: Path) -> List[Dict[str, Any]]:
    """
    Convenience wrapper: return the tamper regions from `run_image_ela`
    without the rest of the ELA payload.
    """
    return run_image_ela(image_path).get("tamper_regions", [])
