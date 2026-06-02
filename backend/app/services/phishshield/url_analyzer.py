import re
import ipaddress
from urllib.parse import urlparse, unquote
from typing import List

KNOWN_BANKS = [
    "hdfcbank", "sbi", "icicibank", "axisbank", "canarabank",
    "kotak", "yesbank", "pnb", "bankofbaroda",
]

OFFICIAL_BANK_DOMAINS = {
    "hdfcbank.com", "sbi.co.in", "onlinesbi.sbi", "icicibank.com",
    "axisbank.com", "canarabank.com", "kotak.com", "yesbank.in",
    "pnbindia.in", "bankofbaroda.in",
}

SUSPICIOUS_KEYWORDS = [
    "login", "verify", "kyc", "update", "otp", "password",
    "secure", "account", "unlock", "blocked", "urgent", "netbanking",
]

SUSPICIOUS_TLDS = {".zip", ".click", ".top", ".xyz", ".tk", ".ml", ".ga", ".cf"}

# AI feature: extended homoglyph/lookalike pattern map for zero-day phishing detection
HOMOGLYPHS = {"0": "o", "1": "l", "3": "e", "4": "a", "5": "s", "6": "b", "8": "b", "@": "a"}


def _normalize(url: str) -> str:
    url = (url or "").strip()
    if not url:
        return ""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url


def _extract_domain(parsed) -> str:
    return (parsed.netloc or parsed.path).split(":")[0].lower().strip().removeprefix("www.")


def _is_ip(domain: str) -> bool:
    try:
        ipaddress.ip_address(domain)
        return True
    except ValueError:
        return False


def _edit_distance(a: str, b: str) -> int:
    if len(a) < len(b):
        a, b = b, a
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a):
        curr = [i + 1]
        for j, cb in enumerate(b):
            curr.append(min(prev[j + 1] + 1, curr[j] + 1, prev[j] + (ca != cb)))
        prev = curr
    return prev[-1]


def _is_official(domain: str) -> bool:
    d = domain.lower().strip().removeprefix("www.")
    return any(d == od or d.endswith("." + od) for od in OFFICIAL_BANK_DOMAINS)


def _domain_root(domain: str) -> str:
    d = domain.lower().strip().removeprefix("www.")
    if _is_ip(d):
        return d
    parts = d.split(".")
    root = parts[0] if len(parts) <= 2 else "".join(parts[:-1])
    return re.sub(r"[^a-z0-9]", "", root)


def _normalize_homoglyphs(text: str) -> str:
    """AI feature: translate digit/homoglyph substitutions to base chars for better detection."""
    return "".join(HOMOGLYPHS.get(c, c) for c in text.lower())


def _bank_similarity(domain: str) -> List[dict]:
    if _is_official(domain):
        return []
    root = _domain_root(domain)
    root_norm = _normalize_homoglyphs(root)
    best: dict = {}
    for bank in KNOWN_BANKS:
        if not root:
            continue
        # Exact substring or homoglyph-normalized match
        if (bank in root and root != bank) or (bank in root_norm and root_norm != bank):
            best[bank] = max(best.get(bank, 0), 0.95)
            continue
        dist = _edit_distance(root, bank)
        mx = max(len(root), len(bank))
        sim = round(1 - dist / mx, 4) if mx else 0
        if sim >= 0.55 and root != bank:
            best[bank] = max(best.get(bank, 0), sim)
    return sorted([{"bank": b, "similarity": s} for b, s in best.items()], key=lambda x: x["similarity"], reverse=True)


def _count_subdomains(domain: str) -> int:
    return max(0, len(domain.lower().strip().removeprefix("www.").split(".")) - 2)


def _get_tld(domain: str) -> str:
    parts = domain.lower().strip().split(".")
    return "." + parts[-1] if parts else ""


def analyze_url(raw_url: str) -> dict:
    normalized = _normalize(raw_url)
    if not normalized:
        return {
            "normalized_url": "", "domain": "",
            "triggered_rules": [{"rule": "empty_url", "score": 0, "detail": "URL is empty."}],
            "domain_similarity_matches": [], "top_keywords": [], "is_official_bank_domain": False,
        }

    parsed = urlparse(normalized)
    domain = _extract_domain(parsed)
    path = unquote((parsed.path or "") + ("?" + parsed.query if parsed.query else "")).lower()
    full = f"{domain}/{path}"
    is_official = _is_official(domain)
    rules = []

    if parsed.scheme == "http":
        rules.append({"rule": "http_only", "score": 20, "detail": "URL uses HTTP instead of HTTPS — no encryption."})

    if _is_ip(domain):
        rules.append({"rule": "ip_as_domain", "score": 30, "detail": f"Domain is a raw IP address: {domain}."})

    matches = _bank_similarity(domain)
    if matches:
        best = matches[0]
        rules.append({"rule": "bank_name_typosquat", "score": 35,
                       "detail": f"Domain resembles known bank '{best['bank']}' (similarity={best['similarity']})."})

    found_kw = [kw for kw in SUSPICIOUS_KEYWORDS if kw in full]
    if found_kw and not is_official:
        rules.append({"rule": "suspicious_keywords", "score": 20,
                       "detail": f"Suspicious keywords detected: {', '.join(found_kw[:5])}."})

    if _count_subdomains(domain) > 3 and not is_official:
        rules.append({"rule": "excessive_subdomains", "score": 15,
                       "detail": f"Domain has {_count_subdomains(domain)} subdomain levels."})

    if "xn--" in domain:
        rules.append({"rule": "punycode_domain", "score": 20, "detail": "Domain contains punycode — possible Unicode spoofing."})

    if len(domain) > 45 and not is_official:
        rules.append({"rule": "long_domain", "score": 10, "detail": f"Domain is unusually long ({len(domain)} chars)."})

    if domain.count("-") >= 3 and not is_official:
        rules.append({"rule": "many_hyphens", "score": 15,
                       "detail": f"Domain contains {domain.count('-')} hyphens — common in phishing domains."})

    tld = _get_tld(domain)
    if tld in SUSPICIOUS_TLDS and not is_official:
        rules.append({"rule": "suspicious_tld", "score": 15, "detail": f"TLD '{tld}' is commonly associated with phishing."})

    # AI feature: homoglyph attack detection
    root_norm = _normalize_homoglyphs(_domain_root(domain))
    for bank in KNOWN_BANKS:
        if bank in root_norm and not is_official and not any(r["rule"] == "bank_name_typosquat" for r in rules):
            rules.append({"rule": "homoglyph_attack", "score": 30,
                           "detail": f"Domain may use digit/character substitution to impersonate '{bank}'."})
            break

    return {
        "normalized_url": normalized,
        "domain": domain,
        "triggered_rules": rules,
        "domain_similarity_matches": matches,
        "top_keywords": found_kw,
        "is_official_bank_domain": is_official,
    }