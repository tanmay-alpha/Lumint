import time
import json
import uuid
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Callable, Any, Dict, Optional, List
from pydantic import BaseModel, Field

from research.dataset_manifest import DatasetManifest, DatasetType
from research.metrics import compute_binary_classification_metrics, compute_latency_metrics
from research.consensus_adapters import load_fixture_consensus, ConsensusResult
from research.agreement import AgreementResult, compare_predictions_to_consensus, compute_consensus_confusion_matrix

class ExperimentRunConfig(BaseModel):
    experiment_name: str
    module_name: str
    manifest_path: Optional[str] = None
    output_dir: str = "backend/research_outputs"
    notes: Optional[str] = None
    consensus_fixture_path: Optional[str] = None
    consensus_provider: Optional[str] = None

class ExperimentRecordResult(BaseModel):
    record_id: str
    true_label: str
    predicted_label: str
    predicted_score: float
    latency_ms: float
    error: Optional[str] = None

class ExperimentResult(BaseModel):
    experiment_id: str
    dataset_name: str
    model_name: str
    record_count: int
    metrics: Dict[str, Any]
    latency: Dict[str, float]
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    notes: Optional[str] = None
    # Extended fields for R4
    config: Optional[ExperimentRunConfig] = None
    results: List[ExperimentRecordResult] = Field(default_factory=list)
    errors_count: int = 0
    # Extended fields for R5
    agreement: Optional[AgreementResult] = None
    consensus_metrics: Optional[Dict[str, Any]] = None
    # Extended fields for R6
    ablation_study: Optional[Any] = None
    confidence_intervals: Optional[Dict[str, Any]] = None
    error_summary: Optional[Dict[str, Any]] = None

def create_experiment_id() -> str:
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y%m%d-%H%M%S")
    rand_str = str(uuid.uuid4())[:8]
    return f"exp-{date_str}-{rand_str}"

def create_research_output_dir(output_dir: str) -> Path:
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    gitkeep = out_path / ".gitkeep"
    if not gitkeep.exists():
        try:
            gitkeep.touch()
        except Exception:
            pass
    return out_path

def run_baseline_experiment(manifest: DatasetManifest, baseline_fn: Callable[[Any], Dict[str, Any]]) -> ExperimentResult:
    y_true = []
    y_pred = []
    latencies = []
    results = []
    
    fn_name = baseline_fn.__name__
    
    for record in manifest.records:
        if fn_name == "document_metadata_baseline":
            input_val = record.metadata
        elif fn_name == "upi_utr_format_baseline":
            input_val = record.metadata.get("utr") or record.path_or_value
        else:
            input_val = record.path_or_value
            
        start_time = time.perf_counter()
        try:
            res = baseline_fn(input_val)
            error_msg = None
        except Exception as e:
            res = {"label": "CLEAN", "score": 0.0}
            error_msg = str(e)
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        
        latencies.append(elapsed_ms)
        
        y_true.append(record.label)
        y_pred.append(res["label"])
        results.append(ExperimentRecordResult(
            record_id=record.id,
            true_label=record.label,
            predicted_label=res["label"],
            predicted_score=float(res.get("score", 0.0)),
            latency_ms=elapsed_ms,
            error=error_msg
        ))
        
    metrics_result = compute_binary_classification_metrics(y_true, y_pred)
    latency_result = compute_latency_metrics(latencies)
    errors_count = sum(1 for r in results if r.error is not None)
    
    return ExperimentResult(
        experiment_id=create_experiment_id(),
        dataset_name=manifest.name,
        model_name=fn_name,
        record_count=len(manifest.records),
        metrics=metrics_result,
        latency=latency_result,
        notes=f"Heuristic baseline evaluation run using {fn_name}.",
        results=results,
        errors_count=errors_count
    )

def run_lumint_experiment(manifest: DatasetManifest, module_name: str, config: Optional[ExperimentRunConfig] = None) -> ExperimentResult:
    """
    Run Lumint module evaluation adapters against dataset manifest records.
    """
    from research.module_adapters import run_record
    
    y_true = []
    y_pred = []
    latencies = []
    results = []
    
    for record in manifest.records:
        pred = run_record(record, module=module_name)
        
        y_true.append(record.label)
        y_pred.append(pred.predicted_label)
        latencies.append(pred.latency_ms)
        
        results.append(ExperimentRecordResult(
            record_id=record.id,
            true_label=record.label,
            predicted_label=pred.predicted_label,
            predicted_score=pred.predicted_score,
            latency_ms=pred.latency_ms,
            error=pred.error
        ))
        
    metrics_result = compute_binary_classification_metrics(y_true, y_pred)
    latency_result = compute_latency_metrics(latencies)
    errors_count = sum(1 for r in results if r.error is not None)
    
    experiment_res = ExperimentResult(
        experiment_id=create_experiment_id(),
        dataset_name=manifest.name,
        model_name=f"lumint_{module_name}",
        record_count=len(manifest.records),
        metrics=metrics_result,
        latency=latency_result,
        notes=f"Lumint evaluation experiment run for module '{module_name}'.",
        config=config,
        results=results,
        errors_count=errors_count
    )

    # Automatically support consensus if defined in config
    if config and config.consensus_fixture_path:
        consensus = load_fixture_consensus(Path(config.consensus_fixture_path))
        experiment_res.agreement = compare_predictions_to_consensus(results, consensus)
        experiment_res.consensus_metrics = compute_consensus_confusion_matrix(results, consensus)
        
    return experiment_res

def run_lumint_experiment_with_consensus(
    manifest: DatasetManifest, 
    module_name: str, 
    consensus_fixture_path: Optional[str] = None
) -> ExperimentResult:
    """
    Run Lumint module experiment and evaluate against external ground-truth consensus.
    """
    config = None
    if consensus_fixture_path:
        config = ExperimentRunConfig(
            experiment_name=f"lumint_{module_name}_consensus",
            module_name=module_name,
            consensus_fixture_path=consensus_fixture_path,
            consensus_provider="fixture"
        )
        
    return run_lumint_experiment(manifest, module_name, config)

def save_experiment_outputs(result: ExperimentResult, output_dir: str) -> None:
    out_path = create_research_output_dir(output_dir)
    
    # 1. Write result JSON
    json_path = out_path / f"{result.experiment_id}.json"
    write_experiment_result(result, str(json_path))
    
    # 2. Write Markdown report
    from research.report_writer import write_markdown_report
    report_path = out_path / f"{result.experiment_id}.md"
    write_markdown_report(result, str(report_path))

def write_experiment_result(result: ExperimentResult, output_path: str) -> None:
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result.model_dump(), f, indent=2, ensure_ascii=False)
