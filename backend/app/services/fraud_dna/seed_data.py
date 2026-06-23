"""Seed the Fraud DNA store with a small set of realistic sample events.

The store is JSON-on-disk (see ``store.py``). On a fresh deploy — and on
the demo deployment, which has no real scans — the store is empty and
``/api/fraud-dna/campaigns`` returns 0 events. Seeding 5-10 realistic
fingerprints makes the graph and campaign list non-empty on first load.

Idempotent: ``seed_if_empty`` is a no-op if the store already has data.
The ``seed_now`` function can be called from a CLI or a "Load sample data"
button on the frontend to force a re-seed (e.g. after the store is
cleared by tests).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import List

from app.services.fraud_dna.store import load_all, save_fingerprint, clear_store


def _now_iso(offset_minutes: int = 0) -> str:
    dt = datetime.now(timezone.utc) - timedelta(minutes=offset_minutes)
    return dt.isoformat()


def _make_fingerprint(
    *,
    source_type: str,
    risk_score: int,
    risk_level: str,
    risk_indicators: List[str],
    top_keywords: List[str],
    document_type_hint: str,
    label: str = None,
    source_domain: str = None,
    doc_id: str = None,
    minutes_ago: int = 0,
) -> dict:
    return {
        "event_id": str(uuid.uuid4()),
        "doc_id": doc_id,
        "source_type": source_type,
        "original_filename": label if source_type == "DOCUMENT" else None,
        "saved_filename": (
            f"{doc_id}.pdf" if source_type == "DOCUMENT" and doc_id else None
        ),
        "file_hash": None,
        "metadata_hash": None,
        "editor_tool": None,
        "producer": None,
        "creator": None,
        "source_domain": source_domain,
        "top_keywords": top_keywords,
        "risk_indicators": risk_indicators,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "document_type_hint": document_type_hint,
        "fingerprint_text": " ".join(
            ([label] if label else [])
            + ([source_domain] if source_domain else [])
            + top_keywords
            + risk_indicators
        ),
        "created_at": _now_iso(minutes_ago),
    }


def build_seed_events() -> List[dict]:
    """Return 9 realistic sample fingerprints (URL + DOCUMENT + UPI mix).

    The events are crafted so the DBSCAN clusterer (eps=0.50, min_samples=2)
    produces at least 2 distinct campaigns and 1-2 singletons.

    TF-IDF clustering is keyword-driven: each event's ``fingerprint_text``
    is the corpus the clusterer vectorises. We deliberately repeat a
    *campaign tag* (``c_hdfc``, ``c_invoice``, ``c_upi``) 10 times across
    all events in a cluster so the rare token dominates TF-IDF and
    cosine-similarity clears the clusterer's threshold (>= 0.50). The
    tag is not visible to the user — it only affects the math.

    Cluster composition:
      - HDFC phishing URLs  (3 events, expected cluster)
      - Fake invoice PDFs    (2 events, expected cluster)
      - UPI phishing URLs    (3 events, expected cluster)
      - 1 singleton PDF (ela-anomaly ID doc) that DBSCAN keeps separate
    """
    def tag(t: str) -> list:
        # 10x repetition pushes intra-cluster cosine sim over the
        # DBSCAN(eps=0.50) threshold without leaking across clusters
        # (each cluster has its own unique tag).
        return [t] * 10

    hdfc_indicators = ["suspicious_tld", "bank_name_typosquat", "suspicious_keywords"]
    invoice_indicators = ["metadata_mismatch", "modified_creator_tool", "invalid_pdf_signature"]
    upi_indicators = ["suspicious_tld", "homoglyph_attack", "suspicious_keywords"]
    return [
        # Cluster 1: HDFC phishing URLs (3 events)
        _make_fingerprint(
            source_type="URL",
            source_domain="hdfc-netbanking-verify.tk",
            risk_score=78,
            risk_level="HIGH",
            risk_indicators=hdfc_indicators,
            top_keywords=tag("c_hdfc") + ["login", "verify", "netbanking", "hdfc", "hdfc"],
            document_type_hint="phishing_url",
            minutes_ago=5,
        ),
        _make_fingerprint(
            source_type="URL",
            source_domain="hdfc-secure-kyc-update.click",
            risk_score=82,
            risk_level="HIGH",
            risk_indicators=["bank_name_typosquat", "many_hyphens", "suspicious_tld"],
            top_keywords=tag("c_hdfc") + ["kyc", "update", "secure", "hdfc", "hdfc"],
            document_type_hint="phishing_url",
            minutes_ago=15,
        ),
        _make_fingerprint(
            source_type="URL",
            source_domain="hdfcbank-otp-resend.xyz",
            risk_score=71,
            risk_level="HIGH",
            risk_indicators=hdfc_indicators,
            top_keywords=tag("c_hdfc") + ["otp", "resend", "hdfc", "hdfc"],
            document_type_hint="phishing_url",
            minutes_ago=45,
        ),
        # Cluster 2: Fake invoice PDFs (2 events, plus 1 singleton id doc)
        _make_fingerprint(
            source_type="DOCUMENT",
            label="invoice_2026_06_04.pdf",
            doc_id="seed-doc-001",
            risk_score=88,
            risk_level="CRITICAL",
            risk_indicators=invoice_indicators,
            top_keywords=tag("c_invoice") + ["invoice", "payment", "urgent", "wire", "invoice"],
            document_type_hint="fake_invoice",
            minutes_ago=120,
        ),
        _make_fingerprint(
            source_type="DOCUMENT",
            label="invoice_acme_may26.pdf",
            doc_id="seed-doc-002",
            risk_score=74,
            risk_level="HIGH",
            risk_indicators=["metadata_mismatch", "suspicious_editor"],
            top_keywords=tag("c_invoice") + ["invoice", "wire transfer", "payment", "invoice"],
            document_type_hint="fake_invoice",
            minutes_ago=180,
        ),
        # Singleton ID doc — different campaign tag, expected to stay alone
        _make_fingerprint(
            source_type="DOCUMENT",
            label="pan_card_copy.jpg",
            doc_id="seed-doc-003",
            risk_score=65,
            risk_level="SUSPICIOUS",
            risk_indicators=["ela_tampering", "font_anomaly"],
            top_keywords=["pan", "identity", "document", "id", "tampered"],
            document_type_hint="id_document",
            minutes_ago=240,
        ),
        # Cluster 3: UPI phishing URLs (3 events)
        _make_fingerprint(
            source_type="URL",
            source_domain="paytm-secure-refund@ybl.top",
            risk_score=92,
            risk_level="CRITICAL",
            risk_indicators=upi_indicators,
            top_keywords=tag("c_upi") + ["refund", "upi", "secure", "paytm", "paytm"],
            document_type_hint="upi_phishing",
            minutes_ago=300,
        ),
        _make_fingerprint(
            source_type="URL",
            source_domain="phonepe-cashback-claim.buzz",
            risk_score=68,
            risk_level="HIGH",
            risk_indicators=["suspicious_tld", "suspicious_keywords"],
            top_keywords=tag("c_upi") + ["cashback", "claim", "upi", "phonepe", "phonepe"],
            document_type_hint="upi_phishing",
            minutes_ago=420,
        ),
        _make_fingerprint(
            source_type="URL",
            source_domain="gpay-reward-claim.fun",
            risk_score=76,
            risk_level="HIGH",
            risk_indicators=upi_indicators,
            top_keywords=tag("c_upi") + ["reward", "upi", "gpay", "gpay"],
            document_type_hint="upi_phishing",
            minutes_ago=540,
        ),
    ]


def seed_if_empty() -> int:
    """If the store is empty, append all seed events. Returns count seeded."""
    if load_all():
        return 0
    return seed_now()


def seed_now() -> int:
    """Clear and replace the store with the seed set. Returns count seeded."""
    clear_store()
    events = build_seed_events()
    for e in events:
        save_fingerprint(e)
    return len(events)


if __name__ == "__main__":
    n = seed_now()
    print(f"Seeded {n} fraud events into the store.")