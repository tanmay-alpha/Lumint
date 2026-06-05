#!/bin/bash
# Lumint Complete Reproducibility Script
# Reproduces all paper results from scratch
# random_state=42 everywhere
# Run time: ~15 minutes on standard laptop

set -e

echo "=== Lumint Paper Reproduction ==="
echo "Step 1: Install dependencies"
pip install -r backend/requirements.txt
cd frontend && npm install && cd ..

echo "Step 2: Generate UPI-FraudBench dataset"
python dataset/generate_dataset.py

echo "Step 3: Train all models (R9)"
python backend/ml/train.py --module all

echo "Step 4: Statistical validation (R10)"
python backend/ml/evaluate.py

echo "Step 5: Ablation study (R11)"
python backend/ml/ablation/summary.py

echo "Step 6: Drift detection experiment (R15)"
python backend/ml/drift/report.py

echo "Step 7: Adversarial robustness (R16)"
python backend/ml/adversarial/report.py

echo "Step 8: Competitive benchmark"
python backend/ml/baselines/compare_all.py

echo "Step 9: Generate paper figures"
python backend/ml/figures/generate_figures.py

echo "Step 10: Run all tests"
pytest --tb=short -q

echo "Step 11: Final paper table generation"
python backend/ml/final_eval.py

echo "=== All results in backend/reports/final/ ==="
