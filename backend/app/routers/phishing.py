import uuid
import logging
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Request
from pydantic import BaseModel, Field, field_validator

from app.rate_limit import limiter, api_key_or_ip_key
from app.dependencies.auth import get_current_user
from app.services.phishshield.url_analyzer import analyze_url, analyze_url_async
from app.services.phishshield.risk_scorer import score_url
from app.services.fraud_dna.store import save_fingerprint
from app.schemas.phishing import PhishingCheckResponse
from app.core.event_publisher import publish_threat_event
from ml.drift.registry import DriftRegistry

logger = logging.getLogger("lumint.routers.phishing")
router = APIRouter(prefix="/api/phishing", tags=["phishing"], dependencies=[Depends(get_current_user)])


class PhishingCheckRequest(BaseModel):
    url: str = Field(..., min_length=1, max_length=2048, description="URL to check (max 2048 chars, RFC 3986)")
    ground_truth: Optional[int] = Field(default=None, ge=0, le=1, description="Optional ground truth label (0=clean, 1=phish)")


class BatchCheckRequest(BaseModel):
    urls: List[str] = Field(..., max_length=100, description="Maximum 100 URLs per batch")

    @field_validator("urls")
    @classmethod
    def validate_urls(cls, v: List[str]) -> List[str]:
        for url in v:
            if len(url) > 2048:
                raise ValueError(f"URL too long ({len(url)} chars, max 2048): {url[:50]}...")
        return v


def _build_response(raw: str, analysis: dict) -> PhishingCheckResponse:
    """Build PhishingCheckResponse + save fingerprint. Shared by sync+async paths.

    `score_source` is set to:
      - "ml"        when the trained phishing classifier was used
      - "heuristic" when the rule-based fallback scored the URL
    It is `None` only for very old client/server versions that predate the
    field; current clients should always see one of the two values.
    """
    # Try using trained ML model if available
    score_source: Optional[str] = None
    try:
        from ml.registry import get_registry
        from ml.features.url_features import extract_full_features, get_feature_names

        registry = get_registry()
        if registry.is_available("phish"):
            vectorizer = registry.get_tfidf("phish")
            feats = extract_full_features(raw, vectorizer)
            prob = registry.predict_proba("phish", feats)
            risk_score = round(prob * 100)

            risk_level = "CLEAN"
            if 31 <= risk_score <= 60:
                risk_level = "SUSPICIOUS"
            elif risk_score >= 61:
                risk_level = "HIGH"
            scoring = {"risk_score": risk_score, "risk_level": risk_level}
            score_source = "ml"

            # Use SHAP explanation for XAI contributions
            from app.core.xai import get_feature_contributions
            model_obj = registry._models["phish"]
            feature_names = get_feature_names(vectorizer)
            feature_contributions = get_feature_contributions(
                model=model_obj,
                features=feats,
                feature_names=feature_names
            )
        else:
            scoring = score_url(
                analysis["triggered_rules"],
                whois=analysis.get("whois"),
                ssl=analysis.get("ssl"),
            )
            score_source = "heuristic"
            from app.core.xai import get_feature_contributions
            feature_contributions = get_feature_contributions(indicators=analysis["triggered_rules"])
    except Exception:
        scoring = score_url(
            analysis["triggered_rules"],
            whois=analysis.get("whois"),
            ssl=analysis.get("ssl"),
        )
        score_source = "heuristic"
        try:
            from app.core.xai import get_feature_contributions
            feature_contributions = get_feature_contributions(indicators=analysis["triggered_rules"])
        except Exception:
            feature_contributions = []

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
            logger.info(f"Fingerprint saved for URL: {analysis['domain']}")
        except Exception as e:
            logger.error(
                f"Failed to save fingerprint for URL {analysis['domain']}: {e}",
                exc_info=True
            )

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
        whois=analysis.get("whois"),
        ssl=analysis.get("ssl"),
        score_source=score_source,
        message="URL analyzed successfully",
    )


def _analyze_single(raw: str) -> PhishingCheckResponse:
    """Sync path: rules only (no WHOIS/SSL). Used by batch endpoint."""
    raw = (raw or "").strip()
    if not raw:
        raise HTTPException(status_code=400, detail="URL must not be empty.")
    analysis = analyze_url(raw)
    return _build_response(raw, analysis)


async def _analyze_single_async(raw: str) -> PhishingCheckResponse:
    """Async path: rules + WHOIS + SSL in parallel."""
    raw = (raw or "").strip()
    if not raw:
        raise HTTPException(status_code=400, detail="URL must not be empty.")
    analysis = await analyze_url_async(raw)
    return _build_response(raw, analysis)



# Rate-limit partition: we explicitly pass key_func=api_key_or_ip_key
# on every @limiter.limit decorator below so two distinct X-Api-Key
# values (or bearer tokens) behind the same NAT don't share a single
# 30/minute budget. Without this, slowapi's default key_func partitions
# by remote address, which collapses all API keys behind one egress
# point into one bucket. The key_func falls back to IP only when no
# credential header is present (e.g. unauthenticated dev probes).


@router.post("/check", response_model=PhishingCheckResponse)
@limiter.limit("30/minute", key_func=api_key_or_ip_key)
async def check_url(request: Request, body: PhishingCheckRequest, background_tasks: BackgroundTasks):
    # Body-size sanity check. The BodySizeLimitMiddleware caps the raw
    # HTTP body at 20 MB, but for a single-URL request that's an
    # absurd ceiling — anything over ~4 KB is either a malformed
    # client or an attacker trying to spam the analyzer. We check the
    # URL length here so the response is a clean 413 with a useful
    # message instead of a generic "body too large" from middleware.
    if len(body.url) > 2048:
        raise HTTPException(
            status_code=413,
            detail=f"URL is {len(body.url)} chars; max is 2048.",
        )

    res = await _analyze_single_async(body.url)
    if body.ground_truth is not None:
        y_pred = 1 if res.risk_score >= 50 else 0
        DriftRegistry.update_all("phish", body.ground_truth, y_pred)

    # Single DriftRegistry lookup, reused below.
    try:
        drift_signal = DriftRegistry.get("phish").get_current_signal()
    except Exception:
        drift_signal = {"status": "stable"}

    background_tasks.add_task(
        publish_threat_event,
        module="phish",
        detection_result=res.model_dump(),
        ai_result=None,
        drift_signal=drift_signal
    )
    return res


# Cap the *aggregate* size of a /check/batch body. With the per-URL
# 2048-char cap, 100 URLs could legally total 200 KB; we leave a small
# margin for JSON framing and reject anything past that as a fast 413
# (the per-endpoint validator below this still caps at 100 entries).
MAX_BATCH_BODY_CHARS = 100 * 2048 + 4096  # ~205 KB ceiling


@router.post("/check/batch")
@limiter.limit("5/minute", key_func=api_key_or_ip_key)
def check_url_batch(request: Request, body: BatchCheckRequest):
    """AI feature: analyze up to 100 URLs in a single request for bulk threat screening.

    Rate-limited to 5/minute: each URL triggers a full SHAP explainability
    pass, so 100 URLs is ~100 model inferences + 100 SHAP runs. A naive
    30/minute global limit would still let a single attacker consume
    ~5000 inferences/minute.
    """
    if not body.urls:
        raise HTTPException(status_code=400, detail="urls list must not be empty.")
    if len(body.urls) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 URLs per batch request.")
    # Aggregate body cap. The per-URL 2048-char limit inside the
    # BatchCheckRequest validator already prevents the worst cases,
    # but a request with 100 max-length URLs plus the JSON framing
    # could still approach 200 KB. We refuse earlier so the request
    # doesn't tie up a rate-limit slot just to be rejected during
    # per-URL validation.
    total_chars = sum(len(u) for u in body.urls)
    if total_chars > MAX_BATCH_BODY_CHARS:
        raise HTTPException(
            status_code=413,
            detail=f"Batch payload is {total_chars} chars; max is {MAX_BATCH_BODY_CHARS}.",
        )
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
