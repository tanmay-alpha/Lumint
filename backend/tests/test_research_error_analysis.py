import pytest
from research.dataset_manifest import DatasetManifest, DatasetRecord, DatasetType
from research.experiment_runner import ExperimentRecordResult
from research.error_analysis import (
    classify_error_case,
    analyze_errors,
    summarize_top_errors,
    ErrorCase
)

def test_classify_error_case():
    # False Negative
    error_case = classify_error_case(
        record_id="rec-1",
        true_label="HIGH",
        pred_label="SAFE",
        pred_score=0.1,
        raw_output={"explanation": ["no active signals"]}
    )
    assert error_case is not None
    assert error_case.error_type == "FALSE_NEGATIVE"
    assert error_case.taxonomy_category == "NO_ACTIVE_SIGNALS"
    
    # Test correlation miss (score between 0.3 and 0.5)
    error_case_corr = classify_error_case(
        record_id="rec-1",
        true_label="HIGH",
        pred_label="SAFE",
        pred_score=0.4,
        raw_output={"correlation_flags": ["some_flag"]}
    )
    assert error_case_corr.taxonomy_category == "CORRELATION_MISS"
    
    # Test False Positive
    error_case_fp = classify_error_case(
        record_id="rec-2",
        true_label="SAFE",
        pred_label="HIGH",
        pred_score=90.0,
        raw_output={}
    )
    assert error_case_fp.error_type == "FALSE_POSITIVE"
    assert error_case_fp.taxonomy_category == "FORENSICS_FAILURE"

def test_analyze_and_summarize_errors():
    record_1 = DatasetRecord(
        id="rec-1",
        dataset_type=DatasetType.URL,
        path_or_value="https://test.com",
        label="HIGH",
        split="BENCHMARK",
        source="test"
    )
    record_2 = DatasetRecord(
        id="rec-2",
        dataset_type=DatasetType.URL,
        path_or_value="https://test-2.com",
        label="SAFE",
        split="BENCHMARK",
        source="test"
    )
    
    # Result 1: FN
    res1 = ExperimentRecordResult(
        record_id="rec-1",
        true_label="HIGH",
        predicted_label="SAFE",
        predicted_score=0.1,
        latency_ms=10.0,
        raw_result={"explanation": ["no active signals"]}
    )
    # Result 2: FP
    res2 = ExperimentRecordResult(
        record_id="rec-2",
        true_label="SAFE",
        predicted_label="HIGH",
        predicted_score=0.9,
        latency_ms=10.0,
        raw_result={}
    )
    
    manifest = DatasetManifest(name="test", version="1", records=[record_1, record_2])
    error_cases = analyze_errors([res1, res2], manifest)
    
    assert len(error_cases) == 2
    types = [e.error_type for e in error_cases]
    assert "FALSE_NEGATIVE" in types
    assert "FALSE_POSITIVE" in types
    
    summary = summarize_top_errors(error_cases)
    assert summary["total_errors"] == 2
    assert summary["error_types"]["FALSE_NEGATIVE"] == 1
    assert summary["error_types"]["FALSE_POSITIVE"] == 1
    assert len(summary["categories"]) > 0
    assert len(summary["samples"]) > 0
