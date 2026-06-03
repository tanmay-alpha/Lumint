# Table 1: Lumint Evaluation Datasets Summary

This table provides an overview of the registered benchmark evaluation datasets used for testing the Lumint framework.

| Dataset / Experiment ID | Title | Target Module | Split | Status | Notes |
|---|---|---|---|---|---|
| `url_detection_synthetic` | URL Phishing Detection Synthetic Benchmark | `PhishShield` | BENCHMARK | `synthetic_done` | Synthetic testing for URL phishing detection heuristics. |
| `upi_forensics_synthetic` | UPI Screenshot Forensics Synthetic Benchmark | `UPIShield` | BENCHMARK | `synthetic_done` | Synthetic testing for ELA, font consistency, and UTR validation. |
| `document_forensics_synthetic` | Document Forensics Synthetic Benchmark | `DocShield` | BENCHMARK | `synthetic_done` | Synthetic testing for document structure analysis. |
| `fusion_synthetic` | Cross-Modal Risk Fusion Synthetic Benchmark | `Fusion` | BENCHMARK | `synthetic_done` | Evaluating dynamic weighting and correlation scaling. |
| `consensus_agreement_synthetic` | External Consensus Agreement Synthetic Benchmark | `Agreement` | BENCHMARK | `synthetic_done` | Agreement scoring and Kappa calculation against external stubs. |
| `ablation_synthetic` | Multimodal Ablation Study Synthetic Benchmark | `Ablation` | BENCHMARK | `synthetic_done` | Measuring performance degradation when removing individual modalities. |
| `url_real_dataset_pending` | URL Phishing Detection Real-World Benchmark | `PhishShield` | BENCHMARK | `real_data_pending` | Evaluation on real-world phishing feeds. |
| `upi_real_dataset_pending` | UPI Screenshot Forensics Real-World Benchmark | `UPIShield` | BENCHMARK | `real_data_pending` | Evaluation on crowd-sourced forged screenshots. |
| `external_consensus_pending` | External Consensus Real-World Benchmark | `Agreement` | BENCHMARK | `real_data_pending` | Fleiss Kappa and bootstrap CI evaluation on real consensus data. |