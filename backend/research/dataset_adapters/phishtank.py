import hashlib
from pathlib import Path
from typing import Optional, List, Dict, Any

from research.dataset_manifest import DatasetManifest, DatasetRecord, DatasetType, DatasetSplit
from research.dataset_adapters.common import (
    DatasetAdapterResult,
    safe_read_csv,
    safe_read_json,
    write_manifest_safe,
    resolve_input_path
)

def convert_phishtank_to_manifest(
    input_path: Path,
    output_path: Path,
    split: str = "BENCHMARK",
    limit: Optional[int] = None,
) -> DatasetAdapterResult:
    """
    Converts a locally downloaded PhishTank CSV or JSON export to a Lumint DatasetManifest.
    """
    input_path = resolve_input_path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"PhishTank source file not found: {input_path}")
        
    records_seen = 0
    records_written = 0
    skipped_records = 0
    warnings = []
    
    raw_records = []
    # Determine format based on suffix
    if input_path.suffix.lower() == ".json":
        data = safe_read_json(input_path)
        if isinstance(data, list):
            raw_records = data
        elif isinstance(data, dict):
            # sometimes json might be keyed by phish_id
            raw_records = list(data.values())
        else:
            raw_records = [data]
    else:
        # Default to CSV
        raw_records = safe_read_csv(input_path)
        
    records_to_process = raw_records
    if limit is not None:
        records_to_process = raw_records[:limit]
        
    records = []
    label_counts = {"CLEAN": 0, "SUSPICIOUS": 0, "HIGH": 0}
    
    for item in records_to_process:
        records_seen += 1
        
        # Look for url column or key
        url = item.get("url") or item.get("URL")
        if not url:
            skipped_records += 1
            continue
            
        phish_id = item.get("phish_id") or item.get("phish_detail_url") or str(records_seen)
        # Check verification
        verified = item.get("verified") or item.get("verification_status")
        online = item.get("online")
        
        # verified phishing -> HIGH, unverified/unknown -> SUSPICIOUS
        is_verified = False
        if verified is not None:
            v_str = str(verified).lower()
            if v_str in {"yes", "true", "1", "verified"}:
                is_verified = True
                
        label = "HIGH" if is_verified else "SUSPICIOUS"
        
        # Generate ID
        rec_id = f"rec_pt_{hashlib.sha256(str(phish_id).encode('utf-8')).hexdigest()[:12]}"
        
        rec = DatasetRecord(
            id=rec_id,
            dataset_type=DatasetType.URL,
            path_or_value=url,
            label=label,
            split=DatasetSplit(split),
            source="phishtank",
            ground_truth_source="phishtank_export",
            metadata={
                "phish_id": str(phish_id),
                "online": str(online) if online is not None else "unknown",
                "target": item.get("target") or "unknown"
            }
        )
        records.append(rec)
        records_written += 1
        label_counts[label] = label_counts.get(label, 0) + 1
        
    if label_counts.get("CLEAN", 0) == 0:
        warnings.append("Dataset is positive-heavy: no CLEAN records found.")
        
    manifest = DatasetManifest(
        name="PhishTank Ingested",
        version="1.0.0",
        records=records,
        notes=f"Converted from PhishTank export file: {input_path.name}"
    )
    
    res = write_manifest_safe(manifest, output_path)
    # Merge findings
    res.records_seen = records_seen
    res.records_written = records_written
    res.skipped_records = skipped_records
    res.warnings = warnings
    return res
