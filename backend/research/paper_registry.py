import json
from pathlib import Path
from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field

class PaperExperiment(BaseModel):
    experiment_id: str
    title: str
    module: str
    manifest_path: str
    output_dir: str
    table_target: str
    status: Literal["planned", "synthetic_done", "real_data_pending", "complete"]
    notes: Optional[str] = None

class PaperExperimentRegistry(BaseModel):
    version: str
    experiments: List[PaperExperiment] = Field(default_factory=list)

def load_paper_registry(path: Path) -> PaperExperimentRegistry:
    """
    Loads paper registry from a JSON file.
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return PaperExperimentRegistry.model_validate(data)

def save_paper_registry(registry: PaperExperimentRegistry, path: Path) -> None:
    """
    Saves paper registry to a JSON file.
    """
    with open(path, "w", encoding="utf-8") as f:
        json.dump(registry.model_dump(), f, indent=2, ensure_ascii=False)

def validate_paper_registry(registry: PaperExperimentRegistry) -> Dict[str, Any]:
    """
    Validates paper registry: checks for unique experiment IDs and valid manifest paths.
    """
    errors = []
    ids = [e.experiment_id for e in registry.experiments]
    if len(ids) != len(set(ids)):
        duplicate_ids = set([x for x in ids if ids.count(x) > 1])
        errors.append(f"Duplicate experiment IDs found: {duplicate_ids}")

    for experiment in registry.experiments:
        # Check if manifest path exists (warning/info if not found)
        # Note: manifest_path can be relative, so we don't strictly enforce physical file existence here,
        # but check format or basic empty string checks.
        if not experiment.experiment_id.strip():
            errors.append("Experiment ID cannot be empty.")
        if not experiment.manifest_path.strip():
            errors.append(f"Experiment {experiment.experiment_id} has empty manifest_path.")
            
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }

def summarize_paper_registry(registry: PaperExperimentRegistry) -> Dict[str, Any]:
    """
    Returns summary statistics of the paper registry.
    """
    summary = {
        "version": registry.version,
        "total_experiments": len(registry.experiments),
        "status_counts": {},
        "module_counts": {},
    }
    for experiment in registry.experiments:
        summary["status_counts"][experiment.status] = summary["status_counts"].get(experiment.status, 0) + 1
        summary["module_counts"][experiment.module] = summary["module_counts"].get(experiment.module, 0) + 1
    return summary
