from typing import List, Optional

RISK_BUCKETS = [
    (0, 30, "CLEAN"),
    (31, 60, "SUSPICIOUS"),
    (61, 100, "HIGH"),
]

# Plain-English explanations shown to frontend/judges
EXPLANATION_MAP = {
    "suspicious_editor":
        "Document was created or edited using image manipulation software — a risk signal.",
    "metadata_mismatch":
        "Document was modified after original creation — possible tampering signal.",
    "blank_author":
        "Author field is missing — weak signal, common in some auto-generated documents.",
    "encrypted_pdf":
        "Document is encrypted — content cannot be fully verified.",
    "scanned_or_image_based":
        "Document has no extractable text — likely scanned. OCR needed for full analysis.",
    "low_text_content":
        "Document has unusually low text for its page count — possible content replacement.",
    "font_anomaly":
        "More than 3 font families detected — uncommon in genuine financial documents.",
    "font_size_anomaly":
        "More than 5 unique font sizes found — may indicate pasted or edited content.",
    "sparse_text_layout":
        "Some pages have very few text blocks — possible deleted or replaced content.",
    "suspicious_spacing":
        "Large empty areas detected on some pages — weak signal, review recommended.",
    "ela_tampering":
        "Visual inconsistency detected via ELA — possible edited image regions (not conclusive).",
    "ela_minor_inconsistency":
        "Minor visual inconsistency via ELA — low-confidence signal only.",
}

# Adjusted scores — reduce false-positive weight on weak signals
SCORE_MAP = {
    "suspicious_editor":      25,   # strong — GIMP/Photoshop is unusual for financial docs
    "metadata_mismatch":      20,   # moderate
    "blank_author":            5,   # REDUCED — very common in legitimate docs
    "encrypted_pdf":          15,
    "scanned_or_image_based": 20,
    "low_text_content":       10,   # REDUCED — sparse docs can be legitimate
    "font_anomaly":           15,
    "font_size_anomaly":       8,   # REDUCED
    "sparse_text_layout":     10,   # REDUCED — weak alone
    "suspicious_spacing":      5,   # REDUCED — very weak signal
    "ela_tampering":          25,   # REDUCED from 30 — ELA is signal, not proof
    "ela_minor_inconsistency": 5,   # REDUCED from 10
}


def _text_indicators(text_analysis: Optional[dict]) -> List[dict]:
    out = []
    if not text_analysis:
        return out
    if text_analysis.get("is_scanned_or_image_based"):
        out.append({
            "rule": "scanned_or_image_based",
            "score": SCORE_MAP["scanned_or_image_based"],
            "detail": "Document has no extractable text — likely scanned or image-based.",
        })
    elif any("unusually low" in w.lower() for w in text_analysis.get("warnings", [])):
        out.append({
            "rule": "low_text_content",
            "score": SCORE_MAP["low_text_content"],
            "detail": "Document has low text content relative to its page count.",
        })
    return out


def _layout_indicators(layout_analysis: Optional[dict]) -> List[dict]:
    out = []
    if not layout_analysis:
        return out

    if layout_analysis.get("font_count", 0) > 3:
        out.append({
            "rule": "font_anomaly",
            "score": SCORE_MAP["font_anomaly"],
            "detail": f"More than 3 font families detected ({layout_analysis['font_count']} found).",
        })

    if layout_analysis.get("font_size_count", 0) > 5:
        out.append({
            "rule": "font_size_anomaly",
            "score": SCORE_MAP["font_size_anomaly"],
            "detail": f"More than 5 unique font sizes detected ({layout_analysis['font_size_count']} found).",
        })

    page_layouts = layout_analysis.get("page_layouts", [])
    sparse = [p for p in page_layouts if p.get("text_blocks", 99) < 3]
    if len(sparse) > 0 and len(page_layouts) > 1:
        out.append({
            "rule": "sparse_text_layout",
            "score": SCORE_MAP["sparse_text_layout"],
            "detail": f"{len(sparse)} page(s) have very few text blocks.",
        })

    suspicious = [p for p in page_layouts if p.get("suspicious_spacing")]
    if suspicious:
        out.append({
            "rule": "suspicious_spacing",
            "score": SCORE_MAP["suspicious_spacing"],
            "detail": f"{len(suspicious)} page(s) have large empty areas with minimal text.",
        })

    return out


def _ela_indicators(ela_analysis: Optional[dict]) -> List[dict]:
    out = []
    if not ela_analysis or not ela_analysis.get("enabled"):
        return out

    ela_score = ela_analysis.get("ela_score", 0)
    suspicious_pages = ela_analysis.get("suspicious_pages", [])

    if ela_score >= 30:
        pages_str = ", ".join(str(p) for p in suspicious_pages)
        out.append({
            "rule": "ela_tampering",
            "score": SCORE_MAP["ela_tampering"],
            "detail": f"High recompression difference on page(s): {pages_str}. Review recommended.",
        })
    elif ela_score >= 10:
        pages_str = ", ".join(str(p) for p in suspicious_pages)
        out.append({
            "rule": "ela_minor_inconsistency",
            "score": SCORE_MAP["ela_minor_inconsistency"],
            "detail": f"Minor recompression inconsistency on page(s): {pages_str}. Low confidence.",
        })

    return out


def _deduplicate(indicators: List[dict]) -> List[dict]:
    seen = set()
    out = []
    for item in indicators:
        if item["rule"] not in seen:
            seen.add(item["rule"])
            out.append(item)
    return out


def calculate_risk(
    metadata_indicators: List[dict],
    text_analysis: Optional[dict] = None,
    layout_analysis: Optional[dict] = None,
    ela_analysis: Optional[dict] = None,
) -> dict:
    all_indicators = _deduplicate(
        metadata_indicators
        + _text_indicators(text_analysis)
        + _layout_indicators(layout_analysis)
        + _ela_indicators(ela_analysis)
    )

    # Normalize scores with central SCORE_MAP to prevent discrepancy from external tools
    for ind in all_indicators:
        rule = ind.get("rule")
        if rule in SCORE_MAP:
            ind["score"] = SCORE_MAP[rule]

    score = min(sum(i["score"] for i in all_indicators), 100)

    level = "CLEAN"
    for low, high, label in RISK_BUCKETS:
        if low <= score <= high:
            level = label
            break

    explanation = [
        EXPLANATION_MAP[i["rule"]]
        for i in all_indicators
        if i["rule"] in EXPLANATION_MAP
    ]

    return {
        "risk_score": score,
        "risk_level": level,
        "indicators": all_indicators,
        "explanation": explanation,
    }