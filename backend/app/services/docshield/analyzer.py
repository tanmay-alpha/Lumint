import logging

from pathlib import Path
from typing import List, Optional

from app.services.docshield.metadata_analyzer import run_metadata_analysis
from app.services.docshield.text_extractor import extract_text, find_suspicious_keywords, keyword_score
from app.services.docshield.layout_checker import check_layout
from app.services.docshield.ela_forensics import run_ela
from app.services.docshield.risk_scorer import calculate_risk
logger = logging.getLogger("lumint.services.docshield.analyzer")


def _empty_image_text(extra_warnings: Optional[List[str]] = None) -> dict:
    """Default text-analysis result for an image with no client-side OCR.

    The frontend runs Tesseract.js in the browser and posts the extracted
    text back as a `text` form field; if that field is missing or empty
    (very small images, OCR failure, JS error), we still get here — the
    explicit warning tells the user why their screenshot came back CLEAN
    even though it visually contained text.
    """
    warnings = [
        "OCR was not performed on this image. Text-based risk rules "
        "(suspicious keywords, UPI/VPA detection) cannot fire.",
    ]
    if extra_warnings:
        warnings.extend(extra_warnings)
    return {
        "extracted_text": "",
        "text_preview": "",
        "has_suspicious_keywords": False,
        "suspicious_keywords_found": [],
        "keyword_score": 0,
        "text_warnings": warnings,
    }


_IMAGE_LAYOUT = {
    "font_families": [], "font_count": 0, "font_sizes": [], "font_size_count": 0,
    "page_layouts": [], "layout_warnings": ["Layout analysis is not applicable for raw images."],
    "layout_score": 0,
}


def text_from_client_ocr(client_ocr_text: Optional[str], extra_warnings: Optional[List[str]] = None) -> dict:
    """Build a text_analysis dict from text the client OCRed in the browser.

    This is the path used for image uploads: the backend has no Tesseract
    binary available, so we trust the client to supply the text. We still
    run the suspicious-keyword scanner on it.
    """
    text = (client_ocr_text or "").strip()
    if not text:
        return _empty_image_text(extra_warnings)
    matches = find_suspicious_keywords(text)
    preview = text[:1500]
    return {
        "extracted_text": text,
        "text_preview": preview,
        "has_suspicious_keywords": bool(matches),
        "suspicious_keywords_found": matches,
        "keyword_score": keyword_score(matches),
        "text_warnings": [
            "Text was extracted client-side (Tesseract.js). Server-side OCR "
            "is not available; trust the client result for keyword analysis.",
        ],
    }


def _build_result(metadata, text_result, layout_result, ela_result, scoring, warnings, message) -> dict:
    return {
        "analysis_status": "completed",
        "risk_score": scoring["risk_score"],
        "risk_level": scoring["risk_level"],
        "metadata": metadata,
        "text_analysis": text_result,
        "layout_analysis": layout_result,
        "ela_analysis": ela_result,
        "indicators": scoring["indicators"],
        "explanation": scoring["explanation"],
        "analysis_warnings": warnings or None,
        "message": message,
    }


def _run_safe(fn, *args, warnings: List[str], label: str):
    try:
        return fn(*args)
    except Exception:
        logger.exception("%s failed during document analysis", label)
        warnings.append(f"{label} failed.")
        return None


def analyze_pdf_document(file_path: Path, file_size: int) -> dict:
    warnings: List[str] = []
    meta_result = _run_safe(run_metadata_analysis, file_path, warnings=warnings, label="Metadata analysis")
    metadata = meta_result["metadata"] if meta_result else None
    metadata_indicators = meta_result["indicators"] if meta_result else []

    text_result = _run_safe(extract_text, file_path, warnings=warnings, label="Text extraction")
    if text_result and text_result.get("text_preview"):
        text_result["text_preview"] = text_result["text_preview"][:1500]

    layout_result = _run_safe(check_layout, file_path, warnings=warnings, label="Layout analysis")
    ela_result = _run_safe(run_ela, file_path, warnings=warnings, label="ELA analysis")

    scoring = calculate_risk(metadata_indicators, text_result, layout_result, ela_result)
    return _build_result(metadata, text_result, layout_result, ela_result, scoring, warnings, "Document analyzed successfully")


def analyze_image_document(file_path: Path, file_size: int, client_ocr_text: Optional[str] = None) -> dict:
    """Analyze an image upload.

    `client_ocr_text` is the text the frontend extracted with Tesseract.js
    in the user's browser. It's the only way we can get OCR for images
    without bundling a Tesseract binary in the backend container. The
    analyzer still runs the rest of the pipeline (metadata + ELA) and the
    keyword scorer flags suspicious vocabulary in the OCR'd text.
    """
    warnings: List[str] = []
    meta_result = _run_safe(run_metadata_analysis, file_path, warnings=warnings, label="Metadata analysis")
    metadata = meta_result["metadata"] if meta_result else None
    metadata_indicators = meta_result["indicators"] if meta_result else []

    ela_result = _run_safe(run_ela, file_path, warnings=warnings, label="ELA analysis")
    text_result = text_from_client_ocr(client_ocr_text, extra_warnings=warnings)
    scoring = calculate_risk(metadata_indicators, text_result, _IMAGE_LAYOUT, ela_result)
    return _build_result(
        metadata,
        text_result,
        _IMAGE_LAYOUT,
        ela_result,
        scoring,
        warnings,
        "Image analyzed successfully (Metadata + ELA + client OCR)",
    )
