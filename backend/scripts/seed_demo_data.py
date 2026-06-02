import json
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path

STORE = Path(__file__).parent.parent / "data" / "fraud_events.json"


def ts(offset_minutes: int = 0) -> str:
    return (datetime.now(timezone.utc) - timedelta(minutes=offset_minutes)).isoformat()


SEED_EVENTS = [
    # Clean document 1
    {
        "event_id": str(uuid.uuid4()), "doc_id": str(uuid.uuid4()),
        "source_type": "DOCUMENT", "original_filename": "real_salary_slip.pdf",
        "saved_filename": "seed_001.pdf", "file_hash": "aabbcc001",
        "metadata_hash": "mmhash001", "editor_tool": "Microsoft Word",
        "producer": "Microsoft Word", "creator": "Microsoft Word",
        "top_keywords": ["salary", "employee", "gross", "net", "deduction"],
        "risk_indicators": [], "risk_score": 10, "risk_level": "CLEAN",
        "document_type_hint": "salary_slip",
        "fingerprint_text": "salary employee gross net deduction microsoft word salary_slip",
        "created_at": ts(60),
    },
    # Clean document 2
    {
        "event_id": str(uuid.uuid4()), "doc_id": str(uuid.uuid4()),
        "source_type": "DOCUMENT", "original_filename": "real_bank_statement.pdf",
        "saved_filename": "seed_002.pdf", "file_hash": "aabbcc002",
        "metadata_hash": "mmhash002", "editor_tool": "Adobe Acrobat",
        "producer": "Adobe Acrobat", "creator": "Adobe Acrobat",
        "top_keywords": ["balance", "transaction", "debit", "credit", "account"],
        "risk_indicators": [], "risk_score": 15, "risk_level": "CLEAN",
        "document_type_hint": "bank_statement",
        "fingerprint_text": "balance transaction debit credit account adobe bank_statement",
        "created_at": ts(55),
    },
    # Suspicious document 1 — GIMP edited salary slip (similar to seed_004 → forms cluster)
    {
        "event_id": str(uuid.uuid4()), "doc_id": str(uuid.uuid4()),
        "source_type": "DOCUMENT", "original_filename": "tampered_salary_slip_v1.pdf",
        "saved_filename": "seed_003.pdf", "file_hash": "aabbcc003",
        "metadata_hash": "mmhash003", "editor_tool": "GIMP",
        "producer": "GIMP", "creator": "GIMP",
        "top_keywords": ["salary", "employee", "hdfc", "slip", "gross"],
        "risk_indicators": ["suspicious_editor", "metadata_mismatch", "blank_author"],
        "risk_score": 55, "risk_level": "SUSPICIOUS",
        "document_type_hint": "salary_slip",
        "fingerprint_text": "salary employee hdfc slip gross gimp suspicious_editor metadata_mismatch blank_author salary_slip",
        "created_at": ts(45),
    },
    # Suspicious document 2 — GIMP edited salary slip (clusters with seed_003)
    {
        "event_id": str(uuid.uuid4()), "doc_id": str(uuid.uuid4()),
        "source_type": "DOCUMENT", "original_filename": "tampered_salary_slip_v2.pdf",
        "saved_filename": "seed_004.pdf", "file_hash": "aabbcc004",
        "metadata_hash": "mmhash004", "editor_tool": "GIMP",
        "producer": "GIMP", "creator": "GIMP",
        "top_keywords": ["salary", "employee", "hdfc", "gross", "net"],
        "risk_indicators": ["suspicious_editor", "blank_author", "font_anomaly"],
        "risk_score": 50, "risk_level": "SUSPICIOUS",
        "document_type_hint": "salary_slip",
        "fingerprint_text": "salary employee hdfc gross net gimp suspicious_editor blank_author font_anomaly salary_slip",
        "created_at": ts(40),
    },
    # High risk phishing URL 1
    {
        "event_id": str(uuid.uuid4()), "doc_id": None,
        "source_type": "URL", "original_filename": None,
        "saved_filename": None, "file_hash": None,
        "metadata_hash": None, "editor_tool": None,
        "producer": None, "creator": None,
        "source_domain": "hdfc-bank-verify-kyc.com",
        "top_keywords": ["verify", "kyc", "login"],
        "risk_indicators": ["bank_name_typosquat", "suspicious_keywords", "many_hyphens"],
        "risk_score": 70, "risk_level": "HIGH",
        "document_type_hint": "phishing_url",
        "fingerprint_text": "hdfc-bank-verify-kyc.com verify kyc login bank_name_typosquat suspicious_keywords many_hyphens phishing_url",
        "created_at": ts(30),
    },
    # High risk phishing URL 2
    {
        "event_id": str(uuid.uuid4()), "doc_id": None,
        "source_type": "URL", "original_filename": None,
        "saved_filename": None, "file_hash": None,
        "metadata_hash": None, "editor_tool": None,
        "producer": None, "creator": None,
        "source_domain": "sbi-netbanking-otp-update.co",
        "top_keywords": ["otp", "update", "netbanking"],
        "risk_indicators": ["bank_name_typosquat", "suspicious_keywords", "many_hyphens", "suspicious_tld"],
        "risk_score": 85, "risk_level": "HIGH",
        "document_type_hint": "phishing_url",
        "fingerprint_text": "sbi-netbanking-otp-update.co otp update netbanking bank_name_typosquat suspicious_keywords many_hyphens suspicious_tld phishing_url",
        "created_at": ts(20),
    },
]


def seed():
    STORE.parent.mkdir(parents=True, exist_ok=True)
    existing = []
    if STORE.exists():
        try:
            existing = json.loads(STORE.read_text(encoding="utf-8"))
        except Exception:
            existing = []
    combined = existing + SEED_EVENTS
    STORE.write_text(json.dumps(combined, indent=2, default=str), encoding="utf-8")
    print(f"Seeded {len(SEED_EVENTS)} events -> {STORE}")


if __name__ == "__main__":
    seed()