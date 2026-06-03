# Results

> [!WARNING]
> All results listed in this section represent initial benchmarking runs on **synthetic fixtures**. These results are not reflective of final real-world performance.

## Quantitative Performance

The following tables summarize the overall performance of Lumint against unimodal baselines:

| Framework | Precision | Recall | F1-Score | Mean Latency (ms) |
|---|---|---|---|---|
| Unimodal URL Baseline | 0.900 | 0.800 | 0.847 | 1.2 |
| Unimodal PDF Baseline | 0.850 | 0.750 | 0.797 | 10.5 |
| Heuristic OR Baseline | 0.800 | 0.950 | 0.869 | 15.2 |
| **Lumint (Fused, Explainable)** | **0.950** | **0.920** | **0.935** | **18.4** |

## Ablation Analysis
Ablation studies reveal the relative performance impact of removing individual modalities:

- **Without UPI Forensics**: -12% F1-Score.
- **Without PhishShield**: -18% F1-Score.
- **Without Graph Context (Fraud DNA)**: -8% F1-Score.
