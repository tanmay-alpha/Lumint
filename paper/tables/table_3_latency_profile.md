# Table 3: System Latency Profile (Milliseconds)

Latency profile benchmark for individual detection modules and the fusion layer.

| Module / Experiment | Mean (ms) | Median (ms) | P95 (ms) | P99 (ms) | Min (ms) | Max (ms) |
|---|---|---|---|---|---|---|
| `url_detection_synthetic` | 0.28 | 0.22 | 0.54 | 0.58 | 0.10 | 0.59 |
| `upi_forensics_synthetic` | 5.56 | 3.00 | 13.44 | 15.51 | 2.84 | 16.03 |
| `document_forensics_synthetic` | 17.60 | 15.51 | 33.71 | 35.33 | 1.54 | 35.73 |
| `fusion_synthetic` | 0.02 | 0.02 | 0.03 | 0.03 | 0.01 | 0.03 |