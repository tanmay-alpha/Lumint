import uuid
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.schemas.document import DocumentAnalysisResponse
from app.services.docshield.metadata_analyzer import run_metadata_analysis
from app.services.docshield.text_extractor import extract_text
from app.services.docshield.layout_checker import check_layout
from app.services.docshield.risk_scorer import calculate_risk

router = APIRouter(prefix="/api/documents", tags=["documents"])

UPLOADS_DIR = Path("uploads")
UPLOADS_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}


@router.post("/analyze", response_model=DocumentAnalysisResponse)
async def analyze_document(file: UploadFile = File(...)):
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="No file provided.")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{suffix}' not allowed. Use: {ALLOWED_EXTENSIONS}",
        )

    contents = await file.read()
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    doc_id = str(uuid.uuid4())
    saved_filename = f"{doc_id}{suffix}"
    save_path = UPLOADS_DIR / saved_filename
    save_path.write_bytes(contents)

    base = {
        "doc_id": doc_id,
        "original_filename": file.filename,
        "saved_filename": saved_filename,
        "file_path": str(save_path),
        "file_size": len(contents),
        "content_type": file.content_type or "unknown",
    }

    if suffix != ".pdf":
        return DocumentAnalysisResponse(
            **base,
            analysis_status="image_analysis_not_implemented_yet",
            message="Image uploaded. OCR + ELA analysis coming in next milestone.",
        )

    # PDF full analysis
    try:
        metadata_result = run_metadata_analysis(save_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Metadata analysis failed: {str(e)}")

    try:
        text_result = extract_text(save_path)
    except Exception as e:
        text_result = None

    try:
        layout_result = check_layout(save_path)
    except Exception as e:
        layout_result = None

    scoring = calculate_risk(
        metadata_indicators=metadata_result["indicators"],
        text_analysis=text_result,
        layout_analysis=layout_result,
    )

    return DocumentAnalysisResponse(
        **base,
        analysis_status="completed",
        risk_score=scoring["risk_score"],
        risk_level=scoring["risk_level"],
        metadata=metadata_result["metadata"],
        text_analysis=text_result,
        layout_analysis=layout_result,
        indicators=scoring["indicators"],
        explanation=scoring["explanation"],
    )