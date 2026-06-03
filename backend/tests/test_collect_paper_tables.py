import json
import pytest
from pathlib import Path
from scripts.collect_paper_tables import collect_tables

def test_collect_paper_tables_dry_run_no_outputs(tmp_path):
    registry_file = tmp_path / "paper_experiments.json"
    outputs_dir = tmp_path / "research_outputs"
    paper_dir = tmp_path / "paper"
    
    registry_data = {
        "version": "1.0.0",
        "experiments": [
            {
                "experiment_id": "exp_1",
                "title": "Ablation Study",
                "module": "Ablation",
                "manifest_path": "research/fixtures/all_manifest.json",
                "output_dir": "research_outputs/ablation",
                "table_target": "tables/generated_ablation.csv",
                "status": "synthetic_done"
            }
        ]
    }
    
    with open(registry_file, "w", encoding="utf-8") as f:
        json.dump(registry_data, f)
        
    # Running dry_run should not create files
    collect_tables(registry_file, outputs_dir, paper_dir, dry_run=True)
    
    # Check that neither tables folder nor index.md got physically created
    assert not (paper_dir / "tables").exists()

def test_collect_paper_tables_creates_index(tmp_path):
    registry_file = tmp_path / "paper_experiments.json"
    outputs_dir = tmp_path / "research_outputs"
    paper_dir = tmp_path / "paper"
    
    registry_data = {
        "version": "1.0.0",
        "experiments": [
            {
                "experiment_id": "exp_1",
                "title": "Ablation Study",
                "module": "Ablation",
                "manifest_path": "research/fixtures/all_manifest.json",
                "output_dir": "research_outputs/ablation",
                "table_target": "tables/generated_ablation.csv",
                "status": "synthetic_done"
            }
        ]
    }
    
    with open(registry_file, "w", encoding="utf-8") as f:
        json.dump(registry_data, f)
        
    # Create fake output file
    exp_out_dir = outputs_dir / "exp_1"
    exp_out_dir.mkdir(parents=True)
    (exp_out_dir / "ablation_results.csv").write_text("modality,f1\nall,0.95\nno_url,0.80")
    
    # Run collection (non dry-run)
    collect_tables(registry_file, outputs_dir, paper_dir, dry_run=False)
    
    # Check that the table file got copied and index.md got created
    copied_file = paper_dir / "tables" / "generated_ablation.csv"
    assert copied_file.exists()
    assert "no_url,0.80" in copied_file.read_text(encoding="utf-8")
    
    index_file = paper_dir / "tables" / "index.md"
    assert index_file.exists()
    assert "generated_ablation.csv" in index_file.read_text(encoding="utf-8")
    assert "✅ Yes" in index_file.read_text(encoding="utf-8")
