import json
import uuid
from pathlib import Path
from app.services.fraud_dna import store as dna_store


def _make_event():
    return {
        "event_id": str(uuid.uuid4()),
        "doc_id": str(uuid.uuid4()),
        "source_type": "DOCUMENT",
        "original_filename": "test.pdf",
        "risk_score": 45,
        "risk_level": "SUSPICIOUS",
        "risk_indicators": ["blank_author"],
        "top_keywords": ["salary"],
        "fingerprint_text": "salary blank_author",
        "created_at": "2024-01-01T00:00:00+00:00",
    }


def test_save_and_load(tmp_path, monkeypatch):
    fake_store = tmp_path / "fraud_events.json"
    monkeypatch.setattr(dna_store, "STORE_PATH", fake_store)

    event = _make_event()
    dna_store.save_fingerprint(event)
    loaded = dna_store.load_all()

    assert len(loaded) == 1
    assert loaded[0]["event_id"] == event["event_id"]


def test_load_missing_file(tmp_path, monkeypatch):
    fake_store = tmp_path / "nonexistent.json"
    monkeypatch.setattr(dna_store, "STORE_PATH", fake_store)
    result = dna_store.load_all()
    assert result == []