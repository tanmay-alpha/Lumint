import uuid
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.phishshield.url_analyzer import analyze_url
from app.services.phishshield.risk_scorer import score_url
from app.services.fraud_dna.store import save_fingerprint
from app.schemas.phishing import PhishingCheckResponse

router = APIRouter(prefix="/api/phishing", tags=["phishing"])


class PhishingCheckRequest(BaseModel):
    url: str


class BatchCheckRequest(BaseModel):
    urls: List[str]


def _analyze_single(raw: str) -> PhishingCheckResponse:
    raw = (raw or "").strip()
    if not raw:
        raise HTTPException(status_code=400, detail="URL must not be empty.")
    analysis = analyze_url(raw)
    scoring = score_url(analysis["triggered_rules"])

    fingerprint = None
    if scoring["risk_score"] >= 31:
        fingerprint = {
            "event_id": str(uuid.uuid4()),
            "doc_id": None,
            "source_type": "URL",
            "original_filename": None,
            "saved_filename": None,
            "file_hash": None,
            "metadata_hash": None,
            "editor_tool": None,
            "producer": None,
            "creator": None,
            "source_domain": analysis["domain"],
            "top_keywords": analysis["top_keywords"],
            "risk_indicators": [r["rule"] for r in analysis["triggered_rules"]],
            "risk_score": scoring["risk_score"],
            "risk_level": scoring["risk_level"],
            "document_type_hint": "phishing_url",
            "fingerprint_text": " ".join(
                [analysis["domain"]] + analysis["top_keywords"] + [r["rule"] for r in analysis["triggered_rules"]]
            ),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        try:
            save_fingerprint(fingerprint)
        except Exception:
            pass

    # Calculate feature contributions for research (XAI)
    try:
        from app.core.xai import get_feature_contributions
        feature_contributions = get_feature_contributions(indicators=analysis["triggered_rules"])
    except Exception:
        feature_contributions = []

    return PhishingCheckResponse(
        url=raw,
        normalized_url=analysis["normalized_url"],
        domain=analysis["domain"],
        risk_score=scoring["risk_score"],
        risk_level=scoring["risk_level"],
        triggered_rules=analysis["triggered_rules"],
        domain_similarity_matches=analysis["domain_similarity_matches"],
        phishing_fingerprint=fingerprint,
        feature_contributions=feature_contributions,
        message="URL analyzed successfully",
    )



@router.post("/check", response_model=PhishingCheckResponse)
def check_url(body: PhishingCheckRequest):
    return _analyze_single(body.url)


@router.post("/check/batch")
def check_url_batch(body: BatchCheckRequest):
    """AI feature: analyze up to 20 URLs in a single request for bulk threat screening."""
    if not body.urls:
        raise HTTPException(status_code=400, detail="urls list must not be empty.")
    if len(body.urls) > 20:
        raise HTTPException(status_code=400, detail="Maximum 20 URLs per batch request.")
    results = []
    for url in body.urls:
        try:
            results.append(_analyze_single(url).model_dump())
        except HTTPException as e:
            results.append({"url": url, "error": e.detail})
    return {"total": len(results), "results": results}


@router.get("/confidence/{risk_score}")
def explain_confidence(risk_score: int):
    """AI feature: translate a numeric risk score into a human-readable confidence explanation."""
    if not 0 <= risk_score <= 100:
        raise HTTPException(status_code=400, detail="risk_score must be between 0 and 100.")
    if risk_score <= 30:
        label, confidence, explanation = "CLEAN", "HIGH", "URL shows no significant phishing signals. Safe to proceed with normal caution."
    elif risk_score <= 60:
        label, confidence, explanation = "SUSPICIOUS", "MEDIUM", "URL has moderate risk signals. Verify the domain independently before entering credentials."
    else:
        label, confidence, explanation = "HIGH", "HIGH", "URL shows strong phishing indicators. Do not interact with this URL. Report it immediately."
    return {
        "risk_score": risk_score,
        "risk_level": label,
        "model_confidence": confidence,
        "explanation": explanation,
        "recommendation": "Block" if risk_score > 60 else ("Review" if risk_score > 30 else "Allow"),
    }