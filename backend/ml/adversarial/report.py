"""
Lumint Adversarial Report Generator
Evaluates all shields (phish, doc, upi) under FGSM and HopSkipJump attacks,
applies adversarial training defense, and saves results/tables.
"""

import os
import json
from pathlib import Path
from datetime import datetime, timezone

from ml.adversarial.evaluate import evaluate_module_robustness
from ml.adversarial.defense import adversarial_training

BACKEND_ROOT = Path(__file__).resolve().parents[2]
REPORTS_DIR = BACKEND_ROOT / "reports"

def generate_adversarial_report() -> None:
    """
    Runs full attack suite on all 3 modules.
    Runs adversarial training defense.
    Generates:
      backend/reports/r16_adversarial_robustness.json
      backend/reports/r16_adversarial_table.md
    """
    print("Starting full adversarial robustness audit...")
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    modules = ["phish", "doc", "upi"]
    results = {}
    
    for module in modules:
        print(f"\n--- Auditing {module.upper()} Shield ---")
        
        # 1. Evaluate baseline robustness (attacks)
        # Using n_samples_fgsm=500 and n_samples_hsj=100 for evaluation
        print("Evaluating baseline robustness...")
        eval_res = evaluate_module_robustness(
            module,
            n_samples_fgsm=500,
            n_samples_hsj=100
        )
        
        # 2. Train defense (hardening)
        print("Training adversarial hardening defense...")
        defense_res = adversarial_training(
            module,
            epsilon=0.05,
            augmentation_ratio=0.3,
            n_samples_eval=500
        )
        
        # Combine
        results[module] = {
            "module": module,
            "baseline_f1": eval_res["baseline_f1"],
            "fgsm_asr_epsilon_0.05": eval_res["fgsm_results"]["epsilon_0.05"]["asr"],
            "hopskipjump_asr": eval_res["hopskipjump_asr"],
            "after_defense_asr": defense_res["hardened_asr_epsilon_0.05"],
            "f1_cost": defense_res["f1_cost"],
            "evaluation": eval_res,
            "defense": defense_res
        }
        
    # Generate JSON
    report_json = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "results": results
    }
    
    json_path = REPORTS_DIR / "r16_adversarial_robustness.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report_json, f, indent=2)
    print(f"\nSaved adversarial robustness JSON report to {json_path}")
    
    # Generate Markdown Table
    md = []
    md.append("# R16 Adversarial Robustness and Defense Study")
    md.append("")
    md.append("This report presents empirical robustness metrics for Lumint protection shields under evasion attacks.")
    md.append("It evaluates Fast Gradient Sign Method (FGSM) and HopSkipJump (HSJ) black-box attacks, alongside")
    md.append("adversarial training hardening results.")
    md.append("")
    md.append("| Module | Baseline F1 | FGSM ASR (ε=0.05) | HopSkipJump ASR | After Defense ASR | F1 Cost |")
    md.append("|---|---|---|---|---|---|")
    
    name_map = {
        "phish": "PhishShield",
        "doc": "DocShield",
        "upi": "UPIShield"
    }
    
    for module in modules:
        res = results[module]
        name = name_map[module]
        baseline_f1 = f"{res['baseline_f1']:.4f}"
        fgsm_asr = f"{res['fgsm_asr_epsilon_0.05']:.4f}"
        hsj_asr = f"{res['hopskipjump_asr']:.4f}"
        defense_asr = f"{res['after_defense_asr']:.4f}"
        f1_cost = f"{res['f1_cost']:.4f}"
        
        md.append(f"| {name} | {baseline_f1} | {fgsm_asr} | {hsj_asr} | {defense_asr} | {f1_cost} |")
        
    md.append("")
    
    md_path = REPORTS_DIR / "r16_adversarial_table.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    print(f"Saved adversarial table to {md_path}")

if __name__ == "__main__":
    generate_adversarial_report()
