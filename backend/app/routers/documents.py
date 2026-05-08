import uuid
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.schemas.document import DocumentAnalysisResponse
from app.services.docshield.metadata_analyzer import run_metadata_analysis
from app.services.docshield.risk_scorer import calculate_risk

router = APIRouter(prefix="/api/documents", tags=["documents"])

UPLOADS_DIR = Path("uploads")
UPLOADS_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpg",
    "image/jpeg",
}


@router.post("/analyze", response_model=DocumentAnalysisResponse)
async def analyze_document(file: UploadFile = File(...)):
    # Validate file provided
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="No file provided.")

    # Validate extension
    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{suffix}' not allowed. Use: {ALLOWED_EXTENSIONS}",
        )

    # Read file bytes
    contents = await file.read()
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # Save with UUID filename
    doc_id = str(uuid.uuid4())
    saved_filename = f"{doc_id}{suffix}"
    save_path = UPLOADS_DIR / saved_filename

    save_path.write_bytes(contents)

    # Base response
    base = {
        "doc_id": doc_id,
        "original_filename": file.filename,
        "saved_filename": saved_filename,
        "file_path": str(save_path),
        "file_size": len(contents),
        "content_type": file.content_type or "unknown",
    }

    # PDF analysis
    if suffix == ".pdf":
        try:
            analysis = run_metadata_analysis(save_path)
            scoring = calculate_risk(analysis["indicators"])
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"PDF analysis failed: {str(e)}",
            )

        return DocumentAnalysisResponse(
            **base,
            analysis_status="completed",
            risk_score=scoring["risk_score"],
            risk_level=scoring["risk_level"],
            metadata=analysis["metadata"],
            indicators=analysis["indicators"],
            explanation=scoring["explanation"],
        )

    # Image — upload OK, analysis pending
    return DocumentAnalysisResponse(
        **base,
        analysis_status="image_analysis_not_implemented_yet",
        message="Image uploaded successfully. OCR and ELA analysis coming in next milestone.",
    )