from typing import List

RISK_BUCKETS = [
    (0, 30, "CLEAN"),
    (31, 60, "SUSPICIOUS"),
    (61, 100, "HIGH"),
]


def score_url(triggered_rules: List[dict]) -> dict:
    total = min(sum(r["score"] for r in triggered_rules), 100)

    level = "CLEAN"
    for low, high, label in RISK_BUCKETS:
        if low <= total <= high:
            level = label
            break

    return {"risk_score": total, "risk_level": level}