import json
import uuid
from pathlib import Path
import pytest

import app.services.fraud_dna.store as dna_store


def _make_event(source_type: str = "DOCUMENT") -> dict:
    base = {
        "event_id": str(uuid.uuid4()),
        "source_type": source_type,
        "risk_score": 45,
        "risk_level": "SUSPICIOUS",
        "risk_indicators": ["blank_author"],
        "top_keywords": ["salary"],
        "fingerprint_text": "salary blank_author",
        "created_at": "2024-01-01T00:00:00+00:00",
    }
    if source_type == "DOCUMENT":
        base["doc_id"] = str(uuid.uuid4())
        base["original_filename"] = "test.pdf"
    else:
        base["doc_id"] = None
        base["original_filename"] = None
        base["source_domain"] = "hdfc-verify.com"
    return base


def test_save_and_load_document(tmp_path, monkeypatch):
    fake_store = tmp_path / "fraud_events.json"
    monkeypatch.setattr(dna_store, "STORE_PATH", fake_store)

    event = _make_event("DOCUMENT")
    dna_store.save_fingerprint(event)
    loaded = dna_store.load_all()

    assert len(loaded) == 1
    assert loaded[0]["event_id"] == event["event_id"]


def test_save_and_load_url_event(tmp_path, monkeypatch):
    fake_store = tmp_path / "fraud_events.json"
    monkeypatch.setattr(dna_store, "STORE_PATH", fake_store)

    event = _make_event("URL")
    dna_store.save_fingerprint(event)
    loaded = dna_store.load_all()

    assert len(loaded) == 1
    assert loaded[0]["doc_id"] is None
    assert loaded[0]["source_type"] == "URL"


def test_load_missing_file(tmp_path, monkeypatch):
    fake_store = tmp_path / "nonexistent.json"
    monkeypatch.setattr(dna_store, "STORE_PATH", fake_store)
    assert dna_store.load_all() == []


def test_multiple_events(tmp_path, monkeypatch):
    fake_store = tmp_path / "fraud_events.json"
    monkeypatch.setattr(dna_store, "STORE_PATH", fake_store)

    for _ in range(5):
        dna_store.save_fingerprint(_make_event())

    loaded = dna_store.load_all()
    assert len(loaded) == 5