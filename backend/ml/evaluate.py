"""
Lumint ML Evaluation Report Generator.

Reads all metrics.json files from ml/models/ and produces
a paper-ready model comparison table in Markdown format.
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, List

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

MODELS_DIR = Path(__file__).resolve().parent / "models"
REPORTS_DIR = BACKEND_ROOT / "reports"

MODULE_DISPLAY = {
    "phish": "PhishShield",
    "doc": "DocShield",
    "upi": "UPI Shield",
    "fusion_meta": "Cross-modal Fusion",
}


def load_all_metrics() -> Dict[str, Dict[str, Any]]:
    """Load all metrics.json files from the models directory."""
    metrics = {}
    if not MODELS_DIR.exists():
        return metrics

    for path in MODELS_DIR.glob("*_metrics.json"):
        module = path.stem.replace("_metrics", "")
        try:
            with open(path, "r", encoding="utf-8") as f:
                metrics[module] = json.load(f)
        except Exception:
            pass

    return metrics


def generate_comparison_table(metrics: Dict[str, Dict]) -> str:
    """Generate Markdown table comparing all models across modules."""
    lines = []
    lines.append("# Table R9.1: ML Model Performance Comparison (Stratified 5-Fold CV)")
    lines.append("")
    lines.append("| Module | Model | Precision | Recall | F1 | AUC | MCC | Log-Loss |")
    lines.append("|--------|-------|-----------|--------|-----|-----|-----|----------|")

    for module in ["phish", "doc", "upi"]:
        data = metrics.get(module, {})
        cv = data.get("cv_results", {})
        best = data.get("best_model", "")
        display_name = MODULE_DISPLAY.get(module, module)

        for model_name in ["LogisticRegression", "RandomForest", "GradientBoosting"]:
            m = cv.get(model_name, {})
            if not m:
                continue
            marker = " **[Best]**" if model_name == best else ""
            lines.append(
                f"| {display_name} | {model_name}{marker} | "
                f"{m.get('precision', 0):.4f} | "
                f"{m.get('recall', 0):.4f} | "
                f"**{m.get('f1', 0):.4f}** | "
                f"{m.get('auc', 0):.4f} | "
                f"{m.get('mcc', 0):.4f} | "
                f"{m.get('logloss', 0):.4f} |"
            )

    # Fusion meta-learner
    fusion = metrics.get("fusion_meta", {})
    if fusion:
        ts = fusion.get("test_set", {})
        lines.append(
            f"| {MODULE_DISPLAY.get('fusion_meta', 'Fusion')} | LogisticRegression (Meta) | "
            f"{ts.get('precision', 0):.4f} | "
            f"{ts.get('recall', 0):.4f} | "
            f"**{ts.get('f1', 0):.4f}** | "
            f"{ts.get('auc', 0):.4f} | "
            f"{ts.get('mcc', 0):.4f} | "
            f"{ts.get('logloss', 0):.4f} |"
        )

    lines.append("")
    lines.append("> **[Best]** = Best model selected for deployment (by F1 score)")
    lines.append("> All results: random_state=42, SMOTE on training folds only")

    return "\n".join(lines)


def generate_ablation_table(metrics: Dict[str, Dict]) -> str:
    """
    Generate ablation table: fusion vs each module alone.
    Shows what happens when a module is removed from fusion.
    """
    lines = []
    lines.append("")
    lines.append("# Table R9.2: Cross-Modal Ablation - Fusion vs. Individual Modules")
    lines.append("")
    lines.append("| Configuration | F1 | AUC | Precision | Recall |")
    lines.append("|---------------|-----|-----|-----------|--------|")

    # Full fusion
    fusion = metrics.get("fusion_meta", {})
    if fusion:
        ts = fusion.get("test_set", {})
        lines.append(
            f"| Lumint Fusion (All Modules) | "
            f"**{ts.get('f1', 0):.4f}** | "
            f"{ts.get('auc', 0):.4f} | "
            f"{ts.get('precision', 0):.4f} | "
            f"{ts.get('recall', 0):.4f} |"
        )

    # Individual modules
    for module in ["phish", "doc", "upi"]:
        data = metrics.get(module, {})
        best = data.get("best_model", "")
        cv = data.get("cv_results", {}).get(best, {})
        display = MODULE_DISPLAY.get(module, module)
        if cv:
            lines.append(
                f"| {display} Only | "
                f"{cv.get('f1', 0):.4f} | "
                f"{cv.get('auc', 0):.4f} | "
                f"{cv.get('precision', 0):.4f} | "
                f"{cv.get('recall', 0):.4f} |"
            )

    # Fusion coefficients
    if fusion and fusion.get("coefficients"):
        lines.append("")
        lines.append("## Fusion Meta-Learner Coefficients")
        lines.append("")
        lines.append("| Input Signal | Coefficient | Weight (%) |")
        lines.append("|-------------|-------------|------------|")

        coefs = fusion["coefficients"]
        total = sum(abs(v) for v in coefs.values()) or 1
        for name, coef in coefs.items():
            pct = abs(coef) / total * 100
            lines.append(f"| {name} | {coef:.4f} | {pct:.1f}% |")

    return "\n".join(lines)


if __name__ == "__main__":
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    metrics = load_all_metrics()

    if not metrics:
        print("No metrics.json files found. Run: python -m ml.train --module all")
        sys.exit(1)

    report = generate_comparison_table(metrics)
    report += "\n\n" + generate_ablation_table(metrics)

    report_path = REPORTS_DIR / "r9_model_comparison_table.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"Report generated: {report_path}")
    print(report)
