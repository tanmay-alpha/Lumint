import pytest
from pathlib import Path
from research.paper_registry import (
    PaperExperiment,
    PaperExperimentRegistry,
    load_paper_registry,
    save_paper_registry,
    validate_paper_registry,
    summarize_paper_registry
)

def test_paper_registry_load_validate_summary(tmp_path):
    registry_file = tmp_path / "paper_experiments.json"
    
    # Create sample registry data
    sample_data = {
        "version": "1.0.0",
        "experiments": [
            {
                "experiment_id": "exp_1",
                "title": "Ablation Study on Fusion",
                "module": "Fusion",
                "manifest_path": "research/fixtures/fusion_manifest.json",
                "output_dir": "research_outputs/fusion",
                "table_target": "tables/generated_fusion.csv",
                "status": "synthetic_done",
                "notes": "Test note"
            },
            {
                "experiment_id": "exp_2",
                "title": "Real UPI Test",
                "module": "UPIShield",
                "manifest_path": "real_datasets/upi_manifest.json",
                "output_dir": "research_outputs/upi_real",
                "table_target": "tables/generated_upi_real.csv",
                "status": "real_data_pending"
            }
        ]
    }
    
    # Save manually
    import json
    with open(registry_file, "w") as f:
        json.dump(sample_data, f)
        
    # Load using our function
    registry = load_paper_registry(registry_file)
    assert registry.version == "1.0.0"
    assert len(registry.experiments) == 2
    assert registry.experiments[0].experiment_id == "exp_1"
    
    # Save back and reload
    save_file = tmp_path / "saved_experiments.json"
    save_paper_registry(registry, save_file)
    reloaded = load_paper_registry(save_file)
    assert reloaded.experiments[1].status == "real_data_pending"
    
    # Validate
    validation = validate_paper_registry(reloaded)
    assert validation["valid"] is True
    assert len(validation["errors"]) == 0
    
    # Duplicate ID validation
    reloaded.experiments.append(reloaded.experiments[0])
    validation_dup = validate_paper_registry(reloaded)
    assert validation_dup["valid"] is False
    assert any("Duplicate" in e for e in validation_dup["errors"])
    
    # Summary
    summary = summarize_paper_registry(registry)
    assert summary["total_experiments"] == 2
    assert summary["status_counts"]["synthetic_done"] == 1
    assert summary["status_counts"]["real_data_pending"] == 1
    assert summary["module_counts"]["Fusion"] == 1
