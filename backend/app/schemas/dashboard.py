from pydantic import BaseModel
from typing import List, Any


class IndicatorCount(BaseModel):
    indicator: str
    count: int


class StatsResponse(BaseModel):
    total_events: int
    document_events: int
    url_events: int
    clean_count: int
    suspicious_count: int
    high_risk_count: int
    active_campaigns: int
    average_risk_score: float
    top_indicators: List[IndicatorCount]
    last_updated: str


class RecentEventsResponse(BaseModel):
    total: int
    limit: int
    events: List[Any]


class RiskDistributionItem(BaseModel):
    risk_level: str
    count: int


class RiskDistributionResponse(BaseModel):
    distribution: List[RiskDistributionItem]


class IndicatorSummaryResponse(BaseModel):
    indicators: List[IndicatorCount]