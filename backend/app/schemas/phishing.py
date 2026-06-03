from pydantic import BaseModel
from typing import List, Optional, Any
from app.schemas.xai import FeatureContributionSchema


class TriggeredRule(BaseModel):
    rule: str
    score: int
    detail: str


class DomainSimilarityMatch(BaseModel):
    bank: str
    similarity: float


class PhishingCheckResponse(BaseModel):
    url: str
    normalized_url: str
    domain: str
    risk_score: int
    risk_level: str
    triggered_rules: List[TriggeredRule]
    domain_similarity_matches: List[DomainSimilarityMatch]
    phishing_fingerprint: Optional[Any] = None
    feature_contributions: Optional[List[FeatureContributionSchema]] = None
    message: str