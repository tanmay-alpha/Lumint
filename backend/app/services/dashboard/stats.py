from collections import Counter
from datetime import datetime, timezone

from app.services.fraud_dna.store import load_all


def get_stats() -> dict:
    events = load_all()
    total = len(events)

    if total == 0:
        return {
            "total_events": 0, "document_events": 0, "url_events": 0,
            "clean_count": 0, "suspicious_count": 0, "high_risk_count": 0,
            "active_campaigns": 0, "average_risk_score": 0.0,
            "top_indicators": [], "last_updated": datetime.now(timezone.utc).isoformat(),
        }

    level_counts = Counter(e.get("risk_level", "CLEAN") for e in events)
    indicator_counter: Counter = Counter()
    doc_events = url_events = 0
    scores = []

    for e in events:
        src = e.get("source_type")
        if src == "DOCUMENT":
            doc_events += 1
        elif src == "URL":
            url_events += 1
        scores.append(e.get("risk_score", 0))
        indicator_counter.update(e.get("risk_indicators", []))

    try:
        from app.services.fraud_dna.clusterer import run_clustering
        active_campaigns = run_clustering().get("total_campaigns", 0)
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
        "average_risk_score": round(sum(scores) / total, 2),
        "top_indicators": [{"indicator": k, "count": v} for k, v in indicator_counter.most_common(10)],
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }


def get_recent_events(limit: int = 20) -> dict:
    events = load_all()
    return {
        "total": len(events),
        "limit": limit,
        "events": sorted(events, key=lambda e: e.get("created_at", ""), reverse=True)[:limit],
    }


def get_risk_distribution() -> dict:
    counter = Counter(e.get("risk_level", "CLEAN") for e in load_all())
    return {
        "distribution": [{"risk_level": lvl, "count": counter.get(lvl, 0)} for lvl in ("CLEAN", "SUSPICIOUS", "HIGH")]
    }


def get_indicator_summary() -> dict:
    counter: Counter = Counter()
    for e in load_all():
        counter.update(e.get("risk_indicators", []))
    return {"indicators": [{"indicator": k, "count": v} for k, v in counter.most_common(20)]}