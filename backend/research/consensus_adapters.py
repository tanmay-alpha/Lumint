import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class ConsensusProvider(BaseModel):
    name: str
    source: str  # "virustotal" | "urlscan" | "abuseipdb" | "fixture"
    available: bool
    reason: Optional[str] = None

class ConsensusResult(BaseModel):
    record_id: str
    provider: str
    target: str
    consensus_label: str  # "CLEAN" | "SUSPICIOUS" | "HIGH" | "UNKNOWN"
    confidence: float
    raw_score: Optional[float] = None
    evidence: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None

def normalize_consensus_label(value: Any) -> str:
    if value is None:
        return "UNKNOWN"
    if isinstance(value, bool):
        return "HIGH" if value else "CLEAN"
    if isinstance(value, (int, float)):
        if value == 1:
            return "HIGH"
        elif value == 0:
            return "CLEAN"
        return "UNKNOWN"
    
    val_str = str(value).strip().lower()
    if not val_str or val_str in ("unknown", "missing", "none", "null"):
        return "UNKNOWN"
    
    if val_str in ("malicious", "phishing", "high", "true", "1", "1.0", "likely_forged"):
        return "HIGH"
    if val_str in ("suspicious", "warning", "unsafe", "unknown_risk"):
        return "SUSPICIOUS"
    if val_str in ("benign", "clean", "safe", "false", "0", "0.0", "genuine"):
        return "CLEAN"
        
    # Substring search for robustness
    if "phish" in val_str or "malicious" in val_str or "high" in val_str or "forge" in val_str:
        return "HIGH"
    if "suspect" in val_str or "suspicious" in val_str or "warn" in val_str:
        return "SUSPICIOUS"
    if "clean" in val_str or "benign" in val_str or "safe" in val_str or "genuine" in val_str:
        return "CLEAN"
        
    return "UNKNOWN"

def create_consensus_result_from_fixture(record_id: str, target: str, fixture_item: Dict[str, Any]) -> ConsensusResult:
    label = normalize_consensus_label(fixture_item.get("consensus_label"))
    confidence = float(fixture_item.get("confidence", 1.0))
    raw_score = fixture_item.get("raw_score")
    if raw_score is not None:
        raw_score = float(raw_score)
    evidence = fixture_item.get("evidence", [])
    metadata = fixture_item.get("metadata", {})
    provider = fixture_item.get("provider", "fixture")
    
    return ConsensusResult(
        record_id=record_id,
        provider=provider,
        target=target,
        consensus_label=label,
        confidence=confidence,
        raw_score=raw_score,
        evidence=evidence,
        metadata=metadata,
        error=fixture_item.get("error")
    )

def fixture_consensus_lookup(record_id: str, fixture_path: Path) -> Optional[ConsensusResult]:
    try:
        p = Path(fixture_path)
        if not p.exists():
            return None
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        items = data.get("items", [])
        for item in items:
            if item.get("record_id") == record_id:
                target = item.get("target", "")
                # Ensure the provider is propagated from the parent file if not present in item
                if "provider" not in item:
                    item = item.copy()
                    item["provider"] = data.get("provider", "fixture")
                return create_consensus_result_from_fixture(record_id, target, item)
    except Exception:
        pass
    return None

def load_fixture_consensus(path: Path) -> Dict[str, ConsensusResult]:
    results = {}
    try:
        p = Path(path)
        if not p.exists():
            return results
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        items = data.get("items", [])
        provider = data.get("provider", "fixture")
        for item in items:
            r_id = item.get("record_id")
            if r_id:
                target = item.get("target", "")
                if "provider" not in item:
                    item = item.copy()
                    item["provider"] = provider
                results[r_id] = create_consensus_result_from_fixture(r_id, target, item)
    except Exception:
        pass
    return results

def get_available_providers() -> List[ConsensusProvider]:
    providers = []
    
    # VirusTotal
    vt_key = os.environ.get("VIRUSTOTAL_API_KEY", "").strip()
    providers.append(ConsensusProvider(
        name="VirusTotal",
        source="virustotal",
        available=bool(vt_key),
        reason=None if vt_key else "VIRUSTOTAL_API_KEY environment variable missing"
    ))
    
    # Urlscan
    us_key = os.environ.get("URLSCAN_API_KEY", "").strip()
    providers.append(ConsensusProvider(
        name="Urlscan.io",
        source="urlscan",
        available=bool(us_key),
        reason=None if us_key else "URLSCAN_API_KEY environment variable missing"
    ))
    
    # AbuseIPDB
    ab_key = os.environ.get("ABUSEIPDB_API_KEY", "").strip()
    providers.append(ConsensusProvider(
        name="AbuseIPDB",
        source="abuseipdb",
        available=bool(ab_key),
        reason=None if ab_key else "ABUSEIPDB_API_KEY environment variable missing"
    ))
    
    return providers
