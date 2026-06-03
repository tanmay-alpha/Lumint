import csv
import io
from typing import Dict, Any, Optional, Tuple, List
from research.ablation import AblationStudyResult

def format_ci(val: float, ci: Optional[Tuple[float, float, float]]) -> str:
    if ci is None:
        return f"{val:.4f}"
    lower, mean_val, upper = ci
    return f"{mean_val:.4f} [{lower:.4f}, {upper:.4f}]"

def metrics_to_markdown_table(
    metrics: Dict[str, Any],
    confidence_intervals: Optional[Dict[str, Tuple[float, float, float]]] = None
) -> str:
    """
    Generates a markdown table for binary classification metrics with optional confidence intervals.
    """
    lines = []
    if confidence_intervals:
        lines.append("| Metric | Value (Point Estimate) | 95% Confidence Interval |")
        lines.append("|---|---|---|")
        for key in ["accuracy", "precision", "recall", "f1", "fpr", "fnr"]:
            if key in metrics:
                val = metrics[key]
                ci_str = ""
                if key in confidence_intervals:
                    lower, _, upper = confidence_intervals[key]
                    ci_str = f"[{lower:.4f}, {upper:.4f}]"
                lines.append(f"| {key.upper()} | {val:.4f} | {ci_str} |")
    else:
        lines.append("| Metric | Value |")
        lines.append("|---|---|")
        for key in ["accuracy", "precision", "recall", "f1", "fpr", "fnr"]:
            if key in metrics:
                val = metrics[key]
                lines.append(f"| {key.upper()} | {val:.4f} |")
                
    return "\n".join(lines)

def latency_to_markdown_table(
    latency: Dict[str, float],
    confidence_intervals: Optional[Dict[str, Tuple[float, float, float]]] = None
) -> str:
    """
    Generates a markdown table representing latency statistics.
    """
    lines = [
        "| Statistic | Value (ms) | 95% Confidence Interval |" if confidence_intervals else "| Statistic | Value (ms) |",
        "|---|---|---|" if confidence_intervals else "|---|---|",
    ]
    
    for key in ["mean", "median", "p95", "p99", "min", "max"]:
        if key in latency:
            val = latency[key]
            if confidence_intervals and key in confidence_intervals:
                lower, _, upper = confidence_intervals[key]
                lines.append(f"| {key.capitalize()} | {val:.2f} | [{lower:.2f}, {upper:.2f}] |")
            else:
                lines.append(f"| {key.capitalize()} | {val:.2f} |" + ("" if not confidence_intervals else " - |"))
                
    return "\n".join(lines)

def ablation_to_markdown_table(ablation_study: AblationStudyResult) -> str:
    """
    Generates a markdown comparison table for all ablation study variants.
    """
    lines = [
        "| Variant Name | Description | Record Count | Accuracy | F1 Score | Mean Latency (ms) |",
        "|---|---|---|---|---|---|",
    ]
    
    for var in ablation_study.variants:
        acc = var.metrics.get("accuracy", 0.0)
        f1 = var.metrics.get("f1", 0.0)
        mean_lat = var.latency.get("mean", 0.0)
        
        is_best = " (Best)" if ablation_study.best_variant == var.variant_name else ""
        lines.append(
            f"| **{var.variant_name}**{is_best} | {var.notes or ''} | {var.record_count} | {acc:.4f} | {f1:.4f} | {mean_lat:.2f} |"
        )
        
    return "\n".join(lines)

def agreement_to_markdown_table(agreement_metrics: Dict[str, Any]) -> str:
    """
    Generates a markdown representation of the agreement and consensus metrics.
    """
    lines = [
        "| Agreement Indicator | Value / Rate | Interpretation |",
        "|---|---|---|",
    ]
    
    for key, val in agreement_metrics.items():
        desc = ""
        if key == "cohen_kappa":
            desc = "Cohen's Kappa coefficient (inter-annotator agreement strength)"
            if val is not None:
                lines.append(f"| Cohen's Kappa | {val:.4f} | {desc} |")
        elif key == "overall_agreement_rate":
            desc = "Raw percentage of matching classifications"
            lines.append(f"| Overall Agreement Rate | {val:.2f}% | {desc} |")
        elif key == "clean_agreement_rate":
            desc = "Matching rate on CLEAN verdicts"
            lines.append(f"| Clean Agreement Rate | {val:.2f}% | {desc} |")
        elif key == "suspicious_agreement_rate":
            desc = "Matching rate on SUSPICIOUS verdicts"
            lines.append(f"| Suspicious Agreement Rate | {val:.2f}% | {desc} |")
        elif key == "high_agreement_rate":
            desc = "Matching rate on HIGH verdicts"
            lines.append(f"| High Agreement Rate | {val:.2f}% | {desc} |")
        elif key == "consensus_coverage":
            desc = "Fraction of records matching consensus benchmark criteria"
            lines.append(f"| Consensus Coverage | {val:.2f}% | {desc} |")
            
    return "\n".join(lines)

def error_taxonomy_to_markdown_table(error_summary: Dict[str, Any]) -> str:
    """
    Generates a markdown table for the top error categories.
    """
    total = error_summary.get("total_errors", 0)
    lines = [
        "| Taxonomy Category | Count | Proportion |",
        "|---|---|---|",
    ]
    
    categories = error_summary.get("categories", {})
    sorted_cats = sorted(categories.items(), key=lambda x: x[1], reverse=True)
    
    for cat, count in sorted_cats:
        prop = (count / total * 100.0) if total > 0 else 0.0
        lines.append(f"| {cat} | {count} | {prop:.2f}% |")
        
    return "\n".join(lines)

def metrics_to_csv(metrics: Dict[str, Any]) -> str:
    """
    Outputs classification metrics in CSV format.
    """
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Metric", "Value"])
    for key in ["accuracy", "precision", "recall", "f1", "fpr", "fnr"]:
        if key in metrics:
            writer.writerow([key.upper(), f"{metrics[key]:.6f}"])
    return output.getvalue()

def ablation_to_csv(ablation_study: AblationStudyResult) -> str:
    """
    Outputs ablation variants summary in CSV format.
    """
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["VariantName", "RecordCount", "Accuracy", "F1", "MeanLatencyMs"])
    for var in ablation_study.variants:
        writer.writerow([
            var.variant_name,
            var.record_count,
            f"{var.metrics.get('accuracy', 0.0):.6f}",
            f"{var.metrics.get('f1', 0.0):.6f}",
            f"{var.latency.get('mean', 0.0):.2f}"
        ])
    return output.getvalue()

def metrics_to_latex_table(
    metrics: Dict[str, Any],
    confidence_intervals: Optional[Dict[str, Tuple[float, float, float]]] = None,
    label: str = "tab:metrics",
    caption: str = "Classification Performance Summary"
) -> str:
    """
    Generates a LaTeX table representation of classification metrics suitable for academic papers.
    """
    lines = [
        "\\begin{table}[h]",
        "\\centering",
        f"\\caption{{{caption}}}",
        f"\\label{{{label}}}",
        "\\begin{tabular}{lcc}" if confidence_intervals else "\\begin{tabular}{lc}",
        "\\hline",
        "Metric & Value (Point Estimate) & 95\\% Confidence Interval \\\\" if confidence_intervals else "Metric & Value \\\\",
        "\\hline",
    ]
    
    for key in ["accuracy", "precision", "recall", "f1", "fpr", "fnr"]:
        if key in metrics:
            val = metrics[key]
            metric_label = key.upper()
            if confidence_intervals and key in confidence_intervals:
                lower, _, upper = confidence_intervals[key]
                lines.append(f"{metric_label} & {val:.4f} & [{lower:.4f}, {upper:.4f}] \\\\")
            else:
                lines.append(f"{metric_label} & {val:.4f} \\\\")
                
    lines.extend([
        "\\hline",
        "\\end{tabular}",
        "\\end{table}"
    ])
    return "\n".join(lines)
