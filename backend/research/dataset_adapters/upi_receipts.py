import csv
import json
import hashlib
from pathlib import Path
from typing import Optional, List, Dict, Any

from research.dataset_manifest import DatasetManifest, DatasetRecord, DatasetType, DatasetSplit
from research.dataset_adapters.common import (
    DatasetAdapterResult,
    write_manifest_safe,
    resolve_input_path
)
from research.anonymization import anonymize_text, anonymize_record_metadata

def convert_upi_receipts_to_manifest(
    input_dir: Path,
    labels_path: Optional[Path],
    output_path: Path,
    split: str = "BENCHMARK",
    limit: Optional[int] = None,
) -> DatasetAdapterResult:
    """
    Converts a local UPI screenshot dataset directory to a Lumint DatasetManifest.
    """
    input_dir = resolve_input_path(input_dir)
    if not input_dir.exists() or not input_dir.is_dir():
        raise FileNotFoundError(f"UPI receipts source directory not found: {input_dir}")
        
    records_seen = 0
    records_written = 0
    skipped_records = 0
    warnings = []
    
    # Load labels / OCR mapping if provided
    labels_mapping = {}
    if labels_path:
        labels_p = resolve_input_path(labels_path)
        if labels_p.exists():
            if labels_p.suffix.lower() == ".json":
                try:
                    with open(labels_p, "r", encoding="utf-8") as f:
                        labels_mapping = json.load(f)
                except Exception as e:
                    warnings.append(f"Failed to read labels JSON: {str(e)}")
            else:
                # Default to CSV with cols like file_name, ocr_text, label
                try:
                    with open(labels_p, "r", encoding="utf-8", errors="ignore") as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            fn = row.get("file_name") or row.get("filename")
                            if fn:
                                labels_mapping[fn] = row
                except Exception as e:
                    warnings.append(f"Failed to read labels CSV: {str(e)}")
        else:
            warnings.append(f"Labels file specified but not found: {labels_path}")
            
    # Traversal directories
    records = []
    
    # Let's collect all image files recursively under input_dir
    image_extensions = {".png", ".jpg", ".jpeg", ".webp"}
    file_list = []
    for filepath in input_dir.rglob("*"):
        if filepath.is_dir():
            continue
        if filepath.suffix.lower() in image_extensions:
            file_list.append(filepath)
            
    # Apply limit
    if limit is not None:
        file_list = file_list[:limit]
        
    for filepath in file_list:
        records_seen += 1
        
        # Determine parent folder name
        parent_name = filepath.parent.name
        
        # Mapping: genuine -> CLEAN, forged_* / tampered -> HIGH
        if parent_name == "genuine":
            label = "CLEAN"
        elif parent_name.startswith("forged_") or parent_name == "tampered":
            label = "HIGH"
        else:
            # Fallback based on labels mapping or default to SUSPICIOUS
            label = "SUSPICIOUS"
            
        # Get relative or absolute path to store
        path_str = str(filepath.resolve())
        
        # Load extra metadata from labels mapping
        meta = {
            "filename": filepath.name,
            "parent_folder": parent_name,
            "size_bytes": filepath.stat().st_size
        }
        
        # If mapping contains data for this file
        file_key = filepath.name
        ocr_text = ""
        if file_key in labels_mapping:
            label_info = labels_mapping[file_key]
            if isinstance(label_info, dict):
                # Anonymize raw OCR text and merge metadata
                for k, v in label_info.items():
                    if k not in {"file_name", "filename"}:
                        meta[k] = anonymize_text(str(v))
                # If explicit label is in metadata, respect it
                map_lbl = label_info.get("label") or label_info.get("Label")
                if map_lbl:
                    s_lbl = str(map_lbl).strip().lower()
                    if s_lbl in {"genuine", "clean", "benign", "safe", "0"}:
                        label = "CLEAN"
                    elif s_lbl in {"forged", "tampered", "fraud", "high", "1"}:
                        label = "HIGH"
            else:
                # If it's just raw string (e.g. ocr text)
                meta["ocr_text"] = anonymize_text(str(label_info))
                
        rec_id = f"rec_upi_{hashlib.sha256(path_str.encode('utf-8')).hexdigest()[:12]}"
        
        rec = DatasetRecord(
            id=rec_id,
            dataset_type=DatasetType.UPI_SCREENSHOT,
            path_or_value=path_str,
            label=label,
            split=DatasetSplit(split),
            source="upi_receipts",
            ground_truth_source="local_directory",
            metadata=meta
        )
        records.append(rec)
        records_written += 1
        
    manifest = DatasetManifest(
        name="UPI Receipts Ingested",
        version="1.0.0",
        records=records,
        notes=f"Converted from UPI directory: {input_dir.name}"
    )
    
    res = write_manifest_safe(manifest, output_path)
    res.records_seen = records_seen
    res.records_written = records_written
    res.skipped_records = skipped_records
    res.warnings = warnings
    return res
