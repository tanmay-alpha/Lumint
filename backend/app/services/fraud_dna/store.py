import json
import uuid
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timezone

STORE_PATH = Path("data/fraud_events.json")


def _load_raw() -> List[dict]:
    if not STORE_PATH.exists():
        return []
    try:
        text = STORE_PATH.read_text(encoding="utf-8")
        return json.loads(text) if text.strip() else []
    except Exception:
        return []


def _save_raw(events: List[dict]) -> None:
    STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STORE_PATH.write_text(
        json.dumps(events, indent=2, default=str),
        encoding="utf-8",
    )


def load_all() -> List[dict]:
    return _load_raw()


def save_fingerprint(fingerprint: dict) -> None:
    events = _load_raw()
    events.append(fingerprint)
    _save_raw(events)


def clear_store() -> None:
    _save_raw([])


def get_fingerprint_by_doc_id(doc_id: str) -> Optional[dict]:
    for e in _load_raw():
        if e.get("doc_id") == doc_id:
            return e
    return None