import csv
import json
import uuid
import hashlib
from pathlib import Path
from enum import Enum
from typing import Tuple, Dict, Any, List, Optional
from pydantic import BaseModel, Field

from research.dataset_manifest import (
    DatasetManifest,
    DatasetRecord,
    DatasetType,
    DatasetSplit,
    save_manifest
)
from research.anonymization import anonymize_text, anonymize_record_metadata

class IngestionSourceType(str, Enum):
    CSV = "CSV"
    JSON = "JSON"
    DIRECTORY = "DIRECTORY"
    MANIFEST = "MANIFEST"

class IngestionConfig(BaseModel):
    source_path: str
    source_type: IngestionSourceType
    dataset_type: DatasetType
    label_column: Optional[str] = None
    value_column: Optional[str] = None
    split: DatasetSplit = DatasetSplit.BENCHMARK
    anonymize: bool = True
    output_manifest_path: str

class IngestionSummary(BaseModel):
    records_seen: int = 0
    records_written: int = 0
    skipped_records: int = 0
    label_counts: Dict[str, int] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)

def validate_label(label: str) -> str:
    """
    Normalizes input labels to standard uppercase labels: CLEAN, SUSPICIOUS, HIGH.
    Raises ValueError for unsupported labels.
    """
    clean_label = label.strip().upper()
    valid_labels = {"CLEAN", "SUSPICIOUS", "HIGH"}
    if clean_label in valid_labels:
        return clean_label
    
    # Check for close matches or aliases
    if clean_label in {"BENIGN", "SAFE", "OK", "0"}:
        return "CLEAN"
    if clean_label in {"MALICIOUS", "FRAUD", "BAD", "1", "FRAUDULENT"}:
        return "HIGH"
    if clean_label in {"WARN", "WARNING", "MEDIUM"}:
        return "SUSPICIOUS"
        
    raise ValueError(f"Invalid label: {label}. Must be one of: {valid_labels}")

def infer_dataset_type_from_path(path: Path) -> Optional[str]:
    """
    Infers the DatasetType based on file extension or filename.
    """
    ext = path.suffix.lower()
    if ext in {".png", ".jpg", ".jpeg", ".webp"}:
        return DatasetType.UPI_SCREENSHOT.value
    if ext in {".pdf", ".doc", ".docx", ".txt"}:
        return DatasetType.DOCUMENT.value
    return None

def build_dataset_record(
    record_id: str,
    dataset_type: DatasetType,
    path_or_value: str,
    label: str,
    split: DatasetSplit,
    source: str,
    anonymize: bool = True,
    ground_truth_source: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> DatasetRecord:
    """
    Constructs a DatasetRecord while optionally applying text and metadata anonymization.
    """
    processed_val = path_or_value
    processed_meta = metadata or {}
    
    if anonymize:
        # If dataset_type is URL or text-based, anonymize the text value
        if dataset_type == DatasetType.URL or not path_or_value.endswith(('.png', '.jpg', '.jpeg', '.pdf', '.webp')):
            processed_val = anonymize_text(path_or_value)
        processed_meta = anonymize_record_metadata(processed_meta)
        
    normalized_label = validate_label(label)
    
    return DatasetRecord(
        id=record_id,
        dataset_type=dataset_type,
        path_or_value=processed_val,
        label=normalized_label,
        split=split,
        source=source,
        ground_truth_source=ground_truth_source,
        metadata=processed_meta
    )

def ingest_csv_to_manifest(config: IngestionConfig) -> Tuple[DatasetManifest, IngestionSummary]:
    summary = IngestionSummary()
    records = []
    
    source_p = Path(config.source_path)
    if not source_p.exists():
        raise FileNotFoundError(f"Source CSV file not found: {config.source_path}")
        
    with open(source_p, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            summary.records_seen += 1
            
            # Determine path_or_value
            val_col = config.value_column or "path_or_value"
            if val_col not in row:
                summary.skipped_records += 1
                summary.warnings.append(f"Row {summary.records_seen} missing value column '{val_col}'")
                continue
            val = row[val_col]
            
            # Determine label
            lbl_col = config.label_column or "label"
            if lbl_col not in row:
                summary.skipped_records += 1
                summary.warnings.append(f"Row {summary.records_seen} missing label column '{lbl_col}'")
                continue
            raw_label = row[lbl_col]
            
            try:
                label = validate_label(raw_label)
            except ValueError as e:
                summary.skipped_records += 1
                summary.warnings.append(f"Row {summary.records_seen} skipped: {str(e)}")
                continue
                
            # Generate deterministic ID
            rec_id = row.get("id") or f"rec_{config.dataset_type.lower()}_{hashlib.sha256(val.encode('utf-8')).hexdigest()[:12]}"
            
            # Metadata is everything else
            meta = {k: v for k, v in row.items() if k not in {val_col, lbl_col, "id"}}
            
            record = build_dataset_record(
                record_id=rec_id,
                dataset_type=config.dataset_type,
                path_or_value=val,
                label=label,
                split=config.split,
                source=row.get("source") or source_p.name,
                anonymize=config.anonymize,
                ground_truth_source=row.get("ground_truth_source"),
                metadata=meta
            )
            records.append(record)
            summary.records_written += 1
            summary.label_counts[label] = summary.label_counts.get(label, 0) + 1
            
    manifest = DatasetManifest(
        name=f"Ingested CSV: {source_p.name}",
        version="1.0.0",
        records=records,
        notes=f"Generated via dataset_ingestion from CSV source: {config.source_path}"
    )
    
    save_manifest(manifest, config.output_manifest_path)
    return manifest, summary

def ingest_json_to_manifest(config: IngestionConfig) -> Tuple[DatasetManifest, IngestionSummary]:
    summary = IngestionSummary()
    records = []
    
    source_p = Path(config.source_path)
    if not source_p.exists():
        raise FileNotFoundError(f"Source JSON file not found: {config.source_path}")
        
    with open(source_p, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    if not isinstance(data, list):
        data = [data]
        
    for item in data:
        summary.records_seen += 1
        
        val_col = config.value_column or "path_or_value"
        if val_col not in item:
            summary.skipped_records += 1
            summary.warnings.append(f"Item {summary.records_seen} missing value column '{val_col}'")
            continue
        val = str(item[val_col])
        
        lbl_col = config.label_column or "label"
        if lbl_col not in item:
            summary.skipped_records += 1
            summary.warnings.append(f"Item {summary.records_seen} missing label column '{lbl_col}'")
            continue
        raw_label = str(item[lbl_col])
        
        try:
            label = validate_label(raw_label)
        except ValueError as e:
            summary.skipped_records += 1
            summary.warnings.append(f"Item {summary.records_seen} skipped: {str(e)}")
            continue
            
        rec_id = item.get("id") or f"rec_{config.dataset_type.lower()}_{hashlib.sha256(val.encode('utf-8')).hexdigest()[:12]}"
        
        meta = {k: v for k, v in item.items() if k not in {val_col, lbl_col, "id"}}
        
        record = build_dataset_record(
            record_id=rec_id,
            dataset_type=config.dataset_type,
            path_or_value=val,
            label=label,
            split=config.split,
            source=item.get("source") or source_p.name,
            anonymize=config.anonymize,
            ground_truth_source=item.get("ground_truth_source"),
            metadata=meta
        )
        records.append(record)
        summary.records_written += 1
        summary.label_counts[label] = summary.label_counts.get(label, 0) + 1
        
    manifest = DatasetManifest(
        name=f"Ingested JSON: {source_p.name}",
        version="1.0.0",
        records=records,
        notes=f"Generated via dataset_ingestion from JSON source: {config.source_path}"
    )
    
    save_manifest(manifest, config.output_manifest_path)
    return manifest, summary

def ingest_directory_to_manifest(config: IngestionConfig) -> Tuple[DatasetManifest, IngestionSummary]:
    summary = IngestionSummary()
    records = []
    
    source_p = Path(config.source_path)
    if not source_p.exists() or not source_p.is_dir():
        raise FileNotFoundError(f"Source directory not found: {config.source_path}")
        
    # We scan recursively for all files
    for filepath in source_p.rglob("*"):
        if filepath.is_dir():
            continue
            
        summary.records_seen += 1
        
        # Determine dataset type (or use config default)
        inferred_type = infer_dataset_type_from_path(filepath)
        dtype = config.dataset_type
        if inferred_type:
            dtype = DatasetType(inferred_type)
            
        # For directories, since we don't have explicit labels, we look for parent folder names
        # like "clean", "suspicious", "fraud", "high"
        parent_name = filepath.parent.name
        try:
            label = validate_label(parent_name)
        except ValueError:
            # Fallback to config label if specified, or default to SUSPICIOUS
            label = "SUSPICIOUS"
            summary.warnings.append(
                f"Could not infer label from directory name '{parent_name}' for file '{filepath.name}', using SUSPICIOUS"
            )
            
        val = str(filepath.resolve())
        rec_id = f"rec_{dtype.lower()}_{hashlib.sha256(val.encode('utf-8')).hexdigest()[:12]}"
        
        # Add basic file size/name metadata
        meta = {
            "filename": filepath.name,
            "size_bytes": filepath.stat().st_size,
            "parent_directory": parent_name
        }
        
        record = build_dataset_record(
            record_id=rec_id,
            dataset_type=dtype,
            path_or_value=val,
            label=label,
            split=config.split,
            source=f"directory_scan:{source_p.name}",
            anonymize=config.anonymize,
            metadata=meta
        )
        records.append(record)
        summary.records_written += 1
        summary.label_counts[label] = summary.label_counts.get(label, 0) + 1
        
    manifest = DatasetManifest(
        name=f"Ingested Directory: {source_p.name}",
        version="1.0.0",
        records=records,
        notes=f"Generated via dataset_ingestion from directory scan: {config.source_path}"
    )
    
    save_manifest(manifest, config.output_manifest_path)
    return manifest, summary
