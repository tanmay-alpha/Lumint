from pathlib import Path
from typing import List, Optional
import fitz

LOW_TEXT_THRESHOLD_PER_PAGE = 50
PREVIEW_CHAR_LIMIT = 2000


def extract_text(file_path: Path) -> dict:
    warnings: List[str] = []

    try:
        doc = fitz.open(str(file_path))
    except Exception as e:
        return {
            "text_preview": None,
            "total_text_length": 0,
            "page_count": 0,
            "pages": [],
            "is_scanned_or_image_based": True,
            "extraction_method": "pymupdf",
            "warnings": [f"Failed to open PDF: {str(e)}"],
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