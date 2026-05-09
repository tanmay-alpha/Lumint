import re
import ipaddress
from urllib.parse import urlparse, unquote
from typing import List


KNOWN_BANKS = [
    "hdfcbank",
    "sbi",
    "icicibank",
    "axisbank",
    "canarabank",
    "kotak",
    "yesbank",
    "pnb",
    "bankofbaroda",
]

OFFICIAL_BANK_DOMAINS = {
    "hdfcbank.com",
    "sbi.co.in",
    "onlinesbi.sbi",
    "icicibank.com",
    "axisbank.com",
    "canarabank.com",
    "kotak.com",
    "yesbank.in",
    "pnbindia.in",
    "bankofbaroda.in",
}

SUSPICIOUS_KEYWORDS = [
    "login",
    "verify",
    "kyc",
    "update",
    "otp",
    "password",
    "secure",
    "account",
    "unlock",
    "blocked",
    "urgent",
    "netbanking",
]

SUSPICIOUS_TLDS = {".zip", ".click", ".top", ".xyz", ".tk", ".ml", ".ga", ".cf"}


def _normalize(url: str) -> str:
    url = (url or "").strip()

    if not url:
        return ""

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    return url


def _extract_domain(parsed) -> str:
    domain = (parsed.netloc or parsed.path).split(":")[0].lower().strip()
    return domain.removeprefix("www.")


def _is_ip(domain: str) -> bool:
    try:
        ipaddress.ip_address(domain)
        return True
    except ValueError:
        return False


def _edit_distance(a: str, b: str) -> int:
    if len(a) < len(b):
        a, b = b, a

    previous_row = list(range(len(b) + 1))

    for i, char_a in enumerate(a):
        current_row = [i + 1]

        for j, char_b in enumerate(b):
            insert_cost = previous_row[j + 1] + 1
            delete_cost = current_row[j] + 1
            replace_cost = previous_row[j] + (char_a != char_b)

            current_row.append(min(insert_cost, delete_cost, replace_cost))

        previous_row = current_row

    return previous_row[-1]


def _is_official_bank_domain(domain: str) -> bool:
    domain = domain.lower().strip().removeprefix("www.")

    for official_domain in OFFICIAL_BANK_DOMAINS:
        if domain == official_domain:
            return True

        # Allow real subdomains like netbanking.hdfcbank.com
        if domain.endswith("." + official_domain):
            return True

    return False


def _domain_root_for_similarity(domain: str) -> str:
    """
    Convert suspicious-looking domains into a compact comparable root.

    Examples:
    - hdfc-bank-verify-kyc.com -> hdfcbankverifykyc
    - sbi-netbanking-login.co -> sbinetbankinglogin
    - netbanking.hdfcbank.com -> netbankinghdfcbank
    """
    domain = domain.lower().strip().removeprefix("www.")

    if _is_ip(domain):
        return domain

    parts = domain.split(".")

    if len(parts) <= 2:
        root = parts[0]
    else:
        root = "".join(parts[:-1])

    return re.sub(r"[^a-z0-9]", "", root)


def _bank_similarity(domain: str) -> List[dict]:
    """
    Return similarity matches only for non-official domains.

    Official bank domains must not be flagged as typosquats:
    - hdfcbank.com -> no match
    - netbanking.hdfcbank.com -> no match

    Fake domains should still match:
    - hdfc-bank-verify-kyc.com -> hdfcbank
    - sbi-netbanking-login.co -> sbi
    """
    if _is_official_bank_domain(domain):
        return []

    root_clean = _domain_root_for_similarity(domain)

    matches = []

    for bank in KNOWN_BANKS:
        if not root_clean:
            continue

        # Strong phishing indicator: bank name embedded inside a non-official domain.
        if bank in root_clean and root_clean != bank:
            matches.append({"bank": bank, "similarity": 0.95})
            continue

        distance = _edit_distance(root_clean, bank)
        max_len = max(len(root_clean), len(bank))
        similarity = round(1 - distance / max_len, 4) if max_len > 0 else 0

        if similarity >= 0.55 and root_clean != bank:
            matches.append({"bank": bank, "similarity": similarity})

    # Deduplicate by bank, keeping strongest match.
    best_by_bank = {}
    for match in matches:
        bank = match["bank"]
        if bank not in best_by_bank or match["similarity"] > best_by_bank[bank]["similarity"]:
            best_by_bank[bank] = match

    return sorted(best_by_bank.values(), key=lambda item: item["similarity"], reverse=True)


def _count_subdomains(domain: str) -> int:
    domain = domain.lower().strip().removeprefix("www.")
    return max(0, len(domain.split(".")) - 2)


def _get_tld(domain: str) -> str:
    parts = domain.lower().strip().split(".")
    return "." + parts[-1] if parts else ""


def analyze_url(raw_url: str) -> dict:
    normalized = _normalize(raw_url)

    if not normalized:
        return {
            "normalized_url": "",
            "domain": "",
            "triggered_rules": [
                {
                    "rule": "empty_url",
                    "score": 0,
                    "detail": "URL is empty.",
                }
            ],
            "domain_similarity_matches": [],
            "top_keywords": [],
            "is_official_bank_domain": False,
        }

    parsed = urlparse(normalized)
    domain = _extract_domain(parsed)
    path = unquote((parsed.path or "") + ("?" + parsed.query if parsed.query else "")).lower()
    full_lower = f"{domain}/{path}".lower()

    is_official_domain = _is_official_bank_domain(domain)
    rules = []

    # Scheme check
    if parsed.scheme == "http":
        rules.append(
            {
                "rule": "http_only",
                "score": 20,
                "detail": "URL uses HTTP instead of HTTPS — no encryption.",
            }
        )

    # IP as domain
    if _is_ip(domain):
        rules.append(
            {
                "rule": "ip_as_domain",
                "score": 30,
                "detail": f"Domain is a raw IP address: {domain}.",
            }
        )

    # Bank impersonation + typosquat
    matches = _bank_similarity(domain)

    if matches:
        best = matches[0]
        rules.append(
            {
                "rule": "bank_name_typosquat",
                "score": 35,
                "detail": (
                    f"Domain is similar to known bank '{best['bank']}' "
                    f"(similarity={best['similarity']})."
                ),
            }
        )

    # Suspicious keywords
    # Do not punish official domains for normal banking words like login/netbanking.
    found_keywords = [kw for kw in SUSPICIOUS_KEYWORDS if kw in full_lower]

    if found_keywords and not is_official_domain:
        rules.append(
            {
                "rule": "suspicious_keywords",
                "score": 20,
                "detail": f"Suspicious banking keywords detected: {', '.join(found_keywords[:5])}.",
            }
        )

    # Excessive subdomains
    subdomain_count = _count_subdomains(domain)

    if subdomain_count > 3 and not is_official_domain:
        rules.append(
            {
                "rule": "excessive_subdomains",
                "score": 15,
                "detail": f"Domain has {subdomain_count} subdomain levels — unusually deep.",
            }
        )

    # Punycode
    if "xn--" in domain:
        rules.append(
            {
                "rule": "punycode_domain",
                "score": 20,
                "detail": "Domain contains punycode encoding — possible Unicode spoofing.",
            }
        )

    # Long domain
    if len(domain) > 45 and not is_official_domain:
        rules.append(
            {
                "rule": "long_domain",
                "score": 10,
                "detail": f"Domain is unusually long ({len(domain)} chars).",
            }
        )

    # Many hyphens
    hyphen_count = domain.count("-")

    if hyphen_count >= 3 and not is_official_domain:
        rules.append(
            {
                "rule": "many_hyphens",
                "score": 15,
                "detail": f"Domain contains {hyphen_count} hyphens — common in phishing domains.",
            }
        )

    # Suspicious TLD
    tld = _get_tld(domain)

    if tld in SUSPICIOUS_TLDS and not is_official_domain:
        rules.append(
            {
                "rule": "suspicious_tld",
                "score": 15,
                "detail": f"TLD '{tld}' is commonly associated with phishing sites.",
            }
        )

    return {
        "normalized_url": normalized,
        "domain": domain,
        "triggered_rules": rules,
        "domain_similarity_matches": matches,
        "top_keywords": found_keywords,
        "is_official_bank_domain": is_official_domain,
    }