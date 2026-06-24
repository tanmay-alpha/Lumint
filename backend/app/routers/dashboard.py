from fastapi import APIRouter, Query, Depends
from app.dependencies.auth import get_current_user
from app.services.dashboard.stats import (
    get_stats,
    get_recent_events,
    get_risk_distribution,
    get_indicator_summary,
    get_timeline,
)
from app.schemas.dashboard import (
    StatsResponse,
    RecentEventsResponse,
    RiskDistributionResponse,
    IndicatorSummaryResponse,
    TimelineResponse,
)

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"], dependencies=[Depends(get_current_user)])


@router.get("/stats", response_model=StatsResponse)
def dashboard_stats():
    return get_stats()


@router.get("/recent-events", response_model=RecentEventsResponse)
def recent_events(limit: int = Query(default=20, ge=1, le=100)):
    return get_recent_events(limit)


@router.get("/risk-distribution", response_model=RiskDistributionResponse)
def risk_distribution():
    return get_risk_distribution()


@router.get("/indicator-summary", response_model=IndicatorSummaryResponse)
def indicator_summary():
    return get_indicator_summary()


@router.get("/timeline", response_model=TimelineResponse)
def timeline(days: int = Query(default=7, ge=1, le=90)):
    """Scan-volume timeline (last ``days`` days). Powers the dashboard chart."""
    return get_timeline(days)