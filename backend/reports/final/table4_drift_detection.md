# Table 4 — Concept Drift Detection Results

Error rate: Phase 1 (t<1000): p_err=0.05 → Phase 2 (t≥1000): p_err=0.40 (abrupt) / linear ramp (gradual).

| Detector | Drift Type | True Drift t | Detection t | Delay | False Alarms (pre-drift) |
|----------|-----------|------------|------------|-------|--------------------------|
| ADWIN | Abrupt | 1000 | 1056 | 56 samples | 0 |
| Page-Hinkley | Abrupt | 1000 | 1170 | 170 samples | 0 |
| DDM | Abrupt | 1000 | 1039 | 39 samples | 0 |
| **Majority Vote** | **Abrupt** | **1000** | **1056** | **56 samples** | **0** |
| ADWIN | Gradual | 1000–2000 | 1344 | 344 samples | 0 |
| Page-Hinkley | Gradual | 1000–2000 | 1576 | 576 samples | 0 |
| DDM | Gradual | 1000–2000 | 1274 | 274 samples | 0 |
| **Majority Vote** | **Gradual** | **1000–2000** | **1344** | **344 samples** | **0** |

Majority vote consensus requires ≥2/3 detectors to flag drift simultaneously.