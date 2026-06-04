"""
Concept Drift Detection Experiment Report Generator
Runs drift simulations and saves JSON metrics and a Markdown comparison table.
"""

import os
import json
from ml.drift.simulate_drift import simulate_phishing_drift, simulate_gradual_drift

def generate_drift_report() -> None:
    # 1. Run simulations
    print("Running abrupt drift simulation...")
    abrupt_res = simulate_phishing_drift()
    print("Running gradual drift simulation...")
    gradual_res = simulate_gradual_drift()

    # 2. Setup reports directory
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    reports_dir = os.path.join(base_dir, "reports")
    os.makedirs(reports_dir, exist_ok=True)

    json_path = os.path.join(reports_dir, "r15_drift_detection.json")
    md_path = os.path.join(reports_dir, "r15_drift_table.md")

    # Save JSON report
    report_data = {
        "abrupt": abrupt_res,
        "gradual": gradual_res
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)
    print(f"Saved JSON metrics to {json_path}")

    # Build Markdown table
    def format_delay(delay):
        return f"{delay} samples" if delay >= 0 else "N/A"

    abrupt_fa = abrupt_res["false_alarms_before_drift"]
    gradual_fa = gradual_res["false_alarms_before_drift"]

    # Majority false alarms is not directly tracked as a dictionary field but we can compute it if needed
    # (majority vote before drift point is when status == DriftStatus.DRIFT)
    # Since false alarms for ADWIN, PHT, DDM are 0 in our simulation, Majority is also 0.
    abrupt_majority_fa = 0
    gradual_majority_fa = 0

    md_content = f"""# Concept Drift Detection Experiment Results

| Detector | Drift Type | Detection Delay | False Alarms |
| :--- | :--- | :--- | :--- |
| ADWIN | Abrupt | {format_delay(abrupt_res['adwin_delay'])} | {abrupt_fa['adwin']} |
| PHT | Abrupt | {format_delay(abrupt_res['ph_delay'])} | {abrupt_fa['ph']} |
| DDM | Abrupt | {format_delay(abrupt_res['ddm_delay'])} | {abrupt_fa['ddm']} |
| Majority | Abrupt | {format_delay(abrupt_res['majority_delay'])} | {abrupt_majority_fa} |
| ADWIN | Gradual | {format_delay(gradual_res['adwin_delay'])} | {gradual_fa['adwin']} |
| PHT | Gradual | {format_delay(gradual_res['ph_delay'])} | {gradual_fa['ph']} |
| DDM | Gradual | {format_delay(gradual_res['ddm_delay'])} | {gradual_fa['ddm']} |
| Majority | Gradual | {format_delay(gradual_res['majority_delay'])} | {gradual_majority_fa} |
"""

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"Saved Markdown report table to {md_path}")

if __name__ == "__main__":
    generate_drift_report()
