import hashlib
from typing import List, Dict
from collections import Counter

import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.metrics.pairwise import cosine_similarity

from app.services.fraud_dna.store import load_all
from app.services.fraud_dna.vectorizer import build_tfidf_matrix

DBSCAN_EPS = 0.50
DBSCAN_MIN_SAMPLES = 2


def _campaign_id_from_event_ids(event_ids: List[str]) -> str:
    combined = "_".join(sorted(event_ids))
    return "campaign_" + hashlib.md5(combined.encode()).hexdigest()[:10]


def _common_values(lists: List[List[str]], top_n: int = 5) -> List[str]:
    counter: Counter = Counter()
    for lst in lists:
        counter.update(lst)
    return [item for item, _ in counter.most_common(top_n)]


def _event_label(e: dict) -> str:
    """Safe label for graph/campaign: use filename OR domain OR event_id."""
    return (
        e.get("original_filename")
        or e.get("source_domain")
        or e.get("event_id", "unknown")
    )


def _slim_event(e: dict) -> dict:
    """Frontend-safe minimal event summary."""
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


def run_clustering() -> dict:
    fingerprints = load_all()
    total_events = len(fingerprints)

    if total_events == 0:
        return {"campaigns": [], "total_campaigns": 0, "total_events": 0}

    matrix, vectorizer, valid_event_ids = build_tfidf_matrix(fingerprints)
    fp_map: Dict[str, dict] = {fp["event_id"]: fp for fp in fingerprints}

    if matrix is None:
        return {"campaigns": [], "total_campaigns": 0, "total_events": total_events}

    distance_matrix = np.clip(1 - cosine_similarity(matrix), 0, None)

    labels = DBSCAN(
        eps=DBSCAN_EPS,
        min_samples=DBSCAN_MIN_SAMPLES,
        metric="precomputed",
    ).fit_predict(distance_matrix)

    cluster_groups: Dict[int, List[str]] = {}
    for label, event_id in zip(labels, valid_event_ids):
        if label == -1:
            continue
        cluster_groups.setdefault(label, []).append(event_id)

    campaigns = []
    for label, event_ids in cluster_groups.items():
        events = [fp_map[eid] for eid in event_ids if eid in fp_map]
        if not events:
            continue

        scores = [e.get("risk_score", 0) for e in events]
        avg_score = round(sum(scores) / len(scores), 1)
        dominant_level = Counter(e.get("risk_level", "CLEAN") for e in events).most_common(1)[0][0]

        timestamps = sorted(e.get("created_at", "") for e in events)

        campaigns.append({
            "campaign_id": _campaign_id_from_event_ids(event_ids),
            "event_count": len(events),
            "risk_level": dominant_level,
            "avg_risk_score": avg_score,
            "common_indicators": _common_values([e.get("risk_indicators", []) for e in events]),
            "common_keywords": _common_values([e.get("top_keywords", []) for e in events]),
            "first_seen": timestamps[0] if timestamps else None,
            "last_seen": timestamps[-1] if timestamps else None,
            "events": [_slim_event(e) for e in events],
        })

    campaigns.sort(key=lambda c: c["avg_risk_score"], reverse=True)
    return {
        "campaigns": campaigns,
        "total_campaigns": len(campaigns),
        "total_events": total_events,
    }


def build_graph() -> dict:
    fingerprints = load_all()
    if not fingerprints:
        return {"nodes": [], "edges": []}

    matrix, vectorizer, valid_event_ids = build_tfidf_matrix(fingerprints)
    fp_map = {fp["event_id"]: fp for fp in fingerprints}

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
        sim_matrix = cosine_similarity(matrix)
        n = len(valid_event_ids)
        for i in range(n):
            for j in range(i + 1, n):
                weight = round(float(sim_matrix[i][j]), 4)
                if weight >= 0.30:
                    edges.append({
                        "source": valid_event_ids[i],
                        "target": valid_event_ids[j],
                        "weight": weight,
                        "reason": "similar fingerprint",
                    })

    return {"nodes": nodes, "edges": edges}