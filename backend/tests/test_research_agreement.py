import tempfile
from pathlib import Path
from research.consensus_adapters import ConsensusResult
from research.agreement import compare_predictions_to_consensus, compute_consensus_confusion_matrix
from research.experiment_runner import ExperimentRecordResult, run_lumint_experiment, ExperimentResult
from research.dataset_manifest import DatasetManifest, DatasetRecord, DatasetType, DatasetSplit
from research.report_writer import write_markdown_report

def test_compare_predictions_to_consensus():
    predictions = [
        ExperimentRecordResult(record_id="rec-1", true_label="HIGH", predicted_label="HIGH", predicted_score=90.0, latency_ms=1.0),
        ExperimentRecordResult(record_id="rec-2", true_label="CLEAN", predicted_label="CLEAN", predicted_score=5.0, latency_ms=1.0),
        ExperimentRecordResult(record_id="rec-3", true_label="HIGH", predicted_label="CLEAN", predicted_score=10.0, latency_ms=1.0),
        ExperimentRecordResult(record_id="rec-4", true_label="SUSPICIOUS", predicted_label="HIGH", predicted_score=75.0, latency_ms=1.0),
    ]
    
    consensus = {
        "rec-1": ConsensusResult(record_id="rec-1", provider="fixture", target="t1", consensus_label="HIGH", confidence=0.9),
        "rec-2": ConsensusResult(record_id="rec-2", provider="fixture", target="t2", consensus_label="CLEAN", confidence=0.9),
        "rec-3": ConsensusResult(record_id="rec-3", provider="fixture", target="t3", consensus_label="HIGH", confidence=0.9),
        "rec-4": ConsensusResult(record_id="rec-4", provider="fixture", target="t4", consensus_label="UNKNOWN", confidence=0.0)
    }
    
    res = compare_predictions_to_consensus(predictions, consensus)
    
    # rec-4 is UNKNOWN -> excluded from comparable (so comparable = 3, total = 4, unknown = 1)
    assert res.total_records == 4
    assert res.comparable_records == 3
    assert res.unknown_count == 1
    
    # rec-1 agrees (HIGH/HIGH)
    # rec-2 agrees (CLEAN/CLEAN)
    # rec-3 disagrees (prediction CLEAN, consensus HIGH)
    assert res.agreement_count == 2
    assert res.disagreement_count == 1
    assert res.agreement_rate == pytest.approx(2.0 / 3.0)
    
    # Disagreements details
    assert len(res.disagreements) == 1
    assert res.disagreements[0]["record_id"] == "rec-3"
    assert res.disagreements[0]["predicted_label"] == "CLEAN"
    assert res.disagreements[0]["consensus_label"] == "HIGH"

def test_consensus_confusion_matrix():
    predictions = [
        ExperimentRecordResult(record_id="rec-1", true_label="HIGH", predicted_label="HIGH", predicted_score=90.0, latency_ms=1.0),
        ExperimentRecordResult(record_id="rec-2", true_label="CLEAN", predicted_label="CLEAN", predicted_score=5.0, latency_ms=1.0),
        ExperimentRecordResult(record_id="rec-3", true_label="HIGH", predicted_label="CLEAN", predicted_score=10.0, latency_ms=1.0),
        ExperimentRecordResult(record_id="rec-4", true_label="SUSPICIOUS", predicted_label="HIGH", predicted_score=75.0, latency_ms=1.0),
    ]
    
    consensus = {
        "rec-1": ConsensusResult(record_id="rec-1", provider="fixture", target="t1", consensus_label="HIGH", confidence=0.9), # TP (both positive)
        "rec-2": ConsensusResult(record_id="rec-2", provider="fixture", target="t2", consensus_label="CLEAN", confidence=0.9), # TN (both negative)
        "rec-3": ConsensusResult(record_id="rec-3", provider="fixture", target="t3", consensus_label="HIGH", confidence=0.9), # FN (true positive, pred negative)
        "rec-4": ConsensusResult(record_id="rec-4", provider="fixture", target="t4", consensus_label="UNKNOWN", confidence=0.0) # Ignored
    }
    
    matrix = compute_consensus_confusion_matrix(predictions, consensus)
    assert matrix["TP"] == 1
    assert matrix["TN"] == 1
    assert matrix["FN"] == 1
    assert matrix["FP"] == 0
    assert matrix["support"] == 3

def test_report_writer_includes_consensus():
    metrics = {"accuracy": 1.0, "precision": 1.0, "recall": 1.0, "f1": 1.0, "TP": 1, "TN": 0, "FP": 0, "FN": 0}
    latency = {"mean": 1.0, "median": 1.0, "p95": 1.0, "p99": 1.0, "min": 1.0, "max": 1.0}
    
    predictions = [
        ExperimentRecordResult(record_id="rec-1", true_label="HIGH", predicted_label="HIGH", predicted_score=90.0, latency_ms=1.0)
    ]
    
    consensus = {
        "rec-1": ConsensusResult(record_id="rec-1", provider="fixture", target="t1", consensus_label="HIGH", confidence=0.9)
    }
    
    agreement = compare_predictions_to_consensus(predictions, consensus)
    consensus_metrics = compute_consensus_confusion_matrix(predictions, consensus)
    
    res = ExperimentResult(
        experiment_id="exp-test-123",
        dataset_name="test_ds",
        model_name="lumint_url",
        record_count=1,
        metrics=metrics,
        latency=latency,
        results=predictions,
        agreement=agreement,
        consensus_metrics=consensus_metrics
    )
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        report_path = Path(tmp_dir) / "report.md"
        write_markdown_report(res, str(report_path))
        
        assert report_path.exists()
        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()
            assert "External Consensus Agreement" in content
            assert "Agreement Rate" in content
            assert "Disagreement Analysis" in content
            assert "Consensus Confusion Matrix" in content

import pytest
