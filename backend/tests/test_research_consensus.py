import os
import pytest
from pathlib import Path
from research.consensus_adapters import (
    normalize_consensus_label,
    fixture_consensus_lookup,
    load_fixture_consensus,
    get_available_providers
)

def test_normalize_consensus_label():
    # Test high values
    assert normalize_consensus_label("HIGH") == "HIGH"
    assert normalize_consensus_label("malicious") == "HIGH"
    assert normalize_consensus_label("phishing") == "HIGH"
    assert normalize_consensus_label(True) == "HIGH"
    assert normalize_consensus_label(1) == "HIGH"
    assert normalize_consensus_label("likely_forged") == "HIGH"

    # Test suspicious values
    assert normalize_consensus_label("SUSPICIOUS") == "SUSPICIOUS"
    assert normalize_consensus_label("warning") == "SUSPICIOUS"
    assert normalize_consensus_label("unsafe") == "SUSPICIOUS"

    # Test clean values
    assert normalize_consensus_label("CLEAN") == "CLEAN"
    assert normalize_consensus_label("benign") == "CLEAN"
    assert normalize_consensus_label("safe") == "CLEAN"
    assert normalize_consensus_label(False) == "CLEAN"
    assert normalize_consensus_label(0) == "CLEAN"

    # Test unknown/missing
    assert normalize_consensus_label(None) == "UNKNOWN"
    assert normalize_consensus_label("unknown") == "UNKNOWN"
    assert normalize_consensus_label("missing") == "UNKNOWN"
    assert normalize_consensus_label("some_other_value") == "UNKNOWN"

def test_fixture_consensus_loading():
    fixtures_dir = Path(__file__).resolve().parents[1] / "research" / "fixtures" / "consensus"
    fixture_path = fixtures_dir / "url_consensus_fixture.json"
    
    assert fixture_path.exists()
    
    # Check lookup of existing record
    res = fixture_consensus_lookup("url-1", fixture_path)
    assert res is not None
    assert res.record_id == "url-1"
    assert res.consensus_label == "HIGH"
    assert res.confidence == 0.96
    assert len(res.evidence) > 0

    # Check lookup of non-existing record
    missing_res = fixture_consensus_lookup("non_existent_id", fixture_path)
    assert missing_res is None

def test_load_all_fixture_consensus():
    fixtures_dir = Path(__file__).resolve().parents[1] / "research" / "fixtures" / "consensus"
    fixture_path = fixtures_dir / "url_consensus_fixture.json"
    
    consensus_dict = load_fixture_consensus(fixture_path)
    assert len(consensus_dict) == 5
    assert "url-1" in consensus_dict
    assert consensus_dict["url-1"].consensus_label == "HIGH"

def test_get_available_providers_never_exposes_keys():
    # Set mock keys in env
    os.environ["VIRUSTOTAL_API_KEY"] = "secret_vt_key"
    os.environ["URLSCAN_API_KEY"] = "secret_us_key"
    os.environ["ABUSEIPDB_API_KEY"] = "secret_ab_key"
    
    try:
        providers = get_available_providers()
        assert len(providers) == 3
        for p in providers:
            assert p.available is True
            assert p.reason is None
            # Ensure the reason or name does not contain the key value
            assert "secret" not in p.name
            if p.reason:
                assert "secret" not in p.reason
    finally:
        # Restore env
        del os.environ["VIRUSTOTAL_API_KEY"]
        del os.environ["URLSCAN_API_KEY"]
        del os.environ["ABUSEIPDB_API_KEY"]
        
    # Test when missing
    providers_missing = get_available_providers()
    for p in providers_missing:
        assert p.available is False
        assert p.reason is not None
        assert "missing" in p.reason.lower()
