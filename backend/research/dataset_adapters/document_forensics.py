import hashlib
from pathlib import Path
from typing import Optional, List, Dict, Any

from research.dataset_manifest import DatasetManifest, DatasetRecord, DatasetType, DatasetSplit
from research.dataset_adapters.common import (
    DatasetAdapterResult,
    write_manifest_safe,
    resolve_input_path
)

def convert_document_forensics_to_manifest(
    input_dir: Path,
    output_path: Path,
    split: str = "BENCHMARK",
    limit: Optional[int] = None,
) -> DatasetAdapterResult:
    """
    Converts a document forensics dataset directory to a Lumint DatasetManifest.
    """
    input_dir = resolve_input_path(input_dir)
    if not input_dir.exists() or not input_dir.is_dir():
        raise FileNotFoundError(f"Document forensics source directory not found: {input_dir}")
        
    records_seen = 0
    records_written = 0
    skipped_records = 0
    warnings = []
    
    # Supported document/image extensions
    supported_extensions = {".pdf", ".png", ".jpg", ".jpeg", ".webp", ".txt", ".tiff"}
    file_list = []
    for filepath in input_dir.rglob("*"):
        if filepath.is_dir():
            continue
        if filepath.suffix.lower() in supported_extensions:
            file_list.append(filepath)
            
    if limit is not None:
        file_list = file_list[:limit]
        
    records = []
    for filepath in file_list:
        records_seen += 1
        
        # Determine parent folder name
        parent_name = filepath.parent.name.lower()
        
        # Mapping: clean -> CLEAN, forged -> HIGH, suspicious -> SUSPICIOUS
        if parent_name == "clean":
            label = "CLEAN"
        elif parent_name == "forged":
            label = "HIGH"
        elif parent_name == "suspicious":
            label = "SUSPICIOUS"
        else:
            label = "SUSPICIOUS"
            
        path_str = str(filepath.resolve())
        rec_id = f"rec_doc_{hashlib.sha256(path_str.encode('utf-8')).hexdigest()[:12]}"
        
        meta = {
            "filename": filepath.name,
            "parent_folder": filepath.parent.name,
            "size_bytes": filepath.stat().st_size
        }
        
        rec = DatasetRecord(
            id=rec_id,
            dataset_type=DatasetType.DOCUMENT,
            path_or_value=path_str,
            label=label,
            split=DatasetSplit(split),
            source="document_forensics",
            ground_truth_source="local_directory",
            metadata=meta
        )
        records.append(rec)
        records_written += 1
        
    manifest = DatasetManifest(
        name="Document Forensics Ingested",
        version="1.0.0",
        records=records,
        notes=f"Converted from Document Forensics directory: {input_dir.name}"
    )
    
    res = write_manifest_safe(manifest, output_path)
    res.records_seen = records_seen
    res.records_written = records_written
    res.skipped_records = skipped_records
    res.warnings = warnings
    return res
