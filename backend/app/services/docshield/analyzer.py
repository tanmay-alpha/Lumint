from pathlib import Path

from app.services.docshield.metadata_analyzer import run_metadata_analysis
from app.services.docshield.text_extractor import extract_text
from app.services.docshield.layout_checker import check_layout
from app.services.docshield.ela_forensics import run_ela
from app.services.docshield.risk_scorer import calculate_risk


def analyze_pdf_document(file_path: Path, file_size: int) -> dict:
    # Metadata
    try:
        metadata_result = run_metadata_analysis(file_path)
        metadata = metadata_result["metadata"]
        metadata_indicators = metadata_result["indicators"]
    except Exception as e:
        metadata = None
        metadata_indicators = []

    # Text extraction
    try:
        text_result = extract_text(file_path)
    except Exception:
        text_result = None

    # Layout analysis
    try:
        layout_result = check_layout(file_path)
    except Exception:
        layout_result = None

    # ELA forensics
    try:
        ela_result = run_ela(file_path)
    except Exception:
        ela_result = None

    # Combined risk scoring
    scoring = calculate_risk(
        metadata_indicators=metadata_indicators,
        text_analysis=text_result,
        layout_analysis=layout_result,
        ela_analysis=ela_result,
    )

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
        "message": "Document analyzed successfully",
    }