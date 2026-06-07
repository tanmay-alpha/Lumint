"""
Feature Name Mapping Dictionary
Maps technical ML feature names to human-readable names for display in Research Center.
"""

PHISH_SHIELD_NAMES = {
    "tfidf_p:": "Path separator char-ngram",
    "tfidf_p:/": "Double slash pattern",
    "tfidf_p://": "Protocol separator",
    "tfidf_tp:": "Triple path pattern",
    "tfidf_tp:/": "Path protocol combo",
    "tfidf_ttp:": "TTP character n-gram",
    "tfidf_ps:": "HTTPS indicator n-gram",
    "tfidf_ps:/": "Secure protocol pattern",
    "tfidf_s:": "Secure indicator",
    "has_https": "HTTPS presence",
    "url_entropy": "URL character entropy",
    "num_dots": "Subdomain dot count",
    "domain_length": "Domain name length",
    "tld_suspicious": "Suspicious TLD flag",
    "has_ip_address": "IP-format hostname",
    "contains_brand_keyword": "Brand keyword match",
    "digit_ratio": "Digit character ratio",
    "url_length": "Full URL length",
    "num_subdomains": "Number of subdomains",
    "special_char_count": "Special character count",
}

DOC_SHIELD_NAMES = {
    "metadata_anomaly_score": "Metadata anomaly score",
    "ela_max": "Maximum ELA error level",
    "ela_std": "ELA variance",
    "ela_mean": "Average ELA density",
    "ela_high_pixel_ratio": "High-error pixel ratio",
    "creation_to_mod_delta_days": "Creation-modification gap",
    "font_count": "Font variety count",
    "page_count": "Page count",
    "file_size_kb": "File size (KB)",
    "image_count": "Embedded image count",
    "has_exif": "EXIF metadata presence",
    "has_author": "Author metadata",
    "has_mod_date": "Modification date",
}

UPI_SHIELD_NAMES = {
    "ocr_confidence": "OCR confidence score",
    "forgery_score_heuristic": "Forgery heuristic score",
    "font_consistency": "Font consistency",
    "brand_color_match": "Brand color match",
    "utr_format_valid": "UTR format validity",
    "amount_plausibility": "Amount plausibility",
    "sender_vpa_valid": "Sender VPA format",
    "receiver_vpa_valid": "Receiver VPA format",
}


def get_readable_feature_name(module: str, technical_name: str) -> str:
    """
    Map a technical feature name to a human-readable display name.

    Args:
        module: "phish", "doc", or "upi"
        technical_name: The raw feature name from the model/SHAP

    Returns:
        Human-readable feature name
    """
    name_map = {
        "phish": PHISH_SHIELD_NAMES,
        "doc": DOC_SHIELD_NAMES,
        "upi": UPI_SHIELD_NAMES,
    }

    mapping = name_map.get(module, {})

    # Direct lookup
    if technical_name in mapping:
        return mapping[technical_name]

    # Try partial match (feature prefixes)
    for key, readable in mapping.items():
        if technical_name.startswith(key):
            return readable

    # Fallback: clean up the name
    cleaned = technical_name.replace("_", " ").replace("-", " ").title()
    return cleaned


__all__ = [
    "PHISH_SHIELD_NAMES",
    "DOC_SHIELD_NAMES",
    "UPI_SHIELD_NAMES",
    "get_readable_feature_name",
]