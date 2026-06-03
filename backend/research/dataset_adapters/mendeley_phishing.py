import hashlib
from pathlib import Path
from typing import Optional, List, Dict, Any

from research.dataset_manifest import DatasetManifest, DatasetRecord, DatasetType, DatasetSplit
from research.dataset_adapters.common import (
    DatasetAdapterResult,
    safe_read_csv,
    write_manifest_safe,
    resolve_input_path,
    normalize_binary_label
)

def convert_mendeley_phishing_to_manifest(
    input_path: Path,
    output_path: Path,
    url_column: str = "url",
    label_column: str = "label",
    split: str = "BENCHMARK",
    limit: Optional[int] = None,
) -> DatasetAdapterResult:
    """
    Converts a Mendeley or generic phishing dataset CSV to a Lumint DatasetManifest.
    """
    input_path = resolve_input_path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Mendeley source file not found: {input_path}")
        
    records_seen = 0
    records_written = 0
    skipped_records = 0
    warnings = []
    
    raw_records = safe_read_csv(input_path)
    
    records_to_process = raw_records
    if limit is not None:
        records_to_process = raw_records[:limit]
        
    records = []
    label_counts = {"CLEAN": 0, "SUSPICIOUS": 0, "HIGH": 0}
    
    for item in records_to_process:
        records_seen += 1
        
        url = item.get(url_column)
        if not url:
            # try to fallback to common names
            url = item.get("url") or item.get("URL") or item.get("link")
            if not url:
                skipped_records += 1
                continue
                
        raw_label = item.get(label_column)
        if raw_label is None:
            raw_label = item.get("label") or item.get("status") or item.get("class")
            if raw_label is None:
                skipped_records += 1
                continue
                
        # Map labels
        s_lbl = str(raw_label).strip().lower()
        if s_lbl in {"legitimate", "benign", "clean", "safe", "ok", "0"}:
            label = "CLEAN"
        elif s_lbl in {"phishing", "malicious", "fraud", "bad", "1", "high"}:
            label = "HIGH"
        elif s_lbl in {"suspicious", "warn", "warning"}:
            label = "SUSPICIOUS"
        else:
            # Use fallback normalize helper
            label = normalize_binary_label(raw_label)
            
        rec_id = f"rec_md_{hashlib.sha256(url.encode('utf-8')).hexdigest()[:12]}"
        
        # Meta contains other fields
        meta = {k: v for k, v in item.items() if k not in {url_column, label_column}}
        
        rec = DatasetRecord(
            id=rec_id,
            dataset_type=DatasetType.URL,
            path_or_value=url,
            label=label,
            split=DatasetSplit(split),
            source="mendeley_phishing",
            ground_truth_source="mendeley_csv",
            metadata=meta
        )
        
        records.append(rec)
        records_written += 1
        label_counts[label] = label_counts.get(label, 0) + 1
        
    manifest = DatasetManifest(
        name="Mendeley Phishing Ingested",
        version="1.0.0",
        records=records,
        notes=f"Converted from Mendeley CSV export: {input_path.name}"
    )
    
    res = write_manifest_safe(manifest, output_path)
    res.records_seen = records_seen
    res.records_written = records_written
    res.skipped_records = skipped_records
    res.warnings = warnings
    return res
