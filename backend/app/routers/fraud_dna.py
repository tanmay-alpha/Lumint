from fastapi import APIRouter, Depends, Request
from app.dependencies.auth import get_current_user
from app.rate_limit import limiter
from app.services.fraud_dna.store import load_all
from app.services.fraud_dna.clusterer import run_clustering, build_graph
from app.schemas.fraud_dna import CampaignsResponse, GraphResponse

router = APIRouter(prefix="/api/fraud-dna", tags=["fraud-dna"], dependencies=[Depends(get_current_user)])


@router.post("/seed")
@limiter.limit("5/minute")
def seed_sample_events(request: Request):
    """Replace the store with the curated sample event set.

    Useful for the "Load sample data" button on the Fraud DNA page —
    clicking it gives the user a fully-populated graph without needing
    to perform real scans first. Idempotent in the sense that the
    resulting state is the same regardless of prior contents.
    """
    from app.services.fraud_dna.seed_data import seed_now
    n = seed_now()
    return {"seeded": n, "total_events": len(load_all())}


@router.get("/fingerprints")
@limiter.limit("60/minute")
def get_fingerprints(request: Request):
    events = load_all()
    return {"total": len(events), "fingerprints": events}


@router.get("/campaigns", response_model=CampaignsResponse)
@limiter.limit("10/minute")
def get_campaigns(request: Request):
    return run_clustering()


@router.get("/graph", response_model=GraphResponse)
@limiter.limit("20/minute")
def get_graph(request: Request):
    return build_graph()


@router.post("/recluster", response_model=CampaignsResponse)
@limiter.limit("2/minute")
def recluster(request: Request):
    """Force a re-clustering of all stored fingerprints.

    This is CPU-bound and O(n²) on the number of events. We rate-limit
    to 2/minute so a single compromised client cannot exhaust the
    worker's CPU by spamming the endpoint. Clients should cache the
    result and call this only when the dataset has grown significantly.
    """
    return run_clustering()


@router.get("/threat-summary")
def threat_summary():
    """AI feature: generate a plain-English threat intelligence summary from all stored fingerprints."""
    events = load_all()
    if not events:
        return {"summary": "No fraud events recorded yet.", "threat_level": "NONE", "top_risks": []}

    from collections import Counter
    level_counts = Counter(e.get("risk_level", "CLEAN") for e in events)
    indicator_counts = Counter(ind for e in events for ind in e.get("risk_indicators", []))
    top_risks = [{"indicator": k, "frequency": v} for k, v in indicator_counts.most_common(5)]

    high = level_counts.get("HIGH", 0)
    susp = level_counts.get("SUSPICIOUS", 0)
    total = len(events)

    if high / total > 0.4:
        threat_level, summary = "CRITICAL", f"Over 40% of {total} events are HIGH risk. Immediate review required."
    elif (high + susp) / total > 0.5:
        threat_level, summary = "ELEVATED", f"{high + susp} of {total} events show suspicious or high-risk signals."
    else:
        threat_level, summary = "NORMAL", f"{total} events analyzed. Most appear clean. Routine monitoring recommended."

    return {
        "total_events": total,
        "threat_level": threat_level,
        "summary": summary,
        "top_risks": top_risks,
        "high_risk_count": high,
        "suspicious_count": susp,
    }