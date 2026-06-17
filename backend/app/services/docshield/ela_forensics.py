import logging

from io import BytesIO
from pathlib import Path
from typing import List

import fitz
import numpy as np
from PIL import Image
logger = logging.getLogger("lumint.services.docshield.ela_forensics")


MAX_PAGES = 3
RENDER_DPI = 72
JPEG_QUALITY = 90
HOTSPOT_HIGH = 0.15
HOTSPOT_LOW = 0.08
MEAN_DIFF_SUSPICIOUS = 8.0
HOTSPOT_PX_THRESHOLD = 25

_ELA_BASE = {
    "enabled": True,
    "method": "jpeg_recompression_difference",
}


def _ela_diff(img: Image.Image) -> dict:
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=JPEG_QUALITY)
    buf.seek(0)
    recomp = Image.open(buf).convert("RGB")
    diff = np.abs(np.array(img, dtype=np.float32) - np.array(recomp, dtype=np.float32))
    hotspot_mask = np.any(diff > HOTSPOT_PX_THRESHOLD, axis=2)
    return {
        "mean_difference": round(float(np.mean(diff)), 4),
        "max_difference": int(np.max(diff)),
        "hotspot_ratio": round(float(np.sum(hotspot_mask) / hotspot_mask.size), 4),
    }


def _classify(stats: dict, page_num: int) -> dict:
    h, m = stats["hotspot_ratio"], stats["mean_difference"]
    if h > HOTSPOT_HIGH or m > MEAN_DIFF_SUSPICIOUS:
        suspicious, reason = True, f"High recompression inconsistency (hotspot_ratio={h}, mean_diff={m})."
    elif h > HOTSPOT_LOW:
        suspicious, reason = True, f"Minor recompression inconsistency (hotspot_ratio={h})."
    else:
        suspicious, reason = False, "No significant recompression inconsistency detected."
    return {"page_number": page_num, **stats, "suspicious": suspicious, "reason": reason}


def _ela_score_from_results(results: List[dict]) -> int:
    score = 0
    for r in results:
        if not r.get("suspicious"):
            continue
        h = r.get("hotspot_ratio") or 0
        if h > HOTSPOT_HIGH:
            score = max(score, 30)
        elif h > HOTSPOT_LOW:
            score = max(score, 10)
    return score


def _build_response(results: List[dict], warnings: List[str], pages_analyzed: int) -> dict:
    suspicious_pages = [r["page_number"] for r in results if r.get("suspicious")]
    return {
        **_ELA_BASE,
        "pages_analyzed": pages_analyzed,
        "ela_score": _ela_score_from_results(results),
        "suspicious_pages": suspicious_pages,
        "page_results": results,
        "warnings": warnings,
    }


def run_ela(file_path: Path) -> dict:
    """Run ELA on images directly; render PDF pages for PDFs."""
    suffix = file_path.suffix.lower()

    if suffix in (".png", ".jpg", ".jpeg"):
        try:
            result = _classify(_ela_diff(Image.open(file_path).convert("RGB")), 1)
            return _build_response([result], [], 1)
        except Exception:
            logger.exception("Could not open image for ELA")
            return {**_ELA_BASE, "pages_analyzed": 0, "ela_score": 0,
                    "suspicious_pages": [], "page_results": [],
                    "warnings": ["Could not open image for ELA."]}

    warnings: List[str] = []
    results: List[dict] = []

    try:
        doc = fitz.open(str(file_path))
    except Exception:
        logger.exception("Could not open PDF for ELA")
        return {**_ELA_BASE, "pages_analyzed": 0, "ela_score": 0,
                "suspicious_pages": [], "page_results": [],
                "warnings": ["Could not open PDF for ELA."]}

    pages_to_analyze = min(doc.page_count, MAX_PAGES)
    for i in range(pages_to_analyze):
        try:
            mat = fitz.Matrix(RENDER_DPI / 72, RENDER_DPI / 72)
            pix = doc[i].get_pixmap(matrix=mat, colorspace=fitz.csRGB)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            results.append(_classify(_ela_diff(img), i + 1))
        except Exception:
            logger.exception("Page %d ELA failed", i + 1)
            warnings.append(f"Page {i + 1} ELA failed.")
            results.append({"page_number": i + 1, "mean_difference": None, "max_difference": None,
                             "hotspot_ratio": None, "suspicious": False,
                             "reason": "ELA could not be completed."})
    doc.close()
    return _build_response(results, warnings, pages_to_analyze)
