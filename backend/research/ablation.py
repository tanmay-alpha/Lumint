import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from research.dataset_manifest import DatasetManifest, DatasetRecord
from research.experiment_runner import run_lumint_experiment

class AblationVariant(BaseModel):
    name: str
    description: str
    disabled_signals: List[str]
    weight_override: Optional[Dict[str, float]] = None
    notes: Optional[str] = None

class AblationResult(BaseModel):
    variant_name: str
    record_count: int
    metrics: Dict[str, Any]
    latency: Dict[str, float]
    agreement: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None

class AblationStudyResult(BaseModel):
    study_id: str
    dataset_name: str
    module_name: str
    variants: List[AblationResult]
    best_variant: Optional[str] = None
    created_at: str
    notes: Optional[str] = None

def create_default_ablation_variants() -> List[AblationVariant]:
    """
    Generate standard ablation variants for Lumint fusion module.
    """
    return [
        AblationVariant(
            name="full_lumint",
            description="Full multi-modal integration using all DocShield, PhishShield, and UPI Shield signals.",
            disabled_signals=[]
        ),
        AblationVariant(
            name="no_document_signal",
            description="Ablates the DocShield document forensics score, relying on phishing and payment layers.",
            disabled_signals=["document"]
        ),
        AblationVariant(
            name="no_phishing_signal",
            description="Ablates the PhishShield URL risk score, relying on document forensics and payment layers.",
            disabled_signals=["phishing"]
        ),
        AblationVariant(
            name="no_upi_signal",
            description="Ablates the UPI Shield layout check forensics, relying on document and URL checks.",
            disabled_signals=["upi"]
        ),
        AblationVariant(
            name="equal_weights",
            description="Equal weights assigned to all active modalities instead of standard dynamic priority weighting.",
            disabled_signals=[],
            weight_override={"document": 0.3333, "phishing": 0.3333, "upi": 0.3334}
        )
    ]

def apply_ablation_to_record(record: DatasetRecord, variant: AblationVariant) -> DatasetRecord:
    """
    Deep-copies a DatasetRecord and removes disabled modalities from its metadata.
    Does not modify the original record.
    """
    new_record = record.model_copy(deep=True)
    if new_record.metadata is None:
        new_record.metadata = {}
        
    for signal in variant.disabled_signals:
        if signal == "document":
            new_record.metadata.pop("document_result", None)
        elif signal == "phishing":
            new_record.metadata.pop("phishing_result", None)
        elif signal == "upi":
            new_record.metadata.pop("upi_result", None)
            
    if variant.weight_override:
        new_record.metadata["weights_override"] = variant.weight_override
    else:
        new_record.metadata.pop("weights_override", None)
        
    return new_record

def select_best_variant(results: List[AblationResult]) -> Optional[str]:
    """
    Identifies the best performing variant based on F1, Accuracy, and Latency.
    """
    if not results:
        return None
        
    def score_key(res: AblationResult):
        f1 = res.metrics.get("f1", 0.0)
        accuracy = res.metrics.get("accuracy", 0.0)
        mean_latency = res.latency.get("mean", 99999.0)
        return (f1, accuracy, -mean_latency)
        
    best = max(results, key=score_key)
    return best.variant_name

def run_ablation_study(
    manifest: DatasetManifest,
    module_name: str,
    variants: Optional[List[AblationVariant]] = None,
    consensus_fixture_path: Optional[str] = None
) -> AblationStudyResult:
    """
    Executes an ablation study by running a manifest against multiple configuration variants.
    """
    if variants is None:
        variants = create_default_ablation_variants()
        
    results = []
    
    for variant in variants:
        # Create a variant-specific copy of the manifest with ablated records
        ablated_records = [apply_ablation_to_record(r, variant) for r in manifest.records]
        variant_manifest = manifest.model_copy(deep=True)
        variant_manifest.records = ablated_records
        
        # Run standard experiment
        experiment = run_lumint_experiment(variant_manifest, module_name)
        
        # Evaluate consensus alignment if consensus path is provided
        agreement_metrics = None
        if consensus_fixture_path:
            try:
                from research.consensus_adapters import load_consensus_data
                from research.agreement import evaluate_agreement
                consensus_data = load_consensus_data(consensus_fixture_path)
                agreement_metrics = evaluate_agreement(experiment.results, consensus_data)
            except Exception:
                pass
                
        results.append(
            AblationResult(
                variant_name=variant.name,
                record_count=len(ablated_records),
                metrics=experiment.metrics,
                latency=experiment.latency,
                agreement=agreement_metrics,
                notes=variant.description
            )
        )
        
    best_var = select_best_variant(results)
    
    import uuid
    study_id = f"ablation-study-{uuid.uuid4().hex[:8]}"
    
    return AblationStudyResult(
        study_id=study_id,
        dataset_name=manifest.name,
        module_name=module_name,
        variants=results,
        best_variant=best_var,
        created_at=datetime.datetime.utcnow().isoformat() + "Z",
        notes=f"Completed ablation study evaluating {len(variants)} variants on module '{module_name}'."
    )
