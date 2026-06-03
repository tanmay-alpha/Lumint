# Evaluation

## Experimental Setup

### Dataset Configurations
We evaluate Lumint using both synthetic and real-world benchmark manifests.
- **Synthetic Fixtures**: A seed dataset containing mock records for all four categories (URLs, PDFs, Screenshots, Graph configurations). Used for deterministic pipeline validation.
- **Real-World Datasets**: Sourced from actual phishing links, merchant reports, and crowd-sourced fraud screenshot repositories (pending deployment).

### Baselines
We compare Lumint's fused results against the following baselines:
1. **Unimodal URL Classifier**: Evaluates only URL signals (PhishShield).
2. **Unimodal PDF Forensic Checker**: Evaluates only document structures (DocShield).
3. **Unimodal Screenshot Analyzer**: Evaluates only image structures (UPI Shield).
4. **Heuristic OR Selector**: Triggers high-risk if any unimodal component detects high-risk.

## Evaluation Protocol
We measure:
- Classification accuracy, Precision, Recall, and F1-score.
- Latency (ms) per component.
- Bootstrap Confidence Intervals (95% CI) over 1000 resamples.
- Inter-rater agreement statistics against public consensus providers.
- Ablation impact.
