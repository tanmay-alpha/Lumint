import pytest
from research.ablation import AblationStudyResult, AblationResult
from research.paper_tables import (
    metrics_to_markdown_table,
    latency_to_markdown_table,
    ablation_to_markdown_table,
    agreement_to_markdown_table,
    error_taxonomy_to_markdown_table,
    metrics_to_csv,
    metrics_to_latex_table
)

def test_metrics_to_markdown_table():
    metrics = {"accuracy": 0.90, "f1": 0.85, "precision": 0.88, "recall": 0.82}
    confidence_intervals = {
        "accuracy": (0.85, 0.90, 0.95),
        "f1": (0.80, 0.85, 0.90),
        "precision": (0.83, 0.88, 0.93),
        "recall": (0.78, 0.82, 0.86)
    }
    
    # Without CI
    tbl = metrics_to_markdown_table(metrics)
    assert "| ACCURACY |" in tbl
    assert "0.9000" in tbl
    
    # With CI
    tbl_ci = metrics_to_markdown_table(metrics, confidence_intervals)
    assert "[0.8500, 0.9500]" in tbl_ci

def test_latency_to_markdown_table():
    latency = {"mean": 15.4, "median": 12.0, "p95": 25.0, "p99": 40.0, "min": 2.0, "max": 100.0}
    confidence_intervals = {"mean": (12.0, 15.4, 18.0)}
    
    tbl = latency_to_markdown_table(latency)
    assert "15.40" in tbl
    
    tbl_ci = latency_to_markdown_table(latency, confidence_intervals)
    assert "[12.00, 18.00]" in tbl_ci

def test_ablation_to_markdown_table():
    study = AblationStudyResult(
        study_id="study-1",
        created_at="2026-06-03T12:00:00",
        experiment_id="exp-1",
        dataset_name="test",
        module_name="fusion",
        best_variant="var1",
        variants=[
            AblationResult(
                variant_name="var1",
                record_count=10,
                metrics={"f1": 0.90, "accuracy": 0.92},
                latency={"mean": 15.0}
            ),
            AblationResult(
                variant_name="var2",
                record_count=10,
                metrics={"f1": 0.80, "accuracy": 0.82},
                latency={"mean": 12.0}
            )
        ]
    )
    tbl = ablation_to_markdown_table(study)
    assert "var1" in tbl
    assert "var2" in tbl
    assert "0.9000" in tbl

def test_metrics_to_csv():
    metrics = {"accuracy": 0.90, "f1": 0.85}
    csv_str = metrics_to_csv(metrics)
    assert "Metric,Value" in csv_str
    assert "ACCURACY,0.900000" in csv_str

def test_metrics_to_latex_table():
    metrics = {"accuracy": 0.90, "f1": 0.85, "precision": 0.88, "recall": 0.82}
    confidence_intervals = {
        "accuracy": (0.85, 0.90, 0.95),
        "f1": (0.80, 0.85, 0.90)
    }
    latex = metrics_to_latex_table(metrics, confidence_intervals)
    assert "\\begin{table}" in latex
    assert "ACCURACY" in latex
    assert "[0.8500, 0.9500]" in latex
