import logging

from fastapi import APIRouter, HTTPException, Depends
from app.dependencies.auth import get_current_user
from app.schemas.fusion import FusionRequest, FusionResponse
from app.core.fusion import compute_lumint_score

logger = logging.getLogger("lumint.routers.fusion")
router = APIRouter(prefix="/api/fusion", tags=["fusion"], dependencies=[Depends(get_current_user)])

@router.post("/score", response_model=FusionResponse)
def get_fusion_score(body: FusionRequest):
    """
    Computes a unified, cross-modal fraud risk score by combining results
    from DocShield, PhishShield, and UPI Shield.
    """
    try:
        score_details = compute_lumint_score(
            doc_result=body.document_result,
            phish_result=body.phishing_result,
            upi_result=body.upi_result,
            weights=body.weights,
            use_ml=True
        )
        if body.ground_truth is not None:
            from ml.drift.registry import DriftRegistry
            y_pred = 1 if score_details.unified_score >= 50 else 0
            DriftRegistry.update_all("fusion", body.ground_truth, y_pred)
        return score_details
    except Exception:
        logger.exception("Cross-modal score fusion calculation failed")
        raise HTTPException(
            status_code=500,
            detail="Cross-modal score fusion calculation failed."
        )
