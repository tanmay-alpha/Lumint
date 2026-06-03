import pytest
from pathlib import Path
from research.dataset_manifest import DatasetManifest, DatasetRecord, DatasetType, load_manifest
from research.ablation import (
    create_default_ablation_variants,
    apply_ablation_to_record,
    select_best_variant,
    run_ablation_study,
    AblationVariant,
    AblationResult
)

def test_create_default_ablation_variants():
    variants = create_default_ablation_variants()
    assert len(variants) == 5
    names = [v.name for v in variants]
    assert "full_lumint" in names
    assert "no_document_signal" in names
    assert "no_phishing_signal" in names
    assert "no_upi_signal" in names
    assert "equal_weights" in names

def test_apply_ablation_to_record():
    record = DatasetRecord(
        id="rec-1",
        dataset_type=DatasetType.URL,
        path_or_value="https://test.com",
        label="HIGH",
        split="BENCHMARK",
        source="test",
        metadata={
            "document_result": {"risk_score": 90},
            "phishing_result": {"risk_score": 80},
            "upi_result": {"forgery_score": 70}
        }
    )
    
    # Test disable document
    variant = AblationVariant(
        name="test_var",
        description="test",
        disabled_signals=["document"]
    )
    
    ablated = apply_ablation_to_record(record, variant)
    # Check that original record was NOT mutated
    assert "document_result" in record.metadata
    
    # Check ablated record
    assert "document_result" not in ablated.metadata
    assert "phishing_result" in ablated.metadata
    assert "upi_result" in ablated.metadata
    assert "weights_override" not in ablated.metadata
    
    # Test weight override
    variant_weight = AblationVariant(
        name="test_weight",
        description="test",
        disabled_signals=[],
        weight_override={"document": 0.5, "phishing": 0.5, "upi": 0.0}
    )
    ablated_weight = apply_ablation_to_record(record, variant_weight)
    assert ablated_weight.metadata["weights_override"] == {"document": 0.5, "phishing": 0.5, "upi": 0.0}

def test_select_best_variant():
    res1 = AblationResult(
        variant_name="var1",
        record_count=10,
        metrics={"f1": 0.85, "accuracy": 0.88},
        latency={"mean": 15.0}
    )
    res2 = AblationResult(
        variant_name="var2",
        record_count=10,
        metrics={"f1": 0.90, "accuracy": 0.92},
        latency={"mean": 20.0}
    )
    res3 = AblationResult(
        variant_name="var3",
        record_count=10,
        metrics={"f1": 0.90, "accuracy": 0.92},
        latency={"mean": 10.0} # Lower latency
    )
    
    best = select_best_variant([res1, res2, res3])
    assert best == "var3"

def test_run_ablation_study():
    # Load fusion manifest to run study
    fixtures_dir = Path(__file__).resolve().parents[1] / "research" / "fixtures"
    manifest_path = fixtures_dir / "fusion_benchmark_manifest.json"
    manifest = load_manifest(str(manifest_path))
    
    study = run_ablation_study(manifest, "fusion")
    assert study.dataset_name == manifest.name
    assert study.module_name == "fusion"
    assert len(study.variants) == 5
    assert study.best_variant is not None
