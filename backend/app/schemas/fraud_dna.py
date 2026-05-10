from pydantic import BaseModel
from typing import List, Optional, Any


class FraudEventSummary(BaseModel):
    event_id: Optional[str] = None
    doc_id: Optional[str] = None          # None for URL events
    source_type: Optional[str] = "DOCUMENT"
    label: Optional[str] = None           # filename or domain
    risk_score: Optional[int] = 0
    risk_level: Optional[str] = "CLEAN"
    document_type_hint: Optional[str] = None
    created_at: Optional[str] = None


class FraudCampaign(BaseModel):
    campaign_id: str
    event_count: int
    risk_level: str
    avg_risk_score: float
    common_indicators: List[str]
    common_keywords: List[str]
    first_seen: Optional[str] = None
    last_seen: Optional[str] = None
    events: List[FraudEventSummary]


class CampaignsResponse(BaseModel):
    campaigns: List[FraudCampaign]
    total_campaigns: int
    total_events: int


class GraphNode(BaseModel):
    id: str
    label: str
    type: str
    risk_level: str
    risk_score: int
    source_type: Optional[str] = "DOCUMENT"
    doc_id: Optional[str] = None          # None for URL events


class GraphEdge(BaseModel):
    source: str
    target: str
    weight: float
    reason: str


class GraphResponse(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]