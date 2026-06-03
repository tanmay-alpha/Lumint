import os
import pytest
import tempfile
from pathlib import Path

from research.dataset_manifest import load_manifest, validate_manifest
from research.module_adapters import run_record, PredictionResult
from research.experiment_runner import run_lumint_experiment, save_experiment_outputs
from scripts.run_research_benchmark import filter_records_for_module

def test_load_and_validate_fixtures():
    fixtures_dir = Path(__file__).resolve().parents[1] / "research" / "fixtures"
    
    for filename in ["url_benchmark_manifest.json", "upi_benchmark_manifest.json", "document_benchmark_manifest.json", "fusion_benchmark_manifest.json", "all_benchmark_manifest.json"]:
        manifest_path = fixtures_dir / filename
        assert manifest_path.exists()
        manifest = load_manifest(str(manifest_path))
        assert validate_manifest(manifest) is True
        assert len(manifest.records) > 0

def test_run_record_url():
    fixtures_dir = Path(__file__).resolve().parents[1] / "research" / "fixtures"
    manifest = load_manifest(str(fixtures_dir / "url_benchmark_manifest.json"))
    
    # Check predicting first record
    record = manifest.records[0]
    result = run_record(record)
    assert isinstance(result, PredictionResult)
    assert result.record_id == record.id
    assert result.module == "url"
    assert result.predicted_label in ["CLEAN", "SUSPICIOUS", "HIGH"]
    assert result.latency_ms >= 0.0
    assert result.error is None

def test_run_record_upi_with_synthetic_text():
    fixtures_dir = Path(__file__).resolve().parents[1] / "research" / "fixtures"
    manifest = load_manifest(str(fixtures_dir / "upi_benchmark_manifest.json"))
    
    # Check predicting first record
    record = manifest.records[0]
    result = run_record(record)
    assert isinstance(result, PredictionResult)
    assert result.record_id == record.id
    assert result.module == "upi"
    assert result.predicted_label in ["CLEAN", "SUSPICIOUS", "HIGH"]
    assert result.error is None

def test_run_record_document_missing_fallback():
    fixtures_dir = Path(__file__).resolve().parents[1] / "research" / "fixtures"
    manifest = load_manifest(str(fixtures_dir / "document_benchmark_manifest.json"))
    
    # Modify a path to verify missing file behaves correctly (returns error instead of crash)
    record = manifest.records[0].model_copy()
    record.path_or_value = "nonexistent_file_path.pdf"
    
    result = run_record(record)
    assert isinstance(result, PredictionResult)
    assert result.record_id == record.id
    assert result.module == "document"
    assert result.error is not None

def test_filter_records_for_module():
    fixtures_dir = Path(__file__).resolve().parents[1] / "research" / "fixtures"
    all_manifest = load_manifest(str(fixtures_dir / "all_benchmark_manifest.json"))
    
    url_m = filter_records_for_module(all_manifest, "url")
    assert all(r.dataset_type.value == "URL" for r in url_m.records)
    
    upi_m = filter_records_for_module(all_manifest, "upi")
    assert all(r.dataset_type.value == "UPI_SCREENSHOT" for r in upi_m.records)

def test_run_lumint_experiment_and_save():
    fixtures_dir = Path(__file__).resolve().parents[1] / "research" / "fixtures"
    manifest = load_manifest(str(fixtures_dir / "url_benchmark_manifest.json"))
    
    result = run_lumint_experiment(manifest, "url")
    assert result.record_count == len(manifest.records)
    assert "accuracy" in result.metrics
    assert result.errors_count == 0
    assert len(result.results) == len(manifest.records)
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        save_experiment_outputs(result, tmp_dir)
        
        json_file = Path(tmp_dir) / f"{result.experiment_id}.json"
        md_file = Path(tmp_dir) / f"{result.experiment_id}.md"
        
        assert json_file.exists()
        assert md_file.exists()
        
        with open(md_file, "r", encoding="utf-8") as f:
            content = f.read()
            assert "Classification Performance Metrics" in content
            assert result.experiment_id in content
