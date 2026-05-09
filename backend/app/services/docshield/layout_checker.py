from pathlib import Path
from typing import List
import fitz

MAX_FONT_FAMILIES = 3
MAX_FONT_SIZES = 5
SPARSE_BLOCK_THRESHOLD = 3


def check_layout(file_path: Path) -> dict:
    warnings: List[str] = []
    layout_score = 0

    try:
        doc = fitz.open(str(file_path))
    except Exception as e:
        return {
            "font_families": [],
            "font_count": 0,
            "font_sizes": [],
            "font_size_count": 0,
            "page_layouts": [],
            "layout_warnings": [f"Layout extraction failed: {str(e)}"],
            "layout_score": 0,
        }

    all_fonts: set = set()
    all_sizes: set = set()
    page_layouts = []

    for i, page in enumerate(doc):
        blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE).get("blocks", [])
        text_blocks = [b for b in blocks if b.get("type") == 0]

        page_fonts: set = set()
        page_sizes: set = set()
        size_sum = 0.0
        span_count = 0

        for block in text_blocks:
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    font = span.get("font", "Unknown")
                    size = round(span.get("size", 0), 1)
                    page_fonts.add(font)
                    page_sizes.add(size)
                    all_fonts.add(font)
                    all_sizes.add(size)
                    size_sum += size
                    span_count += 1

        avg_size = round(size_sum / span_count, 2) if span_count > 0 else 0.0
        suspicious_spacing = len(text_blocks) < SPARSE_BLOCK_THRESHOLD and page.rect.height > 400

        page_layouts.append({
            "page_number": i + 1,
            "text_blocks": len(text_blocks),
            "avg_font_size": avg_size,
            "unique_fonts": len(page_fonts),
            "unique_font_sizes": len(page_sizes),
            "suspicious_spacing": suspicious_spacing,
        })

    doc.close()

    font_list = sorted(all_fonts)
    size_list = sorted(all_sizes)
    font_count = len(font_list)
    size_count = len(size_list)

    if font_count > MAX_FONT_FAMILIES:
        warnings.append(f"More than {MAX_FONT_FAMILIES} font families detected ({font_count}).")
        layout_score += 15

    if size_count > MAX_FONT_SIZES:
        warnings.append(f"More than {MAX_FONT_SIZES} unique font sizes detected ({size_count}).")
        layout_score += 10

    sparse_pages = [p for p in page_layouts if p["text_blocks"] < SPARSE_BLOCK_THRESHOLD]
    if len(sparse_pages) > 0 and len(page_layouts) > 1:
        warnings.append(f"{len(sparse_pages)} page(s) have very few text blocks.")
        layout_score += 15

    suspicious_pages = [p for p in page_layouts if p["suspicious_spacing"]]
    if suspicious_pages:
        warnings.append(f"{len(suspicious_pages)} page(s) show suspicious spacing/empty areas.")
        layout_score += 10

    return {
        "font_families": font_list,
        "font_count": font_count,
        "font_sizes": size_list,
        "font_size_count": size_count,
        "page_layouts": page_layouts,
        "layout_warnings": warnings,
        "layout_score": layout_score,
    }