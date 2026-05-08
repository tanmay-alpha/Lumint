from typing import List, Optional


RISK_BUCKETS = [
    (0, 30, "CLEAN"),
    (31, 60, "SUSPICIOUS"),
    (61, 100, "HIGH"),
]

EXPLANATION_MAP = {
    "suspicious_editor":    "Document was created or edited using image manipulation software.",
    "metadata_mismatch":    "Document shows signs of modification after original creation.",
    "blank_author":         "Author information is missing from document metadata.",
    "encrypted_pdf":        "Document is encrypted, which may conceal tampered content.",
    "scanned_or_image_based": "Document appears to be scanned or image-based with no extractable text.",
    "low_text_content":     "Document has unusually low text content relative to its page count.",
    "font_anomaly":         "More than 3 font families detected — uncommon in genuine financial documents.",
    "font_size_anomaly":    "More than 5 unique font sizes found — may indicate content pasting or editing.",
    "sparse_text_layout":   "Multiple pages have very few text blocks — suggests deleted or replaced content.",
    "suspicious_spacing":   "One or more pages have large empty areas with very little text.",
}

SCORE_MAP = {
    "suspicious_editor":      25,
    "metadata_mismatch":      20,
    "blank_author":           10,
    "encrypted_pdf":          15,
    "scanned_or_image_based": 20,
    "low_text_content":       15,
    "font_anomaly":           15,
    "font_size_anomaly":      10,
    "sparse_text_layout":     15,
    "suspicious_spacing":     10,
}


def build_text_indicators(text_analysis: Optional[dict]) -> List[dict]:
    indicators = []
    if not text_analysis:
        return indicators

    if text_analysis.get("is_scanned_or_image_based"):
        indicators.append({
            "rule": "scanned_or_image_based",
            "score": SCORE_MAP["scanned_or_image_based"],
            "detail": "Document has no extractable text — likely scanned or image-based.",
        })
    elif text_analysis.get("warnings"):
        for w in text_analysis["warnings"]:
            if "unusually low" in w.lower():
                indicators.append({
                    "rule": "low_text_content",
                    "score": SCORE_MAP["low_text_content"],
                    "detail": "Document has very low text content relative to page count.",
                })
                break

    return indicators


def build_layout_indicators(layout_analysis: Optional[dict]) -> List[dict]:
    indicators = []
    if not layout_analysis:
        return indicators

    font_count = layout_analysis.get("font_count", 0)
    size_count = layout_analysis.get("font_size_count", 0)
    page_layouts = layout_analysis.get("page_layouts", [])
    warnings = layout_analysis.get("layout_warnings", [])

    if font_count > 3:
        indicators.append({
            "rule": "font_anomaly",
            "score": SCORE_MAP["font_anomaly"],
            "detail": f"More than 3 font families detected in the document ({font_count} found).",
        })

    if size_count > 5:
        indicators.append({
            "rule": "font_size_anomaly",
            "score": SCORE_MAP["font_size_anomaly"],
            "detail": f"More than 5 unique font sizes detected ({size_count} found).",
        })

    sparse = [p for p in page_layouts if p.get("text_blocks", 99) < 3]
    if len(sparse) > 0 and len(page_layouts) > 1:
        indicators.append({
            "rule": "sparse_text_layout",
            "score": SCORE_MAP["sparse_text_layout"],
            "detail": f"{len(sparse)} page(s) have very few text blocks — possible content deletion.",
        })

    suspicious = [p for p in page_layouts if p.get("suspicious_spacing")]
    if suspicious:
        indicators.append({
            "rule": "suspicious_spacing",
            "score": SCORE_MAP["suspicious_spacing"],
            "detail": f"{len(suspicious)} page(s) have large empty areas with minimal text.",
        })

    return indicators


def calculate_risk(
    metadata_indicators: List[dict],
    text_analysis: Optional[dict] = None,
    layout_analysis: Optional[dict] = None,
) -> dict:
    all_indicators = (
        metadata_indicators
        + build_text_indicators(text_analysis)
        + build_layout_indicators(layout_analysis)
    )

    total = sum(i["score"] for i in all_indicators)
    score = min(total, 100)

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