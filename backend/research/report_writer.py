from research.experiment_runner import ExperimentResult

def write_markdown_report(result: ExperimentResult, output_path: str) -> None:
    metrics = result.metrics
    latency = result.latency
    
    report_content = f"""# Experiment Evaluation Report: {result.model_name}

## Metadata
* **Experiment ID**: `{result.experiment_id}`
* **Model Evaluated**: `{result.model_name}`
* **Dataset Used**: `{result.dataset_name}`
* **Total Records**: {result.record_count}
* **Execution Time**: {result.created_at}
* **Notes**: {result.notes or "No additional notes provided."}

## Classification Performance Metrics
| Metric | Value | Description |
| :--- | :---: | :--- |
| **Accuracy** | {metrics.get("accuracy", 0.0):.4f} | Overall correctness of predictions |
| **Precision** | {metrics.get("precision", 0.0):.4f} | Proportion of positive predictions that are correct |
| **Recall** | {metrics.get("recall", 0.0):.4f} | Proportion of actual positives identified |
| **F1-Score** | {metrics.get("f1", 0.0):.4f} | Harmonic mean of Precision and Recall |
| **False Positive Rate (FPR)** | {metrics.get("fpr", 0.0):.4f} | Proportion of clean instances flagged as fraud |
| **False Negative Rate (FNR)** | {metrics.get("fnr", 0.0):.4f} | Proportion of fraud instances missed |
| **Support Count** | {metrics.get("support", 0)} | Total number of test records |

### Confusion Matrix
| Category | Count | Description |
| :--- | :---: | :--- |
| **True Positives (TP)** | {metrics.get("TP", 0)} | Fraud cases correctly flagged |
| **False Positives (FP)** | {metrics.get("FP", 0)} | Clean cases incorrectly flagged |
| **True Negatives (TN)** | {metrics.get("TN", 0)} | Clean cases correctly passed |
| **False Negatives (FN)** | {metrics.get("FN", 0)} | Fraud cases missed |

## Latency Summary
| Metric | Latency (ms) |
| :--- | :---: |
| **Mean** | {latency.get("mean", 0.0):.2f} ms |
| **Median** | {latency.get("median", 0.0):.2f} ms |
| **95th Percentile (P95)** | {latency.get("p95", 0.0):.2f} ms |
| **99th Percentile (P99)** | {latency.get("p99", 0.0):.2f} ms |
| **Minimum** | {latency.get("min", 0.0):.2f} ms |
| **Maximum** | {latency.get("max", 0.0):.2f} ms |

## Limitations & Research Scope
1. **Rule-Based Heuristic**: The evaluated baseline is rule-based and lacks the deep semantic or spatial context utilized in Lumint's core machine learning engines.
2. **Environment Variance**: Latency timings reflect standard execution on local test hardware and will vary when deployed on distributed or edge environments.
3. **Dataset Limits**: The current manifest evaluation split serves as a control baseline only. True performance evaluations should be conducted against full labeled research datasets.
"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report_content)
