"""
Ablation Summary Table Generator.
Compiles all ablation and SHAP results into formatted Markdown tables for the research paper.
"""

import json
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


def generate_ablation_tables() -> None:
    """Reads all JSON reports and generates the combined r11_ablation_tables.md document."""
    reports_dir = BACKEND_ROOT / "reports"

    # 1. Load module ablation
    with open(reports_dir / "r11_module_ablation.json", "r", encoding="utf-8") as f:
        mod_data = json.load(f)

    # 2. Load feature ablation
    with open(reports_dir / "r11_feature_ablation.json", "r", encoding="utf-8") as f:
        feat_data = json.load(f)

    # 3. Load SMOTE ablation
    with open(reports_dir / "r11_smote_ablation.json", "r", encoding="utf-8") as f:
        smote_data = json.load(f)

    # 4. Load SHAP global values
    shap_data = {}
    for mod in ["phish", "doc", "upi"]:
        with open(reports_dir / f"r11_{mod}_shap_global.json", "r", encoding="utf-8") as f:
            shap_data[mod] = json.load(f)

    # Compile the Markdown content
    md = []
    md.append("# Lumint Research Milestone R11 — Ablation Study & Feature Analysis")
    md.append("\nThis document contains the systematic ablation studies and feature importances for Lumint's sub-shields and fusion layer.")

    # Table A: Module Ablation
    md.append("\n## Table A: Module Ablation (Cross-Modal Fusion)")
    md.append("Tests the performance contribution of individual shields in the cross-modal fusion meta-learner.")
    md.append("\n| Configuration | Features / Shields | F1 Score | AUC-ROC | MCC | &Delta; F1 |")
    md.append("| :--- | :--- | :---: | :---: | :---: | :---: |")

    names_map = {
        "full": ("Full System", "DocShield + PhishShield + UPIShield"),
        "no_doc": ("No DocShield", "PhishShield + UPIShield only"),
        "no_phish": ("No PhishShield", "DocShield + UPIShield only"),
        "no_upi": ("No UPI Shield", "DocShield + PhishShield only"),
        "phish_only": ("PhishShield Only", "PhishShield single modal"),
        "doc_only": ("DocShield Only", "DocShield single modal"),
        "upi_only": ("UPI Shield Only", "UPIShield single modal"),
    }

    # Output in a clean sequence
    for key in ["full", "no_doc", "no_phish", "no_upi", "phish_only", "doc_only", "upi_only"]:
        metrics = mod_data[key]
        cfg_name, desc = names_map[key]
        delta_str = f"{metrics['delta_f1']:+.4f}" if key != "full" else "--"
        md.append(
            f"| **{cfg_name}** | {desc} | {metrics['f1']:.4f} | {metrics['auc']:.4f} | {metrics['mcc']:.4f} | {delta_str} |"
        )

    # Table B: Feature Group Ablation
    md.append("\n## Table B: Feature Group Ablation")
    md.append("Evaluates the synergy between feature groups within PhishShield and DocShield.")
    md.append("\n| Module / Shield | Feature Group | Feature Count | F1 Score | AUC-ROC | MCC | &Delta; F1 |")
    md.append("| :--- | :--- | :---: | :---: | :---: | :---: | :---: |")

    # Phish feature groups
    ph_a = feat_data["phish"]["group_a_lexical"]
    ph_b = feat_data["phish"]["group_b_tfidf"]
    ph_c = feat_data["phish"]["group_c_combined"]
    md.append(f"| **PhishShield** | Group A: Lexical Only | 25 | {ph_a['f1']:.4f} | {ph_a['auc']:.4f} | {ph_a['mcc']:.4f} | {ph_a['delta_f1']:+.4f} |")
    md.append(f"| **PhishShield** | Group B: TF-IDF Only | 2000 | {ph_b['f1']:.4f} | {ph_b['auc']:.4f} | {ph_b['mcc']:.4f} | {ph_b['delta_f1']:+.4f} |")
    md.append(f"| **PhishShield** | Group C: Combined | 2025 | {ph_c['f1']:.4f} | {ph_c['auc']:.4f} | {ph_c['mcc']:.4f} | -- |")

    # Doc feature groups
    doc_a = feat_data["doc"]["group_a_ela"]
    doc_b = feat_data["doc"]["group_b_metadata"]
    doc_c = feat_data["doc"]["group_c_combined"]
    md.append(f"| **DocShield** | Group A: ELA Only | 4 | {doc_a['f1']:.4f} | {doc_a['auc']:.4f} | {doc_a['mcc']:.4f} | {doc_a['delta_f1']:+.4f} |")
    md.append(f"| **DocShield** | Group B: Metadata Only | 9 | {doc_b['f1']:.4f} | {doc_b['auc']:.4f} | {doc_b['mcc']:.4f} | {doc_b['delta_f1']:+.4f} |")
    md.append(f"| **DocShield** | Group C: Combined | 13 | {doc_c['f1']:.4f} | {doc_c['auc']:.4f} | {doc_c['mcc']:.4f} | -- |")

    # Table C: SMOTE balancing strategy comparison
    md.append("\n## Table C: Class Balancing Strategy Comparison")
    md.append("Compares default imbalanced training to SMOTE and balanced class weights. Focuses heavily on Recall.")
    md.append("\n| Module / Shield | Strategy / Configuration | Precision | Recall (Fraud) | F1 Score | AUC-ROC |")
    md.append("| :--- | :--- | :---: | :---: | :---: | :---: |")

    strategy_map = {
        "without_smote": "Raw (Imbalanced / No SMOTE)",
        "class_weight_balanced": "Class Weight (Balanced)",
        "with_smote": "SMOTE Oversampling (Proposed)",
    }

    for mod_name in ["phish", "doc", "upi"]:
        mod_title = {"phish": "PhishShield", "doc": "DocShield", "upi": "UPIShield"}[mod_name]
        for strat in ["without_smote", "class_weight_balanced", "with_smote"]:
            metrics = smote_data[mod_name][strat]
            strat_name = strategy_map[strat]
            md.append(
                f"| **{mod_title}** | {strat_name} | {metrics['precision']:.4f} | {metrics['recall']:.4f} | {metrics['f1']:.4f} | {metrics['auc']:.4f} |"
            )

    # Table D: Top 10 SHAP feature importances per module
    md.append("\n## Table D: Global Feature Importance (Top 10 SHAP Values)")
    md.append("Presents the global mean absolute SHAP values and impact directions for the top 10 features of each shield.")

    for mod_name in ["phish", "doc", "upi"]:
        mod_title = {"phish": "PhishShield", "doc": "DocShield", "upi": "UPIShield"}[mod_name]
        md.append(f"\n### {mod_title} Top Features")
        md.append("| Rank | Feature Name | Mean Absolute SHAP | Direction of Impact | Interpretation / Paper Context |")
        md.append("| :---: | :--- | :---: | :---: | :--- |")

        for feat in shap_data[mod_name]["top_features"]:
            dir_str = "Positive (Higher -> Fraud)" if feat["direction"] == "positive" else "Negative (Higher -> Clean)"
            md.append(
                f"| {feat['rank']} | `{feat['name']}` | {feat['mean_abs_shap']:.5f} | {dir_str} | {feat['interpretation']} |"
            )

    # Write file
    report_path = reports_dir / "r11_ablation_tables.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")

    print(f"Summary markdown generated successfully -> {report_path}")


if __name__ == "__main__":
    generate_ablation_tables()
