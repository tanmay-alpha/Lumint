# Paper Evaluation Results Tables Index

This directory houses the LaTeX/Markdown/CSV tables that compile the final results of the Lumint framework evaluation.

## Table Catalog

| Filename | Content Summary | Status |
|---|---|---|
| [table_1_dataset_summary.md](table_1_dataset_summary.md) | Comprehensive catalog of registered benchmarks. | ✅ Ready |
| [table_2_detection_performance.md](table_2_detection_performance.md) | Point estimates of Accuracy, Recall, F1, FPR, FNR. | ✅ Ready |
| [table_3_latency_profile.md](table_3_latency_profile.md) | Hardware/latency profile and percentile stats (Mean/Median/P95). | ✅ Ready |
| [table_4_ablation.md](table_4_ablation.md) | Modular degradation values under ablation testing. | ✅ Ready |
| [table_5_consensus_agreement.md](table_5_consensus_agreement.md) | Agreement rates and Kappa statistics against consensus. | ✅ Ready |

## Reproduction Protocol

To execute the full synthetic paper experiment pipeline and refresh all bundle tables, execute:
```bash
cd backend
python scripts/run_paper_experiments.py --synthetic-only
python scripts/build_paper_bundle.py --source-dir research_outputs/paper_run --paper-dir ../paper
```

This processes synthetic fixtures deterministically, updates metrics, compiles ablated permutations, and updates all paper artifacts.