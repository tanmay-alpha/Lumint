import os
import tempfile
import pytest
from research.dataset_manifest import (
    DatasetManifest,
    DatasetRecord,
    DatasetType,
    DatasetSplit,
    load_manifest,
    save_manifest,
    validate_manifest,
    summarize_manifest
)
from research.baselines import (
    url_keyword_baseline,
    url_domain_length_baseline,
    document_metadata_baseline,
    upi_utr_format_baseline
)
from research.experiment_runner import run_baseline_experiment, write_experiment_result
from research.report_writer import write_markdown_report

@pytest.fixture
def sample_manifest() -> DatasetManifest:
    records = [
        DatasetRecord(
            id="rec-1",
            dataset_type=DatasetType.URL,
            path_or_value="https://chase-security-verify.net/login",
            label="HIGH",
            split=DatasetSplit.TEST,
            source="PhishTank",
            ground_truth_source="manual_verification",
            metadata={"domain": "chase-security-verify.net"}
        ),
        DatasetRecord(
            id="rec-2",
            dataset_type=DatasetType.URL,
            path_or_value="https://google.com",
            label="CLEAN",
            split=DatasetSplit.TEST,
            source="PhishTank",
            ground_truth_source="manual_verification"
        ),
        DatasetRecord(
            id="rec-3",
            dataset_type=DatasetType.DOCUMENT,
            path_or_value="C:/data/invoice.pdf",
            label="HIGH",
            split=DatasetSplit.BENCHMARK,
            source="Mendeley",
            metadata={"producer": "Adobe Photoshop CC", "editor_tool": "Photoshop"}
        )
    ]
    return DatasetManifest(
        name="test_dataset",
        version="1.0.0",
        records=records,
        notes="A test dataset manifest for validation."
    )

def test_manifest_validation_and_summary(sample_manifest):
    assert validate_manifest(sample_manifest) is True
    
    summary = summarize_manifest(sample_manifest)
    assert summary["name"] == "test_dataset"
    assert summary["version"] == "1.0.0"
    assert summary["total_records"] == 3
    assert summary["split_counts"][DatasetSplit.TEST] == 2
    assert summary["split_counts"][DatasetSplit.BENCHMARK] == 1
    assert summary["type_counts"][DatasetType.URL] == 2
    assert summary["type_counts"][DatasetType.DOCUMENT] == 1
    assert summary["label_counts"]["HIGH"] == 2
    assert summary["label_counts"]["CLEAN"] == 1

def test_manifest_invalid_unique_ids(sample_manifest):
    # Duplicate ID
    sample_manifest.records[1].id = "rec-1"
    assert validate_manifest(sample_manifest) is False

def test_manifest_invalid_empty_paths(sample_manifest):
    # Empty path
    sample_manifest.records[1].path_or_value = "   "
    assert validate_manifest(sample_manifest) is False

def test_manifest_save_and_load(sample_manifest):
    fd, temp_path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    try:
        save_manifest(sample_manifest, temp_path)
        loaded = load_manifest(temp_path)
        assert loaded.name == sample_manifest.name
        assert len(loaded.records) == len(sample_manifest.records)
        assert loaded.records[0].id == sample_manifest.records[0].id
        assert loaded.records[0].dataset_type == DatasetType.URL
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

def test_experiment_runner_and_report_writer(sample_manifest):
    # Run URL keyword baseline
    result = run_baseline_experiment(sample_manifest, url_keyword_baseline)
    assert result.record_count == 3
    assert "accuracy" in result.metrics
    assert "mean" in result.latency
    
    # Save experiment result
    fd1, temp_exp_path = tempfile.mkstemp(suffix=".json")
    fd2, temp_report_path = tempfile.mkstemp(suffix=".md")
    os.close(fd1)
    os.close(fd2)
    
    try:
        write_experiment_result(result, temp_exp_path)
        assert os.path.exists(temp_exp_path)
        
        write_markdown_report(result, temp_report_path)
        assert os.path.exists(temp_report_path)
        with open(temp_report_path, "r", encoding="utf-8") as f:
            content = f.read()
            assert result.model_name in content
            assert "Classification Performance Metrics" in content
    finally:
        for p in (temp_exp_path, temp_report_path):
            if os.path.exists(p):
                os.remove(p)

def test_baselines_heuristics():
    # URL keyword
    r = url_keyword_baseline("https://chase-security-verify.net/login")
    assert r["label"] == "HIGH"
    
    r = url_keyword_baseline("https://google.com")
    assert r["label"] == "CLEAN"
    
    # Domain length
    r = url_domain_length_baseline("https://super-duper-long-phishing-domain-name-that-is-suspicious.com")
    assert r["label"] == "HIGH"
    
    # Document metadata
    r = document_metadata_baseline({"producer": "Adobe Photoshop CC"})
    assert r["label"] == "HIGH"
    
    # UPI UTR
    r = upi_utr_format_baseline("318273645192")
    assert r["label"] == "CLEAN"
    
    r = upi_utr_format_baseline("abc123xyz789")
    assert r["label"] == "HIGH"
    
    r = upi_utr_format_baseline("12345")
    assert r["label"] == "HIGH"
