import json
import os
import tempfile
from pathlib import Path
from typing import List, Optional

# Stable path: resolves to backend/data/ regardless of where uvicorn runs from
_BACKEND_DIR = Path(__file__).resolve().parents[3]
STORE_PATH = _BACKEND_DIR / "data" / "fraud_events.json"


def _ensure_dir() -> None:
    STORE_PATH.parent.mkdir(parents=True, exist_ok=True)


def _load_raw() -> List[dict]:
    if not STORE_PATH.exists():
        return []
    try:
        text = STORE_PATH.read_text(encoding="utf-8")
        return json.loads(text) if text.strip() else []
    except Exception:
        return []


def _atomic_write(events: List[dict]) -> None:
    """Write to a temp file then replace — prevents corruption on interrupt."""
    _ensure_dir()
    tmp_fd, tmp_path = tempfile.mkstemp(
        dir=STORE_PATH.parent,
        prefix=".fraud_events_tmp_",
        suffix=".json",
    )
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            json.dump(events, f, indent=2, default=str)
        # Atomic on POSIX; on Windows os.replace also works
        os.replace(tmp_path, STORE_PATH)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def load_all() -> List[dict]:
    return _load_raw()


def save_fingerprint(fingerprint: dict) -> None:
    events = _load_raw()
    events.append(fingerprint)
    _atomic_write(events)


def clear_store() -> None:
    _atomic_write([])


def get_fingerprint_by_doc_id(doc_id: str) -> Optional[dict]:
    for e in _load_raw():
        if e.get("doc_id") == doc_id:
            return e
    return None