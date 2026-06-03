from research.experiment_runner import ExperimentResult

def write_markdown_report(result: ExperimentResult, output_path: str) -> None:
    metrics = result.metrics
    latency = result.latency
    
    # Sort top errors if results are available
    error_summary_lines = []
    if hasattr(result, "results") and result.results:
        errors = [r.error for r in result.results if r.error]
        error_count = len(errors)
        error_summary_lines.append(f"* **Total Errors/Exceptions**: `{error_count}`")
        if errors:
            from collections import Counter
            counts = Counter(errors)
            error_summary_lines.append("\n### Frequent Errors")
            for err, count in counts.most_common(5):
                error_summary_lines.append(f"- `{err}` (occurrences: {count})")
    else:
        error_summary_lines.append(f"* **Total Errors/Exceptions**: `0`")

    # Generate Per-Record Table
    records_table_rows = []
    if hasattr(result, "results") and result.results:
        for r in result.results:
            err_str = f"`{r.error}`" if r.error else "None"
            records_table_rows.append(
                f"| `{r.record_id}` | `{r.true_label}` | `{r.predicted_label}` | {r.predicted_score:.1f} | {r.latency_ms:.2f} ms | {err_str} |"
            )
    else:
        records_table_rows.append("| - | - | - | - | - | - |")
        
    records_table = "\n".join(records_table_rows)

    report_content = f"""# Lumint Benchmark Report

## Experiment Metadata
* **Experiment ID**: `{result.experiment_id}`
* **Dataset Name**: `{result.dataset_name}`
* **Module Name**: `{result.model_name}`
* **Record Count**: {result.record_count}
* **Created At**: `{result.created_at}`
* **Notes**: {result.notes or "No additional notes provided."}

## Classification Performance Metrics
| Metric | Value | Description |
| :--- | :---: | :--- |
| **Accuracy** | {metrics.get("accuracy", 0.0):.4f} | Overall correctness of predictions |
| **Precision** | {metrics.get("precision", 0.0):.4f} | Ratio of true positive to all positive predictions |
| **Recall** | {metrics.get("recall", 0.0):.4f} | Ratio of true positive to all actual positive cases |
| **F1-Score** | {metrics.get("f1", 0.0):.4f} | Harmonic mean of Precision and Recall |
| **False Positive Rate (FPR)** | {metrics.get("fpr", 0.0):.4f} | Ratio of negative cases incorrectly predicted as positive |
| **False Negative Rate (FNR)** | {metrics.get("fnr", 0.0):.4f} | Ratio of positive cases incorrectly predicted as negative |

### Confusion Matrix
* **True Positives (TP)**: `{metrics.get("TP", 0)}`
* **False Positives (FP)**: `{metrics.get("FP", 0)}`
* **True Negatives (TN)**: `{metrics.get("TN", 0)}`
* **False Negatives (FN)**: `{metrics.get("FN", 0)}`

## Latency Metrics
| Metric | Latency (ms) | Description |
| :--- | :---: | :--- |
| **Mean** | {latency.get("mean", 0.0):.2f} ms | Average execution time |
| **Median** | {latency.get("median", 0.0):.2f} ms | 50th percentile execution time |
| **95th Percentile (P95)** | {latency.get("p95", 0.0):.2f} ms | 95% of execution times are below this value |
| **99th Percentile (P99)** | {latency.get("p99", 0.0):.2f} ms | 99% of execution times are below this value |
| **Minimum** | {latency.get("min", 0.0):.2f} ms | Fastest execution time |
| **Maximum** | {latency.get("max", 0.0):.2f} ms | Slowest execution time |

## Error Summary
{"".join(error_summary_lines)}

## Per-Record Results
| Record ID | True Label | Predicted Label | Score | Latency | Error |
| :--- | :--- | :--- | :--- | :--- | :--- |
{records_table}

## Limitations
1. **Deterministic Local Benchmark**: The current execution environment utilizes synthetic fixtures and rules engines, omitting real-time networking and database constraints.
2. **No External Consensus Yet**: The report represents standalone model classification without cross-reference or voting/consensus systems.
3. **No Production Dataset Yet**: Benchmark is run on mock/curated records, not active production streams.
"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report_content)
