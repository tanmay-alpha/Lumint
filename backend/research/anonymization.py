import re
import hashlib
from urllib.parse import urlparse
from typing import Dict, Any

# Regular expressions for common sensitive indicators
EMAIL_REGEX = re.compile(r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b')
PHONE_REGEX = re.compile(r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b|\b\d{10}\b')
# UPI ID: string@bankname or similar handle
UPI_ID_REGEX = re.compile(r'\b[a-zA-Z0-9.\-_]+@[a-zA-Z0-9]+\b')
# UTR: usually a 12-digit reference number for transactions in India
UTR_REGEX = re.compile(r'\b\d{12}\b')
# Amount: typically Rs. 500, INR 1000, Rs.500.00, etc.
AMOUNT_REGEX = re.compile(r'\b(?:Rs\.?|INR|USD|\$)\s*\d+(?:\.\d{2})?\b')

def hash_identifier(value: str, salt: str = "lumint") -> str:
    """
    Deterministically hashes a string identifier with a salt using SHA-256.
    Returns the first 16 characters of the hex digest.
    """
    if not value:
        return ""
    hasher = hashlib.sha256()
    hasher.update((value + salt).encode('utf-8'))
    return hasher.hexdigest()[:16]

def redact_emails(text: str) -> str:
    """
    Replaces email addresses with a deterministic hash format: <EMAIL_HASH:xxxx>
    """
    def replace_email(match):
        email = match.group(0)
        h = hash_identifier(email.lower())
        return f"<EMAIL_HASH:{h}>"
    return EMAIL_REGEX.sub(replace_email, text)

def redact_phone_numbers(text: str) -> str:
    """
    Replaces phone numbers with <PHONE_HASH:xxxx>
    """
    def replace_phone(match):
        phone = match.group(0)
        # remove spacing/special chars to normalize phone hash
        normalized_phone = re.sub(r'[-.\s\(\)\+]', '', phone)
        h = hash_identifier(normalized_phone)
        return f"<PHONE_HASH:{h}>"
    return PHONE_REGEX.sub(replace_phone, text)

def redact_upi_ids(text: str) -> str:
    """
    Replaces UPI IDs with <UPI_ID_HASH:xxxx>
    """
    def replace_upi(match):
        upi = match.group(0)
        h = hash_identifier(upi.lower())
        return f"<UPI_ID_HASH:{h}>"
    return UPI_ID_REGEX.sub(replace_upi, text)

def redact_utr_numbers(text: str) -> str:
    """
    Replaces 12-digit UTR numbers with <UTR_HASH:xxxx>
    """
    def replace_utr(match):
        utr = match.group(0)
        h = hash_identifier(utr)
        return f"<UTR_HASH:{h}>"
    return UTR_REGEX.sub(replace_utr, text)

def redact_amounts(text: str) -> str:
    """
    Replaces amounts with <AMOUNT>
    """
    return AMOUNT_REGEX.sub("<AMOUNT>", text)

def redact_urls(text: str, keep_domain: bool = True) -> str:
    """
    Redacts URL path and query parameters while keeping the domain if specified.
    """
    # Regex to find URLs in text
    url_pattern = re.compile(r'https?://[^\s/$.?#].[^\s]*', re.IGNORECASE)
    
    def replace_url(match):
        url = match.group(0)
        parsed = urlparse(url)
        if keep_domain and parsed.netloc:
            # We keep the scheme and netloc (domain) and append a hash of the full URL path/query
            full_path = parsed.path + parsed.query + parsed.fragment
            if full_path:
                h = hash_identifier(url)
                return f"{parsed.scheme}://{parsed.netloc}/<PATH_HASH:{h}>"
            else:
                return f"{parsed.scheme}://{parsed.netloc}"
        else:
            h = hash_identifier(url)
            return f"<URL_HASH:{h}>"
            
    return url_pattern.sub(replace_url, text)

def anonymize_text(text: str) -> str:
    """
    Runs all text redaction layers in sequence.
    """
    if not text:
        return ""
    text = redact_emails(text)
    text = redact_utr_numbers(text)
    text = redact_phone_numbers(text)
    text = redact_upi_ids(text)
    text = redact_amounts(text)
    text = redact_urls(text, keep_domain=True)
    return text

def anonymize_record_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively anonymizes any string values inside a dictionary.
    """
    anonymized = {}
    for k, v in metadata.items():
        if isinstance(v, str):
            anonymized[k] = anonymize_text(v)
        elif isinstance(v, dict):
            anonymized[k] = anonymize_record_metadata(v)
        elif isinstance(v, list):
            new_list = []
            for item in v:
                if isinstance(item, str):
                    new_list.append(anonymize_text(item))
                elif isinstance(item, dict):
                    new_list.append(anonymize_record_metadata(item))
                else:
                    new_list.append(item)
            anonymized[k] = new_list
        else:
            anonymized[k] = v
    return anonymized
