from typing import List, Optional

RISK_BUCKETS = [(0, 30, "CLEAN"), (31, 60, "SUSPICIOUS"), (61, 100, "HIGH")]

SCORE_MAP = {
    "suspicious_editor":      25,
    "metadata_mismatch":      20,
    "blank_author":            5,
    "encrypted_pdf":          15,
    "scanned_or_image_based": 20,
    "low_text_content":       10,
    "font_anomaly":           15,
    "font_size_anomaly":       8,
    "sparse_text_layout":     10,
    "suspicious_spacing":      5,
    "ela_tampering":          25,
    "ela_minor_inconsistency": 5,
}

EXPLANATION_MAP = {
    "suspicious_editor":       "Document was created or edited using image manipulation software — a risk signal.",
    "metadata_mismatch":       "Document was modified after original creation — possible tampering signal.",
    "blank_author":            "Author field is missing — weak signal, common in some auto-generated documents.",
    "encrypted_pdf":           "Document is encrypted — content cannot be fully verified.",
    "scanned_or_image_based":  "Document has no extractable text — likely scanned. OCR needed for full analysis.",
    "low_text_content":        "Document has unusually low text for its page count — possible content replacement.",
    "font_anomaly":            "More than 3 font families detected — uncommon in genuine financial documents.",
    "font_size_anomaly":       "More than 5 unique font sizes found — may indicate pasted or edited content.",
    "sparse_text_layout":      "Some pages have very few text blocks — possible deleted or replaced content.",
    "suspicious_spacing":      "Large empty areas detected on some pages — weak signal, review recommended.",
    "ela_tampering":           "Visual inconsistency detected via ELA — possible edited image regions (not conclusive).",
    "ela_minor_inconsistency": "Minor visual inconsistency via ELA — low-confidence signal only.",
}


def _text_indicators(ta: Optional[dict]) -> List[dict]:
    if not ta:
        return []
    if ta.get("is_scanned_or_image_based"):
        return [{"rule": "scanned_or_image_based", "score": SCORE_MAP["scanned_or_image_based"],
                 "detail": "Document has no extractable text — likely scanned or image-based."}]
    if any("unusually low" in w.lower() for w in ta.get("warnings", [])):
        return [{"rule": "low_text_content", "score": SCORE_MAP["low_text_content"],
                 "detail": "Document has low text content relative to its page count."}]
    return []


def _layout_indicators(la: Optional[dict]) -> List[dict]:
    if not la:
        return []
    out = []
    if la.get("font_count", 0) > 3:
        out.append({"rule": "font_anomaly", "score": SCORE_MAP["font_anomaly"],
                    "detail": f"More than 3 font families detected ({la['font_count']} found)."})
    if la.get("font_size_count", 0) > 5:
        out.append({"rule": "font_size_anomaly", "score": SCORE_MAP["font_size_anomaly"],
                    "detail": f"More than 5 unique font sizes detected ({la['font_size_count']} found)."})
    layouts = la.get("page_layouts", [])
    sparse = [p for p in layouts if p.get("text_blocks", 99) < 3]
    if sparse and len(layouts) > 1:
        out.append({"rule": "sparse_text_layout", "score": SCORE_MAP["sparse_text_layout"],
                    "detail": f"{len(sparse)} page(s) have very few text blocks."})
    suspicious = [p for p in layouts if p.get("suspicious_spacing")]
    if suspicious:
        out.append({"rule": "suspicious_spacing", "score": SCORE_MAP["suspicious_spacing"],
                    "detail": f"{len(suspicious)} page(s) have large empty areas with minimal text."})
    return out


def _ela_indicators(ela: Optional[dict]) -> List[dict]:
    if not ela or not ela.get("enabled"):
        return []
    score = ela.get("ela_score", 0)
    pages = ", ".join(str(p) for p in ela.get("suspicious_pages", []))
    if score >= 30:
        return [{"rule": "ela_tampering", "score": SCORE_MAP["ela_tampering"],
                 "detail": f"High recompression difference on page(s): {pages}. Review recommended."}]
    if score >= 10:
        return [{"rule": "ela_minor_inconsistency", "score": SCORE_MAP["ela_minor_inconsistency"],
                 "detail": f"Minor recompression inconsistency on page(s): {pages}. Low confidence."}]
    return []


def calculate_risk(
    metadata_indicators: List[dict],
    text_analysis: Optional[dict] = None,
    layout_analysis: Optional[dict] = None,
    ela_analysis: Optional[dict] = None,
) -> dict:
    seen: set = set()
    all_indicators = []
    for ind in (metadata_indicators + _text_indicators(text_analysis)
                + _layout_indicators(layout_analysis) + _ela_indicators(ela_analysis)):
        rule = ind.get("rule")
        if rule not in seen:
            seen.add(rule)
            # Normalize score against central SCORE_MAP
            if rule in SCORE_MAP:
                ind["score"] = SCORE_MAP[rule]
            all_indicators.append(ind)

    score = min(sum(i["score"] for i in all_indicators), 100)
    level = next((lbl for lo, hi, lbl in RISK_BUCKETS if lo <= score <= hi), "CLEAN")

    return {
        "risk_score": score,
        "risk_level": level,
        "indicators": all_indicators,
        "explanation": [EXPLANATION_MAP[i["rule"]] for i in all_indicators if i["rule"] in EXPLANATION_MAP],
    }