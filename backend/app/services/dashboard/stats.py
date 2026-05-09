from collections import Counter
from datetime import datetime, timezone
from typing import List

from app.services.fraud_dna.store import load_all


def get_stats() -> dict:
    events = load_all()
    total = len(events)

    if total == 0:
        return {
            "total_events": 0,
            "document_events": 0,
            "url_events": 0,
            "clean_count": 0,
            "suspicious_count": 0,
            "high_risk_count": 0,
            "active_campaigns": 0,
            "average_risk_score": 0.0,
            "top_indicators": [],
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }

    doc_events = sum(1 for e in events if e.get("source_type") == "DOCUMENT")
    url_events = sum(1 for e in events if e.get("source_type") == "URL")

    level_counts = Counter(e.get("risk_level", "CLEAN") for e in events)
    scores = [e.get("risk_score", 0) for e in events]
    avg_score = round(sum(scores) / len(scores), 2)

    indicator_counter: Counter = Counter()
    for e in events:
        for ind in e.get("risk_indicators", []):
            indicator_counter[ind] += 1

    top_indicators = [
        {"indicator": ind, "count": cnt}
        for ind, cnt in indicator_counter.most_common(10)
    ]

    # Reuse clusterer for campaign count
    try:
        from app.services.fraud_dna.clusterer import run_clustering
        cluster_result = run_clustering()
        active_campaigns = cluster_result.get("total_campaigns", 0)
    except Exception:
        active_campaigns = 0

    return {
        "total_events": total,
        "document_events": doc_events,
        "url_events": url_events,
        "clean_count": level_counts.get("CLEAN", 0),
        "suspicious_count": level_counts.get("SUSPICIOUS", 0),
        "high_risk_count": level_counts.get("HIGH", 0),
        "active_campaigns": active_campaigns,
        "average_risk_score": avg_score,
        "top_indicators": top_indicators,
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }


def get_recent_events(limit: int = 20) -> dict:
    events = load_all()
    sorted_events = sorted(events, key=lambda e: e.get("created_at", ""), reverse=True)
    return {
        "total": len(events),
        "limit": limit,
        "events": sorted_events[:limit],
    }


def get_risk_distribution() -> dict:
    events = load_all()
    counter = Counter(e.get("risk_level", "CLEAN") for e in events)
    return {
        "distribution": [
            {"risk_level": level, "count": counter.get(level, 0)}
            for level in ["CLEAN", "SUSPICIOUS", "HIGH"]
        ]
    }


def get_indicator_summary() -> dict:
    events = load_all()
    counter: Counter = Counter()
    for e in events:
        for ind in e.get("risk_indicators", []):
            counter[ind] += 1
    return {
        "indicators": [
            {"indicator": ind, "count": cnt}
            for ind, cnt in counter.most_common(20)
        ]
    }