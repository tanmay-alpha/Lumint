import logging
import os
import uuid
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks, Depends, Request
from typing import Optional
from app.rate_limit import limiter
from app.dependencies.auth import get_current_user
from app.schemas.document import DocumentAnalysisResponse
from app.services.docshield.analyzer import analyze_pdf_document, analyze_image_document
from app.services.fraud_dna.fingerprinter import generate_fingerprint
from app.services.fraud_dna.store import save_fingerprint
from app.core.event_publisher import publish_threat_event
from app.core.file_validation import InvalidFileError, validate_upload
from ml.drift.registry import DriftRegistry

logger = logging.getLogger("lumint.routers.documents")

router = APIRouter(prefix="/api/documents", tags=["documents"], dependencies=[Depends(get_current_user)])

# Stable path: backend/uploads/ always, regardless of working directory
_BACKEND_DIR = Path(__file__).resolve().parents[2]
UPLOADS_DIR = _BACKEND_DIR / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}
# Per-endpoint cap is 12 MB; the global BodySizeLimitMiddleware is set to
# 20 MB. Keeping a deliberate ~8 MB buffer between the two means oversized
# uploads are rejected with our specific "File exceeds maximum allowed size
# of 12 MB" 413 instead of the middleware's generic body-too-large error,
# so the client can show a meaningful message ("file too large, try a
# smaller PDF") rather than a vague transport-level failure.
MAX_UPLOAD_BYTES = 12 * 1024 * 1024  # 12 MB


def _safe_unlink(path: Path) -> None:
    """Remove a file if it exists. Errors are logged and swallowed —
    upload cleanup must never crash the request that triggered it.

    The upload is already persisted to the Fraud DNA store before this
    runs, so deleting the on-disk blob doesn't lose evidence.
    """
    try:
        if path.exists():
            os.remove(path)
    except Exception:
        # Don't escalate — the file may already be gone, or the disk
        # may be read-only in some test environments. Either way, the
        # user-visible response is unaffected.
        logger.debug("Could not remove upload %s", path, exc_info=True)


def _sanitize_filename_for_response(raw: str) -> str:
    """Strip control characters and NUL bytes from a user-supplied filename
    before echoing it back in a JSON response.

    ``UploadFile.filename`` is browser-controlled. Even after the
    path-traversal guard, the name may still contain CR/LF (response
    splitting in downstream log lines), NUL bytes (which truncate
    filenames in some log aggregators), or other ASCII control chars.
    Replacing with ``_`` keeps the name readable but neutralises the
    smuggling vectors.
    """
    if not raw:
        return ""
    out = []
    for ch in raw:
        cp = ord(ch)
        if cp == 0 or cp < 0x20 or cp == 0x7f:
            out.append("_")
        else:
            out.append(ch)
    return "".join(out)


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

    # Stream-read the upload in fixed-size chunks and abort as soon as the
    # running total exceeds the cap. The old code did a single
    # ``await file.read()`` which would happily buffer a 100GB body
    # before the size check ran — a trivial memory-exhaustion DoS. The
    # outer BodySizeLimitMiddleware (20MB) provides a defense-in-depth
    # net, but checking per-chunk stops us from buffering more than
    # CHUNK_SIZE + a single chunk of overflow.
    CHUNK_SIZE = 64 * 1024
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await file.read(CHUNK_SIZE)
        if not chunk:
            break
        total += len(chunk)
        if total > MAX_UPLOAD_BYTES:
            max_mb = MAX_UPLOAD_BYTES // (1024 * 1024)
            raise HTTPException(
                status_code=413,
                detail="File exceeds maximum allowed size of " + str(max_mb) + " MB.",
            )
        chunks.append(chunk)
    contents = b"".join(chunks)

    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

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
        # Sanitize control characters (NUL, CR, LF, etc.) before echoing
        # the filename back. The browser-controlled name could otherwise
        # smuggle newlines into downstream logs (response splitting) or
        # truncate the name in tools that treat NUL as a terminator.
        "original_filename": _sanitize_filename_for_response(file.filename),
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
            ml_score = round(prob * 100)

            # Use the rule-based score as a FLOOR — if our heuristics
            # already flagged the document as risky (e.g. a phishing
            # screenshot whose OCR triggered the suspicious_keywords
            # rule), don't let the ML model down-rank it back to CLEAN
            # just because its training set didn't cover that variant.
            # We add the two scores and clamp to 100; this way a strong
            # signal from either side still surfaces, and a strong
            # signal from both compounds.
            rule_score = int(result.get("risk_score") or 0)
            risk_score = min(100, rule_score + ml_score)

            risk_level = "CLEAN"
            if 31 <= risk_score <= 60:
                risk_level = "SUSPICIOUS"
            elif risk_score >= 61:
                risk_level = "HIGH"

            result["risk_score"] = risk_score
            result["risk_level"] = risk_level
            result["ml_score"] = ml_score
            result["rule_score"] = rule_score

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
        y_pred = 1 if response_obj.risk_score >= 50 else 0
        DriftRegistry.update_all("doc", ground_truth, y_pred)

    try:
        drift_signal = DriftRegistry.get("doc").get_current_signal()
    except Exception:
        drift_signal = {"status": "stable"}

    # Best-effort cleanup of the saved upload *after* the response has been
    # built. The file is no longer needed: we've already extracted features,
    # generated a fingerprint, and the response only references metadata.
    # We schedule this as a background task so a slow filesystem doesn't
    # add latency to the user-facing request. The handler is a no-op if
    # the file has already been removed (e.g. by a periodic janitor).
    background_tasks.add_task(_safe_unlink, save_path)

    background_tasks.add_task(
        publish_threat_event,
        module="doc",
        detection_result=response_obj.model_dump(),
        ai_result=None,
        drift_signal=drift_signal
    )

    return response_obj
