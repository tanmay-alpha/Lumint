from typing import List, Optional

RISK_BUCKETS = [
    (0, 30, "CLEAN"),
    (31, 60, "SUSPICIOUS"),
    (61, 100, "HIGH"),
]

# Per-rule weights for the rule-based score. Rule names match the
# `rule` field on TriggeredRule. Unknown rules contribute 0.
RISK_WEIGHTS = {
    "http_only": 20,
    "ip_as_domain": 30,
    "bank_name_typosquat": 35,
    "suspicious_keywords": 20,
    "excessive_subdomains": 15,
    "punycode_domain": 20,
    "long_domain": 10,
    "many_hyphens": 15,
    "suspicious_tld": 15,
    "homoglyph_attack": 30,
    "empty_url": 0,
}


def _bucket(score: int) -> str:
    for low, high, label in RISK_BUCKETS:
        if low <= score <= high:
            return label
    return "HIGH"


def score_url(
    triggered_rules: List[dict],
    whois: Optional[dict] = None,
    ssl: Optional[dict] = None,
) -> dict:
    """Combine rule-based signals with WHOIS/SSL network signals.

    Rule-based score is capped at 70; network signal at 30; total at 100.
    """
    rule_score = sum(
        RISK_WEIGHTS.get(r.get("rule", ""), 0) for r in triggered_rules
    )
    rule_score = min(rule_score, 70)

    network_score = 0
    if whois is None:
        network_score += 5
    else:
        age = whois.get("age_days")
        if isinstance(age, int):
            if age < 30:
                network_score += 20
            elif age < 90:
                network_score += 15
    if ssl is not None:
        if ssl.get("is_self_signed"):
            network_score += 25
        if ssl.get("is_expired"):
            network_score += 10
    network_score = min(network_score, 30)

    total = min(rule_score + network_score, 100)
    return {"risk_score": total, "risk_level": _bucket(total)}