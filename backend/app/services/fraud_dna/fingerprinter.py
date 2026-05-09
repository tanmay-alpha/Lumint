import hashlib
import json
import uuid
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timezone

STOPWORDS = {
    "the", "a", "an", "and", "or", "in", "on", "at", "to", "of",
    "for", "with", "is", "it", "this", "that", "be", "as", "by",
    "from", "are", "was", "were", "has", "have", "had", "not",
    "but", "its", "he", "she", "they", "we", "you", "i", "my",
    "your", "our", "their", "do", "does", "did", "will", "would",
    "can", "could", "should", "may", "might", "no", "so", "if",
}

DOCUMENT_TYPE_KEYWORDS = {
    "salary_slip":     ["salary", "payslip", "pay slip", "employee", "gross", "net pay", "deduction"],
    "bank_statement":  ["statement", "account", "balance", "transaction", "debit", "credit", "bank"],
    "kyc":             ["kyc", "know your customer", "aadhaar", "pan", "identity", "verification"],
    "invoice":         ["invoice", "bill", "amount due", "gst", "tax invoice", "vendor"],
    "application_form":["application", "form", "applicant", "declaration", "signature", "date of birth"],
}


def _sha256_file(file_path: Path) -> str:
    try:
        data = file_path.read_bytes()
        return hashlib.sha256(data).hexdigest()
    except Exception:
        return ""


def _sha256_metadata(metadata: Optional[dict]) -> str:
    if not metadata:
        return ""
    try:
        canonical = json.dumps(metadata, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()
    except Exception:
        return ""


def _extract_keywords(text: Optional[str], top_n: int = 15) -> List[str]:
    if not text:
        return []
    words = text.lower().split()
    cleaned = [
        w.strip(".,;:!?\"'()-/\\")
        for w in words
        if len(w) > 3 and w not in STOPWORDS and w.isalpha()
    ]
    freq: dict = {}
    for w in cleaned:
        freq[w] = freq.get(w, 0) + 1
    sorted_words = sorted(freq, key=lambda x: freq[x], reverse=True)
    return sorted_words[:top_n]


def _detect_document_type(keywords: List[str], text_preview: Optional[str]) -> str:
    combined = " ".join(keywords) + " " + (text_preview or "").lower()
    for doc_type, hints in DOCUMENT_TYPE_KEYWORDS.items():
        if any(h in combined for h in hints):
            return doc_type
    return "unknown"


def _get_editor_tool(metadata: Optional[dict]) -> str:
    if not metadata:
        return "unknown"
    creator = (metadata.get("creator") or "").strip()
    producer = (metadata.get("producer") or "").strip()
    return creator or producer or "unknown"


def _build_fingerprint_text(
    keywords: List[str],
    risk_indicators: List[str],
    editor_tool: str,
    doc_type: str,
) -> str:
    parts = keywords + risk_indicators + [editor_tool, doc_type]
    return " ".join(p for p in parts if p and p != "unknown")


def generate_fingerprint(
    doc_id: str,
    file_path: Path,
    original_filename: str,
    saved_filename: str,
    analysis_result: dict,
) -> dict:
    metadata = analysis_result.get("metadata") or {}
    text_analysis = analysis_result.get("text_analysis") or {}
    indicators = analysis_result.get("indicators") or []

    file_hash = _sha256_file(file_path)
    metadata_hash = _sha256_metadata(metadata)

    text_preview = text_analysis.get("text_preview") or ""
    keywords = _extract_keywords(text_preview)
    risk_indicator_names = [i["rule"] for i in indicators if "rule" in i]
    editor_tool = _get_editor_tool(metadata)
    doc_type = _detect_document_type(keywords, text_preview)
    fingerprint_text = _build_fingerprint_text(
        keywords, risk_indicator_names, editor_tool, doc_type
    )

    return {
        "event_id": str(uuid.uuid4()),
        "doc_id": doc_id,
        "source_type": "DOCUMENT",
        "original_filename": original_filename,
        "saved_filename": saved_filename,
        "file_hash": file_hash,
        "metadata_hash": metadata_hash,
        "editor_tool": editor_tool,
        "producer": (metadata.get("producer") or ""),
        "creator": (metadata.get("creator") or ""),
        "top_keywords": keywords,
        "risk_indicators": risk_indicator_names,
        "risk_score": analysis_result.get("risk_score") or 0,
        "risk_level": analysis_result.get("risk_level") or "CLEAN",
        "document_type_hint": doc_type,
        "fingerprint_text": fingerprint_text,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }