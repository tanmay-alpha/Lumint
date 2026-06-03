import time
import json
import uuid
from datetime import datetime, timezone
from typing import Callable, Any, Dict, Optional
from pydantic import BaseModel, Field
from research.dataset_manifest import DatasetManifest, DatasetType
from research.metrics import compute_binary_classification_metrics, compute_latency_metrics

class ExperimentResult(BaseModel):
    experiment_id: str
    dataset_name: str
    model_name: str
    record_count: int
    metrics: Dict[str, Any]
    latency: Dict[str, float]
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    notes: Optional[str] = None

def create_experiment_id() -> str:
    # Format: exp-YYYYMMDD-HHMMSS-RANDOM
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y%m%d-%H%M%S")
    rand_str = str(uuid.uuid4())[:8]
    return f"exp-{date_str}-{rand_str}"

def run_baseline_experiment(manifest: DatasetManifest, baseline_fn: Callable[[Any], Dict[str, Any]]) -> ExperimentResult:
    y_true = []
    y_pred = []
    latencies = []
    
    fn_name = baseline_fn.__name__
    
    for record in manifest.records:
        # Determine appropriate input for baseline based on its name and dataset type
        if fn_name == "document_metadata_baseline":
            input_val = record.metadata
        elif fn_name == "upi_utr_format_baseline":
            input_val = record.metadata.get("utr") or record.path_or_value
        else:
            input_val = record.path_or_value
            
        start_time = time.perf_counter()
        res = baseline_fn(input_val)
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        
        latencies.append(elapsed_ms)
        
        y_true.append(record.label)
        y_pred.append(res["label"])
        
    metrics_result = compute_binary_classification_metrics(y_true, y_pred)
    latency_result = compute_latency_metrics(latencies)
    
    return ExperimentResult(
        experiment_id=create_experiment_id(),
        dataset_name=manifest.name,
        model_name=fn_name,
        record_count=len(manifest.records),
        metrics=metrics_result,
        latency=latency_result,
        notes=f"Heuristic baseline evaluation run using {fn_name}."
    )

def write_experiment_result(result: ExperimentResult, output_path: str) -> None:
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result.model_dump(), f, indent=2, ensure_ascii=False)
