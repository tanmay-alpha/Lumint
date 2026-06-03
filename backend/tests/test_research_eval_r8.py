import pytest
import tempfile
import json
import csv
from pathlib import Path
from research.dataset_adapters.common import reject_if_private_output_path, write_manifest_safe
from research.module_adapters import normalize_label_from_score
from research.dataset_adapters.phishtank import convert_phishtank_to_manifest
from research.dataset_adapters.mendeley_phishing import convert_mendeley_phishing_to_manifest
from research.dataset_adapters.upi_receipts import convert_upi_receipts_to_manifest
from research.dataset_adapters.document_forensics import convert_document_forensics_to_manifest
from research.dataset_validator import validate_manifest_for_experiment, summarize_validation
from research.dataset_cards import DatasetCard, generate_dataset_card, dataset_card_to_markdown
from research.dataset_manifest import DatasetManifest, DatasetRecord, DatasetType, DatasetSplit
from scripts.run_paper_experiments import run_experiments, resolve_path
from scripts.build_paper_bundle import build_bundle

def test_reject_if_private_output_path():
    # Should work on safe paths
    reject_if_private_output_path(Path("C:/Users/TANMAY/Lumint/backend/research_outputs/manifest.json"))
    reject_if_private_output_path(Path("C:/Users/TANMAY/Lumint/paper/tables/summary.md"))
    
    # Should raise ValueError on unsafe paths containing private terms
    with pytest.raises(ValueError, match="sensitive"):
        reject_if_private_output_path(Path("C:/Users/TANMAY/Lumint/secret_folder/manifest.json"))
    with pytest.raises(ValueError, match="sensitive"):
        reject_if_private_output_path(Path("C:/Users/TANMAY/Lumint/my_passwords/manifest.json"))
    with pytest.raises(ValueError, match="sensitive"):
        reject_if_private_output_path(Path("C:/Users/TANMAY/Lumint/.env/manifest.json"))

def test_normalize_label_from_score():
    assert normalize_label_from_score(85.0) == "HIGH"
    assert normalize_label_from_score(40.0) == "SUSPICIOUS"
    assert normalize_label_from_score(10.0) == "CLEAN"

def test_phishtank_adapter(tmp_path):
    # Create sample phishtank json
    pt_data = [
        {
            "phish_id": "123",
            "url": "http://phish.com/login",
            "verified": "yes",
            "online": "yes"
        },
        {
            "phish_id": "456",
            "url": "http://safe.com/home",
            "verified": "no",
            "online": "no"
        }
    ]
    pt_file = tmp_path / "phishtank.json"
    with open(pt_file, "w") as f:
        json.dump(pt_data, f)
        
    out_manifest = tmp_path / "manifest.json"
    res = convert_phishtank_to_manifest(pt_file, out_manifest)
    assert res.records_written == 2
    
    from research.dataset_manifest import load_manifest
    manifest = load_manifest(str(out_manifest))
    assert len(manifest.records) == 2
    assert manifest.records[0].dataset_type == DatasetType.URL
    assert manifest.records[0].label == "HIGH"
    assert manifest.records[1].label == "SUSPICIOUS"

def test_mendeley_phishing_adapter(tmp_path):
    csv_file = tmp_path / "mendeley.csv"
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["url", "label"])
        writer.writerow(["http://bad.com", "1"])
        writer.writerow(["http://good.com", "0"])
        
    out_manifest = tmp_path / "manifest.json"
    res = convert_mendeley_phishing_to_manifest(csv_file, out_manifest)
    assert res.records_written == 2
    
    from research.dataset_manifest import load_manifest
    manifest = load_manifest(str(out_manifest))
    assert len(manifest.records) == 2
    assert manifest.records[0].label == "HIGH"
    assert manifest.records[1].label == "CLEAN"

def test_upi_receipts_adapter(tmp_path):
    # Setup folders
    genuine_dir = tmp_path / "genuine"
    genuine_dir.mkdir()
    forged_dir = tmp_path / "forged_utr"
    forged_dir.mkdir()
    
    # Create mock files
    g_file = genuine_dir / "receipt1.jpg"
    g_file.write_text("dummy genuine image")
    
    f_file = forged_dir / "receipt2.png"
    f_file.write_text("dummy forged image")
    
    # Metadata json
    meta_data = {
        "receipt1.jpg": {
            "ocr_text": "UPI Ref No: 123456789012. Genuine receipt text.",
            "phone": "9876543210"
        },
        "receipt2.png": {
            "ocr_text": "Fake UPI receipt with UTR 000000000000",
            "email": "attacker@spam.com"
        }
    }
    meta_file = tmp_path / "metadata.json"
    with open(meta_file, "w") as f:
        json.dump(meta_data, f)
        
    out_manifest = tmp_path / "manifest.json"
    res = convert_upi_receipts_to_manifest(tmp_path, meta_file, out_manifest)
    assert res.records_written == 2
    
    from research.dataset_manifest import load_manifest
    manifest = load_manifest(str(out_manifest))
    assert len(manifest.records) == 2
    
    # Check that privacy redactions were applied to ocr_text in metadata
    r1 = next(r for r in manifest.records if "receipt1" in r.path_or_value)
    r2 = next(r for r in manifest.records if "receipt2" in r.path_or_value)
    
    assert "UTR_HASH" in r1.metadata["ocr_text"]
    assert "PHONE_HASH" in r1.metadata["phone"]
    
    assert r2.label == "HIGH"
    assert "EMAIL_HASH" in r2.metadata["email"]

def test_document_forensics_adapter(tmp_path):
    clean_dir = tmp_path / "clean"
    clean_dir.mkdir()
    forged_dir = tmp_path / "forged"
    forged_dir.mkdir()
    
    (clean_dir / "doc1.pdf").write_text("clean pdf content")
    (forged_dir / "doc2.png").write_text("forged png content")
    
    out_manifest = tmp_path / "manifest.json"
    res = convert_document_forensics_to_manifest(tmp_path, out_manifest)
    assert res.records_written == 2
    
    from research.dataset_manifest import load_manifest
    manifest = load_manifest(str(out_manifest))
    assert len(manifest.records) == 2
    
    r1 = next(r for r in manifest.records if "doc1.pdf" in r.path_or_value)
    r2 = next(r for r in manifest.records if "doc2.png" in r.path_or_value)
    
    assert r1.label == "CLEAN"
    assert r2.label == "HIGH"

def test_dataset_validator():
    # Record with phone, email, and absolute system path in text
    record = DatasetRecord(
        id="rec-val-1",
        dataset_type=DatasetType.URL,
        path_or_value="http://evil.com/test?token=secret123",
        label="HIGH",
        split=DatasetSplit.BENCHMARK,
        source="test",
        metadata={
            "ocr_text": "Send money to hack@malicious.com or call 91-9999999999. File is at C:\\Users\\Admin\\Desktop\\secret.txt",
            "upi_id": "test@paytm"
        }
    )
    
    # Record with duplicate value to trigger dup warning
    record_dup = DatasetRecord(
        id="rec-val-2",
        dataset_type=DatasetType.URL,
        path_or_value="http://evil.com/test?token=secret123",
        label="HIGH",
        split=DatasetSplit.BENCHMARK,
        source="test"
    )
    
    manifest = DatasetManifest(
        name="Leak Test Manifest",
        version="1.0.0",
        description="Testing validator rules",
        records=[record, record_dup]
    )
    
    issues = validate_manifest_for_experiment(manifest)
    val_res = summarize_validation(issues)
    
    # We should have found warnings for leaks and duplicates
    assert val_res["warning_count"] > 0
    codes = val_res["codes"]
    assert "DUPLICATE_VALUE" in codes
    assert "LEAK_EMAIL" in codes
    assert "LEAK_PHONE" in codes
    assert "LEAK_USERNAME" in codes
    assert "LEAK_UPI_ID" in codes
    assert "URL_QUERY_PARAMS" in codes
    assert "EXTREME_IMBALANCE" in codes

def test_dataset_card_generation():
    card = DatasetCard(
        dataset_name="Test Card",
        dataset_type="URL",
        record_count=10,
        label_distribution={"CLEAN": 5, "SUSPICIOUS": 3, "HIGH": 2},
        source_description="A test dataset description.",
        privacy_notes="Cleaned & Verified",
        known_limitations="None",
        recommended_use="Benchmarking"
    )
    
    md = dataset_card_to_markdown(card)
    assert "# Dataset Card: Test Card" in md
    assert "- **Total Records**: 10" in md
    assert "Cleaned & Verified" in md

def test_paper_experiment_orchestrator_dry_run():
    fixtures_dir = Path(__file__).resolve().parents[1] / "research" / "fixtures"
    registry_file = fixtures_dir / "paper_experiments.json"
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        out_path = Path(tmp_dir) / "output"
        summary = run_experiments(
            registry_path=registry_file,
            output_dir=out_path,
            synthetic_only=True,
            real_manifest_dir=out_path,
            with_consensus=True,
            with_ablation=True,
            dry_run=True
        )
        
        # In dry run, it should list experiments but not write outputs
        assert len(summary["experiments_run"]) > 0
        assert not (out_path / "paper_run_summary.json").exists()

def test_build_paper_bundle_placeholders(tmp_path):
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    paper_dir = tmp_path / "paper"
    
    fixtures_dir = Path(__file__).resolve().parents[1] / "research" / "fixtures"
    registry_file = fixtures_dir / "paper_experiments.json"
    
    build_bundle(
        source_dir=source_dir,
        paper_dir=paper_dir,
        registry_path=registry_file,
        dry_run=False
    )
    
    # Check that placeholders and indices are created
    assert (paper_dir / "tables" / "index.md").exists()
    assert (paper_dir / "tables" / "table_1_dataset_summary.md").exists()
    assert (paper_dir / "tables" / "table_2_detection_performance.md").exists()
    assert (paper_dir / "tables" / "table_3_latency_profile.md").exists()
    assert (paper_dir / "tables" / "table_4_ablation.md").exists()
    assert (paper_dir / "tables" / "table_5_consensus_agreement.md").exists()
    
    # Verify content in Table 1
    t1_content = (paper_dir / "tables" / "table_1_dataset_summary.md").read_text(encoding="utf-8")
    assert "# Table 1: Lumint Evaluation Datasets Summary" in t1_content
    assert "url_detection_synthetic" in t1_content
