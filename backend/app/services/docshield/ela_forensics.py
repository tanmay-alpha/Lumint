from pathlib import Path
from typing import List
from io import BytesIO

import fitz
import numpy as np
from PIL import Image

MAX_PAGES = 3
RENDER_DPI = 72          # low DPI keeps it fast and memory-safe
JPEG_QUALITY = 90
HOTSPOT_THRESHOLD_HIGH = 0.15
HOTSPOT_THRESHOLD_LOW = 0.08
MEAN_DIFF_SUSPICIOUS = 8.0
HOTSPOT_PIXEL_THRESHOLD = 25  # per-channel diff considered "high error"


def _render_page_to_image(page: fitz.Page) -> Image.Image:
    mat = fitz.Matrix(RENDER_DPI / 72, RENDER_DPI / 72)
    pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    return img


def _ela_diff(original: Image.Image) -> dict:
    buffer = BytesIO()
    original.save(buffer, format="JPEG", quality=JPEG_QUALITY)
    buffer.seek(0)
    recompressed = Image.open(buffer).convert("RGB")

    orig_arr = np.array(original, dtype=np.float32)
    recomp_arr = np.array(recompressed, dtype=np.float32)

    diff = np.abs(orig_arr - recomp_arr)
    mean_diff = float(np.mean(diff))
    max_diff = int(np.max(diff))

    hotspot_mask = np.any(diff > HOTSPOT_PIXEL_THRESHOLD, axis=2)
    hotspot_ratio = float(np.sum(hotspot_mask) / hotspot_mask.size)

    return {
        "mean_difference": round(mean_diff, 4),
        "max_difference": max_diff,
        "hotspot_ratio": round(hotspot_ratio, 4),
    }


def _classify_page(stats: dict, page_number: int) -> dict:
    hotspot = stats["hotspot_ratio"]
    mean_diff = stats["mean_difference"]

    if hotspot > HOTSPOT_THRESHOLD_HIGH or mean_diff > MEAN_DIFF_SUSPICIOUS:
        suspicious = True
        reason = (
            f"High recompression inconsistency detected "
            f"(hotspot_ratio={hotspot}, mean_diff={mean_diff})."
        )
    elif hotspot > HOTSPOT_THRESHOLD_LOW:
        suspicious = True
        reason = (
            f"Minor recompression inconsistency detected "
            f"(hotspot_ratio={hotspot})."
        )
    else:
        suspicious = False
        reason = "No significant recompression inconsistency detected."

    return {
        "page_number": page_number,
        "mean_difference": stats["mean_difference"],
        "max_difference": stats["max_difference"],
        "hotspot_ratio": hotspot,
        "suspicious": suspicious,
        "reason": reason,
    }


def run_ela(file_path: Path) -> dict:
    warnings: List[str] = []
    page_results = []

    try:
        doc = fitz.open(str(file_path))
    except Exception as e:
        return {
            "enabled": True,
            "method": "jpeg_recompression_difference",
            "pages_analyzed": 0,
            "ela_score": 0,
            "suspicious_pages": [],
            "page_results": [],
            "warnings": [f"Could not open PDF for ELA: {str(e)}"],
        }

    pages_to_analyze = min(doc.page_count, MAX_PAGES)

    for i in range(pages_to_analyze):
        try:
            page = doc[i]
            img = _render_page_to_image(page)
            stats = _ela_diff(img)
            result = _classify_page(stats, page_number=i + 1)
            page_results.append(result)
        except Exception as e:
            warnings.append(f"Page {i + 1} ELA failed: {str(e)}")
            page_results.append({
                "page_number": i + 1,
                "mean_difference": None,
                "max_difference": None,
                "hotspot_ratio": None,
                "suspicious": False,
                "reason": f"ELA could not be completed for this page: {str(e)}",
            })

    doc.close()

    suspicious_pages = [r["page_number"] for r in page_results if r.get("suspicious")]

    ela_score = 0
    for r in page_results:
        if not r.get("suspicious"):
            continue
        hotspot = r.get("hotspot_ratio") or 0
        if hotspot > HOTSPOT_THRESHOLD_HIGH:
            ela_score = max(ela_score, 30)
        elif hotspot > HOTSPOT_THRESHOLD_LOW:
            ela_score = max(ela_score, 10)

    return {
        "enabled": True,
        "method": "jpeg_recompression_difference",
        "pages_analyzed": pages_to_analyze,
        "ela_score": ela_score,
        "suspicious_pages": suspicious_pages,
        "page_results": page_results,
        "warnings": warnings,
    }