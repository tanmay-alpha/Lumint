import logging

from pathlib import Path
from typing import List

from app.services.docshield.metadata_analyzer import run_metadata_analysis
from app.services.docshield.text_extractor import extract_text
from app.services.docshield.layout_checker import check_layout
from app.services.docshield.ela_forensics import run_ela
from app.services.docshield.risk_scorer import calculate_risk
logger = logging.getLogger("lumint.services.docshield.analyzer")


_IMAGE_TEXT = {
    "extracted_text": "", "text_preview": "", "has_suspicious_keywords": False,
    "suspicious_keywords_found": [], "keyword_score": 0,
    "text_warnings": ["OCR for images is not implemented yet. Text analysis skipped."],
}
_IMAGE_LAYOUT = {
    "font_families": [], "font_count": 0, "font_sizes": [], "font_size_count": 0,
    "page_layouts": [], "layout_warnings": ["Layout analysis is not applicable for raw images."],
    "layout_score": 0,
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


def analyze_image_document(file_path: Path, file_size: int) -> dict:
    warnings: List[str] = []
    meta_result = _run_safe(run_metadata_analysis, file_path, warnings=warnings, label="Metadata analysis")
    metadata = meta_result["metadata"] if meta_result else None
    metadata_indicators = meta_result["indicators"] if meta_result else []

    ela_result = _run_safe(run_ela, file_path, warnings=warnings, label="ELA analysis")
    scoring = calculate_risk(metadata_indicators, _IMAGE_TEXT, _IMAGE_LAYOUT, ela_result)
    return _build_result(metadata, _IMAGE_TEXT, _IMAGE_LAYOUT, ela_result, scoring, warnings, "Image analyzed successfully (Metadata + ELA)")
