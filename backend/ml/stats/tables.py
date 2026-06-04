"""
Generates markdown tables for peer-reviewed papers from statistical reports.
"""


def generate_paper_table_with_ci(stats_report: dict) -> str:
    """
    Generates paper-ready markdown tables for a single module.
    """
    module = stats_report["module"]
    models = stats_report["models"]
    sig_tests = stats_report["significance_tests"]
    auc_comps = stats_report["auc_comparisons"]

    lines = []
    lines.append(f"## {module.upper()} Module Statistical Evaluation")
    lines.append("")

    # 1. Main Table with CIs
    lines.append("### Classifier Performance with 95% Confidence Intervals")
    lines.append("")
    lines.append(
        "| Model | F1-Score (95% CI) | Precision (95% CI) | Recall (95% CI) | AUC (DeLong 95% CI) | MCC (95% CI) |"
    )
    lines.append(
        "| :--- | :---: | :---: | :---: | :---: | :---: |"
    )

    model_names_map = {
        "LogisticRegression": "Logistic Regression (Baseline)",
        "RandomForest": "Random Forest",
        "GradientBoosting": "Gradient Boosting",
    }

    for name in ["LogisticRegression", "RandomForest", "GradientBoosting"]:
        if name not in models:
            continue
        m_data = models[name]
        cis = m_data["confidence_intervals"]
        delong = m_data["auc_delong_ci"]

        f1_str = f"{cis['f1']['point_estimate']:.4f} ({cis['f1']['ci_lower']:.4f}-{cis['f1']['ci_upper']:.4f})"
        prec_str = f"{cis['precision']['point_estimate']:.4f} ({cis['precision']['ci_lower']:.4f}-{cis['precision']['ci_upper']:.4f})"
        rec_str = f"{cis['recall']['point_estimate']:.4f} ({cis['recall']['ci_lower']:.4f}-{cis['recall']['ci_upper']:.4f})"
        auc_str = f"{delong['auc']:.4f} ({delong['ci_lower']:.4f}-{delong['ci_upper']:.4f})"
        mcc_str = f"{cis['mcc']['point_estimate']:.4f} ({cis['mcc']['ci_lower']:.4f}-{cis['mcc']['ci_upper']:.4f})"

        lines.append(
            f"| {model_names_map.get(name, name)} | {f1_str} | {prec_str} | {rec_str} | {auc_str} | {mcc_str} |"
        )

    lines.append("")

    # 2. Significance Test Results
    lines.append("### Model-to-Model Statistical Significance Comparison")
    lines.append("")
    lines.append(
        "| Comparison | McNemar Exact mid-p p-value | DeLong AUC p-value | Significant (α=0.05)? | Interpretation |"
    )
    lines.append(
        "| :--- | :---: | :---: | :---: | :--- |"
    )

    comparisons = [
        ("RF_vs_LR", "Random Forest vs Logistic Regression"),
        ("GB_vs_RF", "Gradient Boosting vs Random Forest"),
        ("GB_vs_LR", "Gradient Boosting vs Logistic Regression"),
    ]

    for key, display_name in comparisons:
        mcnemar_p = sig_tests[key]["p_value"]
        delong_p = auc_comps[key]["p_value"]
        sig = sig_tests[key]["significant"] or (delong_p < 0.05)

        sig_str = "**Yes**" if sig else "No"
        interpretation = sig_tests[key]["interpretation"]

        lines.append(
            f"| {display_name} | {mcnemar_p:.4f} | {delong_p:.4f} | {sig_str} | {interpretation} |"
        )

    lines.append("")
    lines.append(f"**Best Model Justification:** {stats_report['best_model_justification']}")
    lines.append("")
    lines.append("---")
    lines.append("")

    return "\n".join(lines)
