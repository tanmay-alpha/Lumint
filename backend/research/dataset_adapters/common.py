import csv
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from research.dataset_manifest import DatasetManifest, save_manifest

class DatasetAdapterResult(BaseModel):
    dataset_name: str
    records_seen: int
    records_written: int
    skipped_records: int
    output_manifest_path: str
    label_counts: Dict[str, int] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)

def normalize_binary_label(value: Any) -> str:
    """
    Normalizes binary labels (0/1, benign/malicious, true/false) into CLEAN or HIGH.
    """
    if value is None:
        return "SUSPICIOUS"
    s = str(value).strip().lower()
    if s in {"legitimate", "clean", "benign", "safe", "ok", "0", "false", "no"}:
        return "CLEAN"
    if s in {"phishing", "malicious", "forged", "fraud", "bad", "1", "true", "yes", "high"}:
        return "HIGH"
    return "SUSPICIOUS"

def normalize_risk_label(value: Any) -> str:
    """
    Normalizes risk/classification labels (clean, warning, high, critical) into CLEAN, SUSPICIOUS, or HIGH.
    """
    if value is None:
        return "SUSPICIOUS"
    s = str(value).strip().lower()
    if s in {"clean", "benign", "safe", "ok", "0", "low"}:
        return "CLEAN"
    if s in {"suspicious", "warn", "warning", "medium"}:
        return "SUSPICIOUS"
    if s in {"high", "malicious", "forged", "fraud", "bad", "1", "critical"}:
        return "HIGH"
    return "SUSPICIOUS"

def safe_read_csv(path: Path) -> List[Dict[str, Any]]:
    """
    Safely reads a CSV file trying UTF-8 first, falling back to Latin-1.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return list(reader)
    except UnicodeDecodeError:
        with open(path, "r", encoding="latin-1") as f:
            reader = csv.DictReader(f)
            return list(reader)

def safe_read_json(path: Path) -> Any:
    """
    Safely reads a JSON file trying UTF-8 first, falling back to Latin-1.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except UnicodeDecodeError:
        with open(path, "r", encoding="latin-1") as f:
            return json.load(f)

def reject_if_private_output_path(path: Path) -> None:
    """
    Raises ValueError if the output path contains sensitive folder names
    (e.g., credentials, secrets, password, etc.).
    """
    path_str = str(path).lower()
    sensitive_keywords = {"secret", "credentials", "password", ".env"}
    for part in path.parts:
        part_lower = part.lower()
        if any(kw in part_lower for kw in sensitive_keywords):
            raise ValueError(f"Output path contains sensitive part: {part}")

def write_manifest_safe(manifest: DatasetManifest, output_path: Path) -> DatasetAdapterResult:
    """
    Safely checks and writes the manifest to output_path.
    """
    reject_if_private_output_path(output_path)
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    save_manifest(manifest, str(output_path))
    
    # Calculate stats
    label_counts = {}
    for r in manifest.records:
        label_counts[r.label] = label_counts.get(r.label, 0) + 1
        
    return DatasetAdapterResult(
        dataset_name=manifest.name,
        records_seen=len(manifest.records),
        records_written=len(manifest.records),
        skipped_records=0,
        output_manifest_path=str(output_path),
        label_counts=label_counts,
        warnings=[]
    )

def resolve_input_path(path: str | Path) -> Path:
    """
    Resolves input path into absolute Path object.
    """
    p = Path(path)
    if not p.is_absolute():
        p = p.resolve()
    return p
