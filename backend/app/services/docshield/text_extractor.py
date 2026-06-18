import logging
import re

from pathlib import Path
from typing import List, Optional

import fitz

LOW_TEXT_THRESHOLD_PER_PAGE = 50
PREVIEW_CHAR_LIMIT = 2000

# Words that are uncommon in genuine UPI/banking/payment screenshots
# but very common in scam/phishing payment requests. The list is
# intentionally conservative — false positives on real screenshots
# are far worse than missed scams here, so we only flag obviously
# suspicious vocabulary.
SUSPICIOUS_KEYWORDS = [
    r"\bkyc\b",
    r"\bverify\b",
    r"\bverification\b",
    r"\bsuspend(ed|ing)?\b",
    r"\bblock(ed|ing)?\b",
    r"\bdeactivat(e|ed|ion)\b",
    r"\bexpire[sd]?\b",
    r"\bexpir(y|ing|ed)\b",
    r"\burgent(ly)?\b",
    r"\bclick\s+here\b",
    r"\bclick\s+below\b",
    r"\bclick\s+the\s+link\b",
    r"\bwon\b",
    r"\bcongratulations\b",
    r"\blottery\b",
    r"\breward\b",
    r"\bclaim\b",
    r"\brefund\b",
    r"\bprize\b",
    r"\bgift\s*card\b",
    r"\bbitcoin\b",
    r"\bbtc\b",
    r"\busdt\b",
    r"\bcrypto\b",
    r"\binvest(ment)?\s+opportunity\b",
    r"\bsend\s+to\s+claim\b",
    r"\bkyc\s+update\b",
    r"\bkyc\s+pending\b",
    r"\bpan\s+(card\s+)?update\b",
    r"\bpan\s+card\s+link\b",
    r"\baadhaar\s+link\b",
    r"\bfree\s+offer\b",
    r"\bnet\s*banking\s+login\b",
    r"\binternet\s+banking\b",
    r"\bonline\s+banking\s+login\b",
    r"\bsign\s*in\s+to\s+(?:claim|verify|continue)\b",
]

_KEYWORD_RE = re.compile("|".join(SUSPICIOUS_KEYWORDS), re.IGNORECASE)


def find_suspicious_keywords(text: str) -> List[str]:
    """Return the list of suspicious keywords found in the given text.

    Each match is reported at most once. Case is normalised to the original
    text to make the UI feel grounded.
    """
    if not text:
        return []
    seen: set = set()
    out: List[str] = []
    for m in _KEYWORD_RE.finditer(text):
        word = m.group(0).strip()
        if not word:
            continue
        key = word.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(word)
    return out


def keyword_score(matches: List[str]) -> int:
    """Return a small risk score scaled by how many suspicious keywords fired.

    0 matches -> 0
    1 match   -> 25
    2 matches -> 45
    3 matches -> 65
    4+ matches -> 80 (capped)
    """
    n = len(matches)
    if n == 0:
        return 0
    if n == 1:
        return 25
    if n == 2:
        return 45
    if n == 3:
        return 65
    return 80

logger = logging.getLogger("lumint.services.docshield.text_extractor")


def extract_text(file_path: Path) -> dict:
    warnings: List[str] = []

    try:
        doc = fitz.open(str(file_path))
    except Exception:
        logger.exception("PDF text extraction failed")
        return {
            "text_preview": None,
            "total_text_length": 0,
            "page_count": 0,
            "pages": [],
            "is_scanned_or_image_based": True,
            "extraction_method": "pymupdf",
            "warnings": ["Failed to open PDF."],
        }

    page_count = doc.page_count
    pages = []
    full_text = ""

    for i, page in enumerate(doc):
        text = page.get_text("text") or ""
        word_count = len(text.split())
        has_text = len(text.strip()) > 0

        pages.append({
            "page_number": i + 1,
            "text_length": len(text),
            "word_count": word_count,
            "has_extractable_text": has_text,
        })
        full_text += text

    doc.close()

    total_length = len(full_text)
    text_preview = full_text[:PREVIEW_CHAR_LIMIT].strip()

    pages_without_text = sum(1 for p in pages if not p["has_extractable_text"])
    is_scanned = (
        total_length == 0
        or (page_count > 1 and pages_without_text >= page_count // 2)
    )

    if is_scanned:
        warnings.append(
            "Document appears to be scanned or image-based. OCR required for text analysis."
        )

    if (
        page_count > 1
        and not is_scanned
        and total_length < LOW_TEXT_THRESHOLD_PER_PAGE * page_count
    ):
        warnings.append("Document has unusually low text content for its page count.")

    return {
        "text_preview": text_preview or None,
        "total_text_length": total_length,
        "page_count": page_count,
        "pages": pages,
        "is_scanned_or_image_based": is_scanned,
        "extraction_method": "pymupdf",
        "warnings": warnings,
    }