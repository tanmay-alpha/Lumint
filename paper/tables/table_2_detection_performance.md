# Table 2: Fraud Detection Performance Metrics

Comparative performance of individual modules and the unified multimodal fusion scoring layer.

| Module / Experiment | Type | Records | Accuracy | Precision | Recall | F1-Score | FPR | FNR |
|---|---|---|---|---|---|---|---|---|
| `url_detection_synthetic` | Synthetic | 5 | 0.6000 | 1.0000 | 0.3333 | **0.5000** | 0.0000 | 0.6667 |
| `upi_forensics_synthetic` | Synthetic | 5 | 0.6000 | 1.0000 | 0.3333 | **0.5000** | 0.0000 | 0.6667 |
| `document_forensics_synthetic` | Synthetic | 3 | 0.3333 | 0.0000 | 0.0000 | **0.0000** | 0.0000 | 1.0000 |
| `fusion_synthetic` | Synthetic | 3 | 1.0000 | 1.0000 | 1.0000 | **1.0000** | 0.0000 | 0.0000 |
| `url_real_dataset_pending` | Real-World | *Pending* | - | - | - | - | - | - |
| `upi_real_dataset_pending` | Real-World | *Pending* | - | - | - | - | - | - |