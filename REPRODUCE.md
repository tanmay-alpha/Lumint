# Lumint Paper Results Reproducibility Guide

This guide provides instructions to reproduce the complete set of evaluations, baseline benchmarks, ablation studies, drift monitoring, and adversarial robustness experiments presented in the Lumint paper.

## 1. System Requirements

* **Operating System:** Windows 10/11, macOS (13+), or Linux (Ubuntu 20.04+)
* **Python Version:** Python 3.11
* **NodeJS Version:** Node v18+ (for frontend package compilation)
* **Hardware Requirements:**
  * CPU: 4+ cores, 2.4 GHz minimum
  * Memory: 8 GB RAM minimum (16 GB recommended)
  * Disk: 2 GB available space
  * GPU: Optional (Visual features fallback to spatial pixel grid and ELA analysis automatically if PyTorch/CUDA is not present)

## 2. Environment Setup

It is highly recommended to run this inside a virtual environment to prevent dependency conflicts:

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install required backend dependencies
pip install -r backend/requirements.txt

# Install frontend dependencies
cd frontend
npm install
cd ..
```

---

## 3. Running the Reproduction Suite

You can execute the entire evaluation pipeline end-to-end via the provided bash script:

```bash
chmod +x reproduce.sh
./reproduce.sh
```

For Windows environments without Git Bash, you can execute each step manually in your terminal:

```cmd
:: Step 2: Generate dataset
python dataset/generate_dataset.py

:: Step 3: Train models
python backend/ml/train.py --module all

:: Step 4: Run evaluation
python backend/ml/evaluate.py

:: Step 5: Feature and module ablation
python backend/ml/ablation/summary.py

:: Step 6: Drift simulation
python backend/ml/drift/report.py

:: Step 7: Adversarial robustness evaluation
python backend/ml/adversarial/report.py

:: Step 8: Competitive benchmark comparison
python backend/ml/baselines/compare_all.py

:: Step 9: Generate figures
python backend/ml/figures/generate_figures.py

:: Step 10: Run test suite
pytest --tb=short -q

:: Step 11: Final paper table outputs
python backend/ml/final_eval.py
```

---

## 4. Expected Outputs and Metric Ranges

Upon complete execution, all artifacts, figures, and reports will be populated under the `backend/reports/final/` and `backend/ml/models/` directories.

Below are the reference ranges for key metrics under clean and perturbed evaluation setups:

### A. Clean Classification Performance (5-Fold CV)
* **Expected Metrics:**
  * Precision: `1.0000` (within `±0.005`)
  * Recall: `1.0000` (within `±0.005`)
  * F1-Score: `1.0000` (within `±0.005`)
  * AUC-ROC: `1.0000`
  * MCC: `1.0000`

### B. Competitive Benchmark vs. FakePay Baseline
* **Expected Clean F1:**
  * Lumint UPIShield: `1.0000`
  * FakePay Baseline: `1.0000`
* **Under Perturbations / Failure Modes:**
  * **OCR Failure:** FakePay `~0.83` | UPIShield `~0.71` (Fused Lumint recovers via multi-modal alignment)
  * **OOD Layout Shift:** FakePay `~0.95` | UPIShield `1.00` (Lumint remains invariant to layout alterations)
  * **Sophisticated Evasion:** FakePay `0.00` | UPIShield `~0.96` (Semantic UTR verification captures pixel-perfect spoofing)

### C. Drift Detection Statistics
* **Drift Sensitivity:** P-value threshold = `0.05`.
* **Expected Output:** Drift reports (`drift_report.json`) confirming successful statistical shift flag within 10-15 out-of-distribution batches.

---

## 5. Troubleshooting & Support

1. **ModuleNotFoundError:** Ensure your working directory is at the repository root and your virtual environment is active. The backend code references import structures relative to `backend`.
2. **PyTorch Import Errors:** If `torch` or `torchvision` cannot be loaded, the FakePay baseline automatically falls back to a deterministic 512-dimensional spatial color and edge density descriptor to guarantee reproducibility without specialized hardware.
3. **Reproducibility Seed:** The global random seed is set to `42` (`random_state=42` / `SEED = 42`) across all classifier initializations, split generation, and synthetic receipt perturbations to ensure byte-level matching of outputs.
