import hashlib
import json
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

STOPWORDS = {
    "the", "a", "an", "and", "or", "in", "on", "at", "to", "of", "for", "with",
    "is", "it", "this", "that", "be", "as", "by", "from", "are", "was", "were",
    "has", "have", "had", "not", "but", "its", "he", "she", "they", "we", "you",
    "i", "my", "your", "our", "their", "do", "does", "did", "will", "would",
    "can", "could", "should", "may", "might", "no", "so", "if",
}

DOCUMENT_TYPE_KEYWORDS = {
    "salary_slip":      ["salary", "payslip", "pay slip", "employee", "gross", "net pay", "deduction"],
    "bank_statement":   ["statement", "account", "balance", "transaction", "debit", "credit", "bank"],
    "kyc":              ["kyc", "know your customer", "aadhaar", "pan", "identity", "verification"],
    "invoice":          ["invoice", "bill", "amount due", "gst", "tax invoice", "vendor"],
    "application_form": ["application", "form", "applicant", "declaration", "signature", "date of birth"],
}


def _sha256_file(file_path: Path) -> str:
    try:
        return hashlib.sha256(file_path.read_bytes()).hexdigest()
    except Exception:
        return ""


def _sha256_metadata(metadata: Optional[dict]) -> str:
    if not metadata:
        return ""
    try:
        return hashlib.sha256(json.dumps(metadata, sort_keys=True, default=str).encode()).hexdigest()
    except Exception:
        return ""


def _extract_keywords(text: Optional[str], top_n: int = 15) -> List[str]:
    if not text:
        return []
    words = [w.strip(".,;:!?\"'()-/\\") for w in text.lower().split()]
    freq = Counter(w for w in words if len(w) > 3 and w not in STOPWORDS and w.isalpha())
    return [w for w, _ in freq.most_common(top_n)]


def _detect_document_type(keywords: List[str], text_preview: Optional[str]) -> str:
    combined = " ".join(keywords) + " " + (text_preview or "").lower()
    return next((dt for dt, hints in DOCUMENT_TYPE_KEYWORDS.items() if any(h in combined for h in hints)), "unknown")


def generate_fingerprint(
    doc_id: str,
    file_path: Path,
    original_filename: str,
    saved_filename: str,
    analysis_result: dict,
) -> dict:
    metadata = analysis_result.get("metadata") or {}
    text_preview = (analysis_result.get("text_analysis") or {}).get("text_preview") or ""
    indicators = analysis_result.get("indicators") or []

    keywords = _extract_keywords(text_preview)
    risk_indicator_names = [i["rule"] for i in indicators if "rule" in i]
    creator = (metadata.get("creator") or "").strip()
    producer = (metadata.get("producer") or "").strip()
    editor_tool = creator or producer or "unknown"
    doc_type = _detect_document_type(keywords, text_preview)
    fingerprint_parts = keywords + risk_indicator_names + [editor_tool, doc_type]

    return {
        "event_id": str(uuid.uuid4()),
        "doc_id": doc_id,
        "source_type": "DOCUMENT",
        "original_filename": original_filename,
        "saved_filename": saved_filename,
        "file_hash": _sha256_file(file_path),
        "metadata_hash": _sha256_metadata(metadata),
        "editor_tool": editor_tool,
        "producer": producer,
        "creator": creator,
        "top_keywords": keywords,
        "risk_indicators": risk_indicator_names,
        "risk_score": analysis_result.get("risk_score") or 0,
        "risk_level": analysis_result.get("risk_level") or "CLEAN",
        "document_type_hint": doc_type,
        "fingerprint_text": " ".join(p for p in fingerprint_parts if p and p != "unknown"),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }