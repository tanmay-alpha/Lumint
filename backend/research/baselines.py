import re
from typing import Dict, Any, List

def url_keyword_baseline(url: str) -> Dict[str, Any]:
    url_lower = (url or "").lower()
    suspicious_keywords = ["login", "secure", "verify", "update", "chase", "paypal", "upi", "paytm", "gpay", "phonepe", "free", "gift", "prize"]
    
    found = [kw for kw in suspicious_keywords if kw in url_lower]
    
    if len(found) >= 2:
        return {
            "score": 85,
            "label": "HIGH",
            "reasons": [f"Multiple suspicious keywords detected: {found}"]
        }
    elif len(found) == 1:
        return {
            "score": 50,
            "label": "SUSPICIOUS",
            "reasons": [f"Suspicious keyword detected: {found}"]
        }
    return {
        "score": 10,
        "label": "CLEAN",
        "reasons": ["No suspicious keywords found"]
    }

def url_domain_length_baseline(url: str) -> Dict[str, Any]:
    # Extract domain/host simply
    clean_url = re.sub(r'^https?://', '', url or '')
    domain = clean_url.split('/')[0]
    
    length = len(domain)
    if length > 30:
        return {
            "score": 75,
            "label": "HIGH",
            "reasons": [f"Domain length ({length}) exceeds 30 characters"]
        }
    elif length > 20:
        return {
            "score": 45,
            "label": "SUSPICIOUS",
            "reasons": [f"Domain length ({length}) exceeds 20 characters"]
        }
    return {
        "score": 5,
        "label": "CLEAN",
        "reasons": [f"Domain length ({length}) is within normal limits"]
    }

def document_metadata_baseline(metadata: Dict[str, Any]) -> Dict[str, Any]:
    metadata_lower = {str(k).lower(): str(v).lower() for k, v in (metadata or {}).items()}
    
    producer = metadata_lower.get("producer", "")
    creator = metadata_lower.get("creator", "")
    editor_tool = metadata_lower.get("editor_tool", "")
    
    editing_signatures = ["photoshop", "gimp", "illustrator", "canvas", "edit", "acrobat pro"]
    
    found = []
    for sig in editing_signatures:
        if sig in producer or sig in creator or sig in editor_tool:
            found.append(sig)
            
    if found:
        return {
            "score": 80,
            "label": "HIGH",
            "reasons": [f"Image editing signature found: {found}"]
        }
        
    # Check for empty metadata fields
    if not producer and not creator:
        return {
            "score": 40,
            "label": "SUSPICIOUS",
            "reasons": ["Document has completely stripped creator/producer metadata"]
        }
        
    return {
        "score": 10,
        "label": "CLEAN",
        "reasons": ["Metadata appears authentic and untampered"]
    }

def upi_utr_format_baseline(utr: str) -> Dict[str, Any]:
    utr_clean = (utr or "").strip()
    
    if not utr_clean:
        return {
            "score": 90,
            "label": "HIGH",
            "reasons": ["UTR reference number is empty"]
        }
        
    if not utr_clean.isdigit():
        return {
            "score": 95,
            "label": "HIGH",
            "reasons": [f"UTR must be numeric, got: {utr_clean}"]
        }
        
    if len(utr_clean) != 12:
        return {
            "score": 85,
            "label": "HIGH",
            "reasons": [f"UTR must be exactly 12 digits, got length: {len(utr_clean)}"]
        }
        
    # Valid Indian banking UTRs for recent years usually start with 3, 4, 5, 6
    if not utr_clean.startswith(('3', '4', '5', '6')):
        return {
            "score": 40,
            "label": "SUSPICIOUS",
            "reasons": [f"UTR starts with unusual digit: {utr_clean[0]}"]
        }
        
    return {
        "score": 0,
        "label": "CLEAN",
        "reasons": ["UTR matches standard 12-digit UPI format"]
    }
