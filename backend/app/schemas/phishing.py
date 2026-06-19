from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Any
from app.schemas.xai import FeatureContributionSchema


class TriggeredRule(BaseModel):
    rule: str
    score: int
    detail: str


class DomainSimilarityMatch(BaseModel):
    bank: str
    similarity: float


class PhishingCheckResponse(BaseModel):
    """Response schema for a single URL phishing check.

    `score_source` indicates whether the `risk_score` was produced by the
    trained ML model (`"ml"`) or by the deterministic rule-based heuristic
    fallback (`"heuristic"`). It is `None` only for very old client/server
    versions that predate the field; current clients should always see one
    of the two values.
    """
    url: str
    normalized_url: str
    domain: str
    risk_score: int
    risk_level: str
    triggered_rules: List[TriggeredRule]
    domain_similarity_matches: List[DomainSimilarityMatch]
    phishing_fingerprint: Optional[Any] = None
    feature_contributions: Optional[List[FeatureContributionSchema]] = None
    score_source: Optional[Literal["ml", "heuristic"]] = Field(
        default=None,
        description=(
            "Origin of the risk_score: 'ml' when produced by the trained "
            "phishing classifier in the ML registry, 'heuristic' when "
            "produced by the rule-based fallback scorer (e.g. when no "
            "trained model is loaded). New in this version; older clients "
            "may not send or read this field."
        ),
    )
    message: str