from pydantic import BaseModel
from typing import List, Optional, Literal


class DocumentAIRequest(BaseModel):
    original_filename: str
    risk_score: int
    risk_level: str
    indicators: List[dict]
    metadata: Optional[dict] = None
    ela_analysis: Optional[dict] = None
    layout_analysis: Optional[dict] = None
    text_analysis: Optional[dict] = None


class DocumentAIResponse(BaseModel):
    verdict: Literal["GENUINE", "SUSPICIOUS", "FRAUDULENT"]
    confidence: int
    anomalies: List[str]
    attack_type: str
    analyst_note: str
    recommended_action: str
    model_used: str
    latency_ms: int


class PhishingAIRequest(BaseModel):
    url: str
    normalized_url: str
    domain: str
    risk_score: int
    risk_level: str
    triggered_rules: List[dict]
    domain_similarity_matches: List[dict]
    top_keywords: Optional[List[str]] = None
    is_official_bank_domain: Optional[bool] = False


class PhishingAIResponse(BaseModel):
    verdict: Literal["SAFE", "SUSPICIOUS", "PHISHING"]
    target_brand: Optional[str] = None
    attack_vector: Literal[
        "credential_harvest",
        "malware_delivery",
        "financial_scam",
        "account_takeover",
        "brand_impersonation",
        "unknown",
    ]
    confidence: int
    analyst_note: str
    ioc_summary: List[str]
    model_used: str
    latency_ms: int


class CampaignEventSummary(BaseModel):
    event_id: str
    doc_id: Optional[str] = None
    source_type: Literal["DOCUMENT", "URL"]
    label: str
    risk_score: int
    risk_level: str
    document_type_hint: str
    created_at: str


class CampaignAIRequest(BaseModel):
    campaign_id: str
    event_count: int
    risk_level: str
    avg_risk_score: float
    common_indicators: List[str]
    common_keywords: List[str]
    first_seen: Optional[str] = None
    last_seen: Optional[str] = None
    events: List[CampaignEventSummary]


class CampaignAIResponse(BaseModel):
    campaign_name: str
    threat_level: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    pattern_summary: str
    estimated_scale: str
    analyst_brief: str
    recommended_actions: List[str]
    ttps: List[str]
    model_used: str
    latency_ms: int


class UPIAIRequest(BaseModel):
    utr_number: Optional[str] = None
    risk_score: int = 0
    sender: Optional[str] = None
    receiver: Optional[str] = None
    amount: Optional[float] = None
    font_anomalies: bool = False
    suspicious_handle: bool = False


class UPIAIResponse(BaseModel):
    verdict: Literal["GENUINE", "SUSPICIOUS", "FORGED"]
    confidence: int
    forgery_method: Optional[str] = None
    evidence_points: List[str]
    analyst_note: str
    recommended_action: str
    model_used: str
    latency_ms: int
