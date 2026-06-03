import uuid
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.schemas.document import DocumentAnalysisResponse
from app.services.docshield.analyzer import analyze_pdf_document, analyze_image_document
from app.services.fraud_dna.fingerprinter import generate_fingerprint
from app.services.fraud_dna.store import save_fingerprint, STORE_PATH

router = APIRouter(prefix="/api/documents", tags=["documents"])

# Stable path: backend/uploads/ always, regardless of working directory
_BACKEND_DIR = Path(__file__).resolve().parents[2]
UPLOADS_DIR = _BACKEND_DIR / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}
MAX_UPLOAD_BYTES = 15 * 1024 * 1024  # 15 MB

MAGIC_BYTES = {
    ".pdf":  b"%PDF",
    ".png":  b"\x89PNG",
    ".jpg":  b"\xff\xd8\xff",
    ".jpeg": b"\xff\xd8\xff",
}


def _validate_magic(contents: bytes, suffix: str) -> bool:
    magic = MAGIC_BYTES.get(suffix)
    if not magic:
        return True
    return contents[: len(magic)] == magic


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

    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds maximum allowed size of 15 MB.")

    if not _validate_magic(contents, suffix):
        raise HTTPException(
            status_code=400,
            detail=f"File content does not match expected type '{suffix}'. Possible spoofed extension.",
        )

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
        try:
            result = analyze_image_document(save_path, len(contents))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Image analysis failed: {str(e)}")
    else:
        try:
            result = analyze_pdf_document(save_path, len(contents))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    # Compute Feature Contributions for research (XAI)
    try:
        from app.core.xai import get_feature_contributions
        result["feature_contributions"] = get_feature_contributions(indicators=result.get("indicators"))
    except Exception as e:
        result["feature_contributions"] = []

    # Store Fraud DNA fingerprint silently
    try:
        fingerprint = generate_fingerprint(
            doc_id=doc_id,
            file_path=save_path,
            original_filename=file.filename,
            saved_filename=saved_filename,
            analysis_result=result,
        )
        save_fingerprint(fingerprint)
    except Exception as e:
        # Surface as warning, never crash upload
        if result.get("analysis_warnings") is None:
            result["analysis_warnings"] = []
        result["analysis_warnings"].append(f"Fraud DNA fingerprint storage failed: {str(e)}")

    return DocumentAnalysisResponse(**base, **result)