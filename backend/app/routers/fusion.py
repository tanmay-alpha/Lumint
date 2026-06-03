from fastapi import APIRouter, HTTPException
from app.schemas.fusion import FusionRequest, FusionResponse
from app.core.fusion import compute_lumint_score

router = APIRouter(prefix="/api/fusion", tags=["fusion"])

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
        return score_details
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Cross-modal score fusion calculation failed: {str(e)}"
        )
