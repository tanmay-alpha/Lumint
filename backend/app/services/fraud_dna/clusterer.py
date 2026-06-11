import hashlib
from collections import Counter
from typing import Dict, List

import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.metrics.pairwise import cosine_similarity

from app.services.fraud_dna.store import load_all
from app.services.fraud_dna.vectorizer import build_tfidf_matrix

DBSCAN_EPS = 0.50
DBSCAN_MIN_SAMPLES = 2


def _campaign_id(event_ids: List[str]) -> str:
    return "campaign_" + hashlib.sha256("_".join(sorted(event_ids)).encode()).hexdigest()[:10]


def _top_values(lists: List[List[str]], n: int = 5) -> List[str]:
    c: Counter = Counter()
    for lst in lists:
        c.update(lst)
    return [k for k, _ in c.most_common(n)]


def _event_label(e: dict) -> str:
    return e.get("original_filename") or e.get("source_domain") or e.get("event_id", "unknown")


def _slim_event(e: dict) -> dict:
    return {
        "event_id": e.get("event_id"),
        "doc_id": e.get("doc_id"),
        "source_type": e.get("source_type", "DOCUMENT"),
        "label": _event_label(e),
        "risk_score": e.get("risk_score", 0),
        "risk_level": e.get("risk_level", "CLEAN"),
        "document_type_hint": e.get("document_type_hint"),
        "created_at": e.get("created_at"),
    }


def _load_matrix():
    """Shared loader: returns (fingerprints, fp_map, matrix, valid_event_ids)."""
    fingerprints = load_all()
    if not fingerprints:
        return fingerprints, {}, None, []
    fp_map: Dict[str, dict] = {fp["event_id"]: fp for fp in fingerprints}
    matrix, _, valid_ids = build_tfidf_matrix(fingerprints)
    return fingerprints, fp_map, matrix, valid_ids


def run_clustering() -> dict:
    fingerprints, fp_map, matrix, valid_ids = _load_matrix()
    total = len(fingerprints)

    if total == 0:
        return {"campaigns": [], "total_campaigns": 0, "total_events": 0}
    if matrix is None:
        return {"campaigns": [], "total_campaigns": 0, "total_events": total}

    labels = DBSCAN(
        eps=DBSCAN_EPS, min_samples=DBSCAN_MIN_SAMPLES, metric="precomputed"
    ).fit_predict(np.clip(1 - cosine_similarity(matrix), 0, None))

    groups: Dict[int, List[str]] = {}
    for label, eid in zip(labels, valid_ids):
        if label != -1:
            groups.setdefault(label, []).append(eid)

    campaigns = []
    for event_ids in groups.values():
        events = [fp_map[eid] for eid in event_ids if eid in fp_map]
        if not events:
            continue
        scores = [e.get("risk_score", 0) for e in events]
        timestamps = sorted(e.get("created_at", "") for e in events)
        campaigns.append({
            "campaign_id": _campaign_id(event_ids),
            "event_count": len(events),
            "risk_level": Counter(e.get("risk_level", "CLEAN") for e in events).most_common(1)[0][0],
            "avg_risk_score": round(sum(scores) / len(scores), 1),
            "common_indicators": _top_values([e.get("risk_indicators", []) for e in events]),
            "common_keywords": _top_values([e.get("top_keywords", []) for e in events]),
            "first_seen": timestamps[0] if timestamps else None,
            "last_seen": timestamps[-1] if timestamps else None,
            "events": [_slim_event(e) for e in events],
        })

    campaigns.sort(key=lambda c: c["avg_risk_score"], reverse=True)
    return {"campaigns": campaigns, "total_campaigns": len(campaigns), "total_events": total}


def build_graph() -> dict:
    fingerprints, fp_map, matrix, valid_ids = _load_matrix()
    if not fingerprints:
        return {"nodes": [], "edges": []}

    nodes = [
        {
            "id": fp["event_id"],
            "label": _event_label(fp),
            "type": "event",
            "risk_level": fp.get("risk_level", "CLEAN"),
            "risk_score": fp.get("risk_score", 0),
            "source_type": fp.get("source_type", "DOCUMENT"),
            "doc_id": fp.get("doc_id"),
        }
        for fp in fingerprints
    ]

    edges = []
    if matrix is not None:
        sim = cosine_similarity(matrix)
        n = len(valid_ids)
        for i in range(n):
            for j in range(i + 1, n):
                w = round(float(sim[i][j]), 4)
                if w >= 0.30:
                    edges.append({"source": valid_ids[i], "target": valid_ids[j], "weight": w, "reason": "similar fingerprint"})

    return {"nodes": nodes, "edges": edges}