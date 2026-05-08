from typing import List


RISK_BUCKETS = [
    (0, 30, "CLEAN"),
    (31, 60, "SUSPICIOUS"),
    (61, 100, "HIGH"),
]

EXPLANATION_MAP = {
    "suspicious_editor": "Document was created or edited using image manipulation software.",
    "metadata_mismatch": "The document shows signs of modification after creation.",
    "blank_author": "Author information is missing from document metadata.",
    "encrypted_pdf": "Document is encrypted, which may be used to hide tampered content.",
}


def calculate_risk(indicators: List[dict]) -> dict:
    total = sum(i["score"] for i in indicators)
    score = min(total, 100)

    level = "CLEAN"
    for low, high, label in RISK_BUCKETS:
        if low <= score <= high:
            level = label
            break

    explanation = [
        EXPLANATION_MAP[i["rule"]]
        for i in indicators
        if i["rule"] in EXPLANATION_MAP
    ]

    return {
        "risk_score": score,
        "risk_level": level,
        "explanation": explanation,
    }