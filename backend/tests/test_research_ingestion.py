import csv
import json
import pytest
from pathlib import Path
from research.dataset_manifest import DatasetType, DatasetSplit, load_manifest
from research.dataset_ingestion import (
    IngestionConfig,
    IngestionSourceType,
    ingest_csv_to_manifest,
    ingest_json_to_manifest,
    ingest_directory_to_manifest,
    validate_label
)

def test_invalid_labels_normalized_or_warned():
    # Valid normalizations
    assert validate_label("clean") == "CLEAN"
    assert validate_label("benign") == "CLEAN"
    assert validate_label("safe") == "CLEAN"
    assert validate_label("ok") == "CLEAN"
    
    assert validate_label("fraud") == "HIGH"
    assert validate_label("malicious") == "HIGH"
    assert validate_label("bad") == "HIGH"
    
    assert validate_label("warn") == "SUSPICIOUS"
    assert validate_label("warning") == "SUSPICIOUS"
    assert validate_label("medium") == "SUSPICIOUS"
    
    with pytest.raises(ValueError):
        validate_label("super_fraud")

def test_ingest_csv_to_manifest_tmp_file(tmp_path):
    csv_file = tmp_path / "test_urls.csv"
    manifest_file = tmp_path / "manifest.json"
    
    # Create mock CSV
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "url_val", "raw_lbl", "source", "notes"])
        writer.writerow(["rec_1", "https://scam-url.com/login?token=abc", "fraud", "test_csv", "phone: 9876543210"])
        writer.writerow(["rec_2", "https://legit-site.com", "clean", "test_csv", "ok"])
        writer.writerow(["rec_3", "https://suspicious-site.com", "warn", "test_csv", "maybe bad"])
        
    config = IngestionConfig(
        source_path=str(csv_file),
        source_type=IngestionSourceType.CSV,
        dataset_type=DatasetType.URL,
        label_column="raw_lbl",
        value_column="url_val",
        split=DatasetSplit.BENCHMARK,
        anonymize=True,
        output_manifest_path=str(manifest_file)
    )
    
    manifest, summary = ingest_csv_to_manifest(config)
    
    assert summary.records_seen == 3
    assert summary.records_written == 3
    assert summary.skipped_records == 0
    assert summary.label_counts["HIGH"] == 1
    assert summary.label_counts["CLEAN"] == 1
    assert summary.label_counts["SUSPICIOUS"] == 1
    
    # Load and verify manifest contents
    loaded = load_manifest(str(manifest_file))
    assert len(loaded.records) == 3
    
    # Check anonymization
    rec1 = next(r for r in loaded.records if r.id == "rec_1")
    assert "token=abc" not in rec1.path_or_value
    assert "9876543210" not in rec1.metadata["notes"]
    assert "<PHONE_HASH:" in rec1.metadata["notes"]

def test_ingest_json_to_manifest_tmp_file(tmp_path):
    json_file = tmp_path / "test_docs.json"
    manifest_file = tmp_path / "manifest.json"
    
    mock_data = [
        {"id": "doc_1", "file_path": "uploads/fake_invoice.pdf", "lbl": "fraud", "notes": "email: scam@gmail.com"},
        {"id": "doc_2", "file_path": "uploads/real_invoice.pdf", "lbl": "clean"}
    ]
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(mock_data, f)
        
    config = IngestionConfig(
        source_path=str(json_file),
        source_type=IngestionSourceType.JSON,
        dataset_type=DatasetType.DOCUMENT,
        label_column="lbl",
        value_column="file_path",
        split=DatasetSplit.TEST,
        anonymize=True,
        output_manifest_path=str(manifest_file)
    )
    
    manifest, summary = ingest_json_to_manifest(config)
    
    assert summary.records_seen == 2
    assert summary.records_written == 2
    loaded_manifest = load_manifest(str(manifest_file))
    assert loaded_manifest
    assert len(loaded_manifest.records) == 2
    
    rec1 = next(r for r in loaded_manifest.records if r.id == "doc_1")
    assert "scam@gmail.com" not in rec1.metadata["notes"]

def test_ingest_directory_to_manifest_tmp_files(tmp_path):
    # Setup folders
    clean_dir = tmp_path / "clean"
    fraud_dir = tmp_path / "fraud"
    clean_dir.mkdir()
    fraud_dir.mkdir()
    
    # Write empty files representing screenshots
    (clean_dir / "sc_1.png").write_text("dummy")
    (fraud_dir / "sc_2.jpg").write_text("dummy")
    
    manifest_file = tmp_path / "manifest.json"
    
    config = IngestionConfig(
        source_path=str(tmp_path),
        source_type=IngestionSourceType.DIRECTORY,
        dataset_type=DatasetType.UPI_SCREENSHOT,
        split=DatasetSplit.BENCHMARK,
        anonymize=False,
        output_manifest_path=str(manifest_file)
    )
    
    manifest, summary = ingest_directory_to_manifest(config)
    
    assert summary.records_seen == 2
    assert summary.records_written == 2
    assert summary.label_counts["CLEAN"] == 1
    assert summary.label_counts["HIGH"] == 1
