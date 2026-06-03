import json
from datetime import datetime, timezone
from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class DatasetType(str, Enum):
    DOCUMENT = "DOCUMENT"
    URL = "URL"
    UPI_SCREENSHOT = "UPI_SCREENSHOT"
    FRAUD_DNA = "FRAUD_DNA"

class DatasetSplit(str, Enum):
    TRAIN = "TRAIN"
    VALIDATION = "VALIDATION"
    TEST = "TEST"
    BENCHMARK = "BENCHMARK"

class DatasetRecord(BaseModel):
    id: str
    dataset_type: DatasetType
    path_or_value: str
    label: str  # e.g., "CLEAN", "SUSPICIOUS", "HIGH"
    split: DatasetSplit
    source: str
    ground_truth_source: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class DatasetManifest(BaseModel):
    name: str
    version: str
    records: List[DatasetRecord] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    notes: Optional[str] = None

def load_manifest(path: str) -> DatasetManifest:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return DatasetManifest.model_validate(data)

def save_manifest(manifest: DatasetManifest, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        # Use model_dump_json or model_dump + json.dump for clean encoding
        json.dump(manifest.model_dump(), f, indent=2, ensure_ascii=False)

def validate_manifest(manifest: DatasetManifest) -> bool:
    # Ensure all record IDs are unique
    ids = [r.id for r in manifest.records]
    if len(ids) != len(set(ids)):
        return False
    # Ensure path_or_value is non-empty
    for record in manifest.records:
        if not record.path_or_value.strip():
            return False
    return True

def summarize_manifest(manifest: DatasetManifest) -> Dict[str, Any]:
    summary = {
        "name": manifest.name,
        "version": manifest.version,
        "total_records": len(manifest.records),
        "split_counts": {},
        "type_counts": {},
        "label_counts": {},
    }
    
    for record in manifest.records:
        summary["split_counts"][record.split] = summary["split_counts"].get(record.split, 0) + 1
        summary["type_counts"][record.dataset_type] = summary["type_counts"].get(record.dataset_type, 0) + 1
        summary["label_counts"][record.label] = summary["label_counts"].get(record.label, 0) + 1
        
    return summary
