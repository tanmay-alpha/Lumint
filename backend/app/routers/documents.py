import logging
import uuid
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks, Depends, Request
from typing import Optional
from app.rate_limit import limiter
from app.dependencies.auth import get_current_user
from app.schemas.document import DocumentAnalysisResponse
from app.services.docshield.analyzer import analyze_pdf_document, analyze_image_document
from app.services.fraud_dna.fingerprinter import generate_fingerprint
from app.services.fraud_dna.store import save_fingerprint, STORE_PATH
from app.core.event_publisher import publish_threat_event
from app.core.file_validation import InvalidFileError, validate_upload

logger = logging.getLogger("lumint.routers.documents")

router = APIRouter(prefix="/api/documents", tags=["documents"], dependencies=[Depends(get_current_user)])

# Stable path: backend/uploads/ always, regardless of working directory
_BACKEND_DIR = Path(__file__).resolve().parents[2]
UPLOADS_DIR = _BACKEND_DIR / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}
MAX_UPLOAD_BYTES = 15 * 1024 * 1024  # 15 MB


@router.post("/analyze", response_model=DocumentAnalysisResponse)
@limiter.limit("10/minute")
async def analyze_document(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    text: Optional[str] = Form(None),
    ground_truth: Optional[int] = None
):
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="No file provided.")

    # Reject path-traversal attempts in the filename *before* anything else.
    # Anything not a "bare" filename (no slashes, no ..) is suspicious.
    safe_name = Path(file.filename).name
    if safe_name != file.filename or ".." in file.filename or "/" in file.filename or "\\" in file.filename:
        raise HTTPException(status_code=400, detail="Invalid filename.")

    contents = await file.read()

    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds maximum allowed size of 15 MB.")

    # Multi-layer content validation (magic + structural + bomb guard).
    try:
        validate_upload(contents, safe_name)
    except InvalidFileError as e:
        # Surface the safe message; the original exception is already
        # logged inside validate_upload.
        raise HTTPException(status_code=400, detail=str(e)) from e

    doc_id = str(uuid.uuid4())
    suffix = Path(safe_name).suffix.lower()
    saved_filename = f"{doc_id}{suffix}"
    save_path = UPLOADS_DIR / saved_filename
    save_path.write_bytes(contents)

    base = {
        "doc_id": doc_id,
        "original_filename": file.filename,
        "saved_filename": saved_filename,
        "file_path": f"uploads/{saved_filename}",
        "file_size": len(contents),
        "content_type": file.content_type or "unknown",
    }

    from fastapi.concurrency import run_in_threadpool
    if suffix != ".pdf":
        try:
            result = await run_in_threadpool(analyze_image_document, save_path, len(contents), text)
        except Exception:
            logger.exception("Image analysis failed for document upload %s", doc_id)
            raise HTTPException(status_code=500, detail="Image analysis failed.")
    else:
        try:
            result = await run_in_threadpool(analyze_pdf_document, save_path, len(contents))
        except Exception:
            logger.exception("PDF analysis failed for document upload %s", doc_id)
            raise HTTPException(status_code=500, detail="Analysis failed.")

    # Try using trained ML model if available
    try:
        from ml.registry import get_registry
        from ml.features.doc_features import extract_doc_features, get_feature_names

        registry = get_registry()
        if registry.is_available("doc"):
            feats = extract_doc_features(result)
            prob = registry.predict_proba("doc", feats)
            risk_score = round(prob * 100)

            risk_level = "CLEAN"
            if 31 <= risk_score <= 60:
                risk_level = "SUSPICIOUS"
            elif risk_score >= 61:
                risk_level = "HIGH"

            result["risk_score"] = risk_score
            result["risk_level"] = risk_level

            # Use SHAP explanation for XAI contributions
            from app.core.xai import get_feature_contributions
            model_obj = registry._models["doc"]
            feature_names = get_feature_names()
            result["feature_contributions"] = get_feature_contributions(
                model=model_obj,
                features=feats,
                feature_names=feature_names
            )
        else:
            from app.core.xai import get_feature_contributions
            result["feature_contributions"] = get_feature_contributions(indicators=result.get("indicators"))
    except Exception as e:
        try:
            from app.core.xai import get_feature_contributions
            result["feature_contributions"] = get_feature_contributions(indicators=result.get("indicators"))
        except Exception:
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
    except Exception:
        # Surface as warning, never crash upload. Keep implementation
        # details and filesystem paths in the server logs only.
        logger.exception("Fraud DNA fingerprint storage failed for document upload %s", doc_id)
        if result.get("analysis_warnings") is None:
            result["analysis_warnings"] = []
        result["analysis_warnings"].append("Fraud DNA fingerprint storage failed.")

    response_obj = DocumentAnalysisResponse(**base, **result)
    if ground_truth is not None:
        from ml.drift.registry import DriftRegistry
        y_pred = 1 if response_obj.risk_score >= 50 else 0
        DriftRegistry.update_all("doc", ground_truth, y_pred)

    from ml.drift.registry import DriftRegistry
    try:
        drift_signal = DriftRegistry.get("doc").get_current_signal()
    except Exception:
        drift_signal = {"status": "stable"}

    background_tasks.add_task(
        publish_threat_event,
        module="doc",
        detection_result=response_obj.model_dump(),
        ai_result=None,
        drift_signal=drift_signal
    )

    return response_obj
