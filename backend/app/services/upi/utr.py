import re
from typing import List, Dict, Optional, Any

def normalize_utr(value: str) -> str:
    """
    Remove whitespace, dashes, and other non-alphanumeric chars.
    """
    if not value:
        return ""
    # Strip common symbols
    return re.sub(r'[^a-zA-Z0-9]', '', value).strip()

def classify_utr(value: str) -> Dict[str, Any]:
    """
    Classify the UTR/Txn ID format based on length and characters.
    Returns format details: format, valid, confidence, evidence.
    """
    norm = normalize_utr(value)
    if not norm:
        return {
            "format": "invalid",
            "valid": False,
            "confidence": 0.0,
            "evidence": "Empty transaction reference"
        }
        
    length = len(norm)
    
    # 1. PhonePe style: exactly 12 numeric digits
    if norm.isdigit() and length == 12:
        return {
            "format": "phonepe_numeric_12",
            "valid": True,
            "confidence": 0.95,
            "evidence": f"Matches standard India UPI 12-digit numeric UTR format (e.g. PhonePe)."
        }
        
    # 2. Paytm style: starts with 'T' followed by 10-17 digits, or begins with Paytm-specific prefix
    if norm.startswith('T') and norm[1:].isdigit() and 10 <= length <= 18:
        return {
            "format": "paytm_t_prefix",
            "valid": True,
            "confidence": 0.90,
            "evidence": "Matches Paytm 'T'-prefix transaction reference format."
        }
        
    # 3. Google Pay style: alphanumeric reference of length 10-18
    # Note: GPay often has UTR and a transaction ID. If alphanumeric and 10-18 chars, it fits.
    if 10 <= length <= 18:
        # Check if it has both letters and numbers, or is numeric of non-12 length
        is_alphanumeric = not norm.isdigit() and not norm.isalpha()
        if is_alphanumeric or (norm.isdigit() and length != 12):
            return {
                "format": "gpay_alphanumeric",
                "valid": True,
                "confidence": 0.85,
                "evidence": "Matches Google Pay alphanumeric transaction reference format."
            }
            
    # 4. Generic but potentially valid UPI/UTR format (numeric but 10-18 length, or general alphanumeric)
    if 10 <= length <= 18:
        return {
            "format": "generic",
            "valid": True,
            "confidence": 0.70,
            "evidence": "Generic alphanumeric transaction ID within length boundaries."
        }
        
    # 5. Invalid
    return {
        "format": "invalid",
        "valid": False,
        "confidence": 0.10,
        "evidence": f"Reference length ({length}) or content is outside normal Indian UPI boundaries (10-18 alphanumeric)."
    }

def validate_utr(value: str, app_hint: Optional[str] = None) -> Dict[str, Any]:
    """
    Validate and return UTR details, taking into account any app hint (PhonePe, GPay, Paytm).
    """
    norm = normalize_utr(value)
    classification = classify_utr(norm)
    
    # Apply app hint checks
    if app_hint:
        app_lower = app_hint.lower()
        fmt = classification["format"]
        
        if "phonepe" in app_lower and fmt != "phonepe_numeric_12":
            # PhonePe app with non-12-digit UTR is suspicious
            classification["valid"] = False
            classification["confidence"] = min(classification["confidence"], 0.40)
            classification["evidence"] += " Mismatch: PhonePe receipt should contain exactly 12 numeric digits UTR."
        elif "gpay" in app_lower or "google pay" in app_lower:
            # GPay can be alphanumeric or numeric
            pass
        elif "paytm" in app_lower and fmt != "paytm_t_prefix" and not (fmt == "phonepe_numeric_12"):
            # Paytm receipts typically use Paytm-specific references or 12 digit UTRs
            pass
            
    return {
        "value": value,
        "normalized": norm,
        "format": classification["format"],
        "valid": classification["valid"],
        "confidence": classification["confidence"],
        "evidence": classification["evidence"]
    }

def extract_utr_candidates(text: str) -> List[Dict[str, Any]]:
    """
    Find candidate UTRs or Transaction IDs in receipt text.
    Uses regex matching typical prefixes and patterns.
    """
    candidates = []
    text_clean = text.replace('\n', ' ')
    
    # 1. Regex looking for label prefixes
    # UTR, UPI Ref, Transaction ID, Ref No, UPI Transaction ID, Bank Reference ID, Txn ID
    pattern = r'(?i)(?:utr|upi\s+ref|transaction\s+id|txn\s+id|ref\s+no|upi\s+transaction\s+id|bank\s+reference\s+id)\s*[:#-]?\s*([a-zA-Z0-9]{10,18})'
    for match in re.finditer(pattern, text_clean):
        val = match.group(1)
        val_norm = normalize_utr(val)
        if val_norm and val_norm not in [c["normalized"] for c in candidates]:
            val_details = validate_utr(val)
            candidates.append(val_details)
            
    # 2. Look for standalone 12-digit numeric codes that might be UTRs (if not already matched)
    digit_pattern = r'\b(\d{12})\b'
    for match in re.finditer(digit_pattern, text_clean):
        val = match.group(1)
        val_norm = normalize_utr(val)
        if val_norm and val_norm not in [c["normalized"] for c in candidates]:
            val_details = validate_utr(val)
            candidates.append(val_details)

    # 3. Look for standalone Paytm 'T' transaction references
    paytm_pattern = r'\b(T\d{10,17})\b'
    for match in re.finditer(paytm_pattern, text_clean):
        val = match.group(1)
        val_norm = normalize_utr(val)
        if val_norm and val_norm not in [c["normalized"] for c in candidates]:
            val_details = validate_utr(val)
            candidates.append(val_details)
            
    return candidates
