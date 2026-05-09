import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.phishshield.url_analyzer import analyze_url
from app.services.phishshield.risk_scorer import score_url
from app.services.fraud_dna.store import save_fingerprint
from app.schemas.phishing import PhishingCheckResponse

router = APIRouter(prefix="/api/phishing", tags=["phishing"])


class PhishingCheckRequest(BaseModel):
    url: str


@router.post("/check", response_model=PhishingCheckResponse)
def check_url(body: PhishingCheckRequest):
    raw = (body.url or "").strip()
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
                [analysis["domain"]]
                + analysis["top_keywords"]
                + [r["rule"] for r in analysis["triggered_rules"]]
            ),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        try:
            save_fingerprint(fingerprint)
        except Exception:
            pass

    return PhishingCheckResponse(
        url=raw,
        normalized_url=analysis["normalized_url"],
        domain=analysis["domain"],
        risk_score=scoring["risk_score"],
        risk_level=scoring["risk_level"],
        triggered_rules=analysis["triggered_rules"],
        domain_similarity_matches=analysis["domain_similarity_matches"],
        phishing_fingerprint=fingerprint,
        message="URL analyzed successfully",
    )