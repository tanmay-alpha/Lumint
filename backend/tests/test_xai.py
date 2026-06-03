import pytest
from app.core.xai import (
    normalize_contributions,
    contributions_from_indicators,
    contributions_from_feature_map,
    get_feature_contributions
)

def test_normalize_contributions_sums_to_100():
    items = [
        {"name": "Feature A", "raw_score": 10.0},
        {"name": "Feature B", "raw_score": 30.0},
        {"name": "Feature C", "raw_score": 60.0}
    ]
    normalized = normalize_contributions(items)
    
    # Check ordering is descending by percentage
    assert normalized[0]["name"] == "Feature C"
    assert normalized[1]["name"] == "Feature B"
    assert normalized[2]["name"] == "Feature A"
    
    assert normalized[0]["contribution_pct"] == 60.0
    assert normalized[1]["contribution_pct"] == 30.0
    assert normalized[2]["contribution_pct"] == 10.0
    
    total_pct = sum(item["contribution_pct"] for item in normalized)
    assert abs(total_pct - 100.0) < 1e-5

def test_normalize_contributions_zero_total():
    items = [
        {"name": "Feature A", "raw_score": 0.0},
        {"name": "Feature B", "raw_score": 0.0}
    ]
    normalized = normalize_contributions(items)
    
    for item in normalized:
        assert item["contribution_pct"] == 0.0

def test_contributions_from_indicators_supports_dicts():
    indicators = [
        {"rule": "is_encrypted", "score": 20, "detail": "PDF is password protected"},
        {"rule": "adobe_photoshop", "score": 80, "detail": "Photoshop signature detected in metadata"}
    ]
    contributions = contributions_from_indicators(indicators)
    
    assert len(contributions) == 2
    assert contributions[0]["name"] == "Adobe Photoshop"
    assert contributions[0]["raw_score"] == 80.0
    assert contributions[0]["direction"] == "risk_increasing"
    assert contributions[0]["evidence"] == "Photoshop signature detected in metadata"
    
    assert contributions[1]["name"] == "Is Encrypted"
    assert contributions[1]["raw_score"] == 20.0
    assert contributions[1]["direction"] == "risk_increasing"
    assert contributions[1]["evidence"] == "PDF is password protected"

def test_feature_map_boolean_and_numeric():
    feature_map = {
        "is_suspicious_domain": True,
        "is_safe_connection": False,
        "transaction_count": 5.0,
        "threat_severity": "HIGH",
        "validation_state": "CLEAN"
    }
    weights = {
        "is_suspicious_domain": 1.5,
        "transaction_count": 2.0
    }
    
    contributions = contributions_from_feature_map(feature_map, weights)
    
    # Verify suspicious domain is boosted by weight 1.5: 40 * 1.5 = 60
    susp_domain = next(c for c in contributions if c["name"] == "Is Suspicious Domain")
    assert susp_domain["raw_score"] == 60.0
    assert susp_domain["direction"] == "risk_increasing"
    
    # Verify transaction count is boosted by weight 2.0: 5.0 * 2.0 = 10
    tx_count = next(c for c in contributions if c["name"] == "Transaction Count")
    assert tx_count["raw_score"] == 10.0
    assert tx_count["direction"] == "risk_increasing"
    
    # Verify threat severity string "HIGH" returns positive risk_increasing
    threat = next(c for c in contributions if c["name"] == "Threat Severity")
    assert threat["raw_score"] == 50.0
    assert threat["direction"] == "risk_increasing"
    
    # Verify validation state string "CLEAN" returns risk_decreasing
    val_state = next(c for c in contributions if c["name"] == "Validation State")
    assert val_state["raw_score"] == -20.0
    assert val_state["direction"] == "risk_decreasing"

def test_get_feature_contributions_fallback():
    # Test fallback routes on empty / missing inputs
    assert get_feature_contributions() == []
    
    # Test indicators input
    indicators = [{"rule": "test_rule", "score": 10, "detail": "test"}]
    res = get_feature_contributions(indicators=indicators)
    assert len(res) == 1
    assert res[0]["name"] == "Test Rule"
    
    # Test features input
    features = {"test_feature": 10.0}
    res2 = get_feature_contributions(features=features)
    assert len(res2) == 1
    assert res2[0]["name"] == "Test Feature"
