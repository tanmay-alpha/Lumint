from collections import Counter
from datetime import datetime, timezone, timedelta

from app.services.fraud_dna.store import load_all


def _bucket_for_level(level: str) -> str:
    """Map raw risk_level strings into the 4 buckets the dashboard exposes.

    CRITICAL is its own bucket (separate from HIGH) so the dashboard pie
    can show "Critical" instead of hiding it inside "High".
    """
    if level == "CRITICAL":
        return "CRITICAL"
    if level == "HIGH":
        return "HIGH"
    if level == "SUSPICIOUS":
        return "SUSPICIOUS"
    return "CLEAN"


def get_stats() -> dict:
    events = load_all()
    total = len(events)

    if total == 0:
        return {
            "total_events": 0, "document_events": 0, "url_events": 0,
            "clean_count": 0, "suspicious_count": 0, "high_risk_count": 0, "critical_count": 0,
            "active_campaigns": 0, "average_risk_score": 0.0,
            "top_indicators": [], "last_updated": datetime.now(timezone.utc).isoformat(),
        }

    level_counts = Counter(_bucket_for_level(e.get("risk_level", "CLEAN")) for e in events)
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
        "critical_count": level_counts.get("CRITICAL", 0),
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
    counter = Counter(_bucket_for_level(e.get("risk_level", "CLEAN")) for e in load_all())
    return {
        "distribution": [
            {"risk_level": lvl, "count": counter.get(lvl, 0)}
            for lvl in ("CLEAN", "SUSPICIOUS", "HIGH", "CRITICAL")
        ]
    }


def get_indicator_summary() -> dict:
    counter: Counter = Counter()
    for e in load_all():
        counter.update(e.get("risk_indicators", []))
    return {"indicators": [{"indicator": k, "count": v} for k, v in counter.most_common(20)]}


def get_timeline(days: int = 7) -> dict:
    """Return scan-volume timeline for the last ``days`` days (oldest first).

    Each bucket contains:
      - date           (YYYY-MM-DD, the bucket's day in UTC)
      - phishing       (URL events)
      - documents      (DOCUMENT events)
      - total          (sum of the two)

    Days with no events are included with zero counts so the chart x-axis
    is continuous.

    Note: this groups by *created_at* day. On a fresh deploy with seed
    data only, all events land on the same day, so earlier buckets will
    be zero — that's correct, not a bug. New scans immediately update.
    """
    end = datetime.now(timezone.utc).date()
    start = end - timedelta(days=days - 1)

    buckets: dict = {(start + timedelta(days=i)).isoformat(): {"phishing": 0, "documents": 0}
                     for i in range(days)}

    for e in load_all():
        created = e.get("created_at")
        if not created:
            continue
        try:
            d = datetime.fromisoformat(created.replace("Z", "+00:00")).date()
        except (ValueError, AttributeError):
            continue
        if d < start or d > end:
            continue
        key = d.isoformat()
        if key not in buckets:
            continue
        if e.get("source_type") == "DOCUMENT":
            buckets[key]["documents"] += 1
        elif e.get("source_type") == "URL":
            buckets[key]["phishing"] += 1

    points = []
    for date_str in sorted(buckets):
        b = buckets[date_str]
        points.append({
            "date": date_str,
            "phishing": b["phishing"],
            "documents": b["documents"],
            "total": b["phishing"] + b["documents"],
        })

    return {
        "days": days,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "points": points,
        "total_scans": sum(p["total"] for p in points),
    }