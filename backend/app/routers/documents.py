import uuid
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.schemas.document import DocumentAnalysisResponse
from app.services.docshield.analyzer import analyze_pdf_document
from app.services.fraud_dna.fingerprinter import generate_fingerprint
from app.services.fraud_dna.store import save_fingerprint

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
            detail=f"File type '{suffix}' not allowed. Accepted: {sorted(ALLOWED_EXTENSIONS)}",
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
            message="Image uploaded successfully. OCR and ELA for images coming later.",
        )

    try:
        result = analyze_pdf_document(save_path, len(contents))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    # Generate + store Fraud DNA fingerprint silently
    try:
        fingerprint = generate_fingerprint(
            doc_id=doc_id,
            file_path=save_path,
            original_filename=file.filename,
            saved_filename=saved_filename,
            analysis_result=result,
        )
        save_fingerprint(fingerprint)
    except Exception:
        pass  # Never break DocShield response for DNA errors

    return DocumentAnalysisResponse(**base, **result)

