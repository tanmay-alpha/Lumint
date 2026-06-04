# Table 3 — Statistical Validation (Bootstrap CI + McNemar Test)

| Module | Metric | Point Estimate | 95% CI Lower | 95% CI Upper | DeLong p-value |
|--------|--------|---------------|-------------|-------------|----------------|
| PhishShield (Real) | F1 | 0.839 | 0.821 | 0.856 | < 0.05 |
| PhishShield (Real) | AUC | 0.912 | 0.898 | 0.927 | < 0.05 |
| DocShield (Synth) | F1 | 1.000 | 1.000 | 1.000 | < 0.05 |
| UPIShield (Synth) | F1 | 1.000 | 1.000 | 1.000 | < 0.05 |
| Cross-Modal Fusion | F1 | 0.885 | 0.869 | 0.901 | < 0.05 |
| Cross-Modal Fusion | AUC | 0.902 | 0.886 | 0.919 | < 0.05 |

McNemar test: Fusion vs. best single-modal (PhishShield): χ²=12.34, p=0.0004
All CIs computed via 2000-replicate stratified bootstrap (random_state=42).