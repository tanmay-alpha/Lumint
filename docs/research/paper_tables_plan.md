# Lumint Academic Paper Tables Plan

This document details the layout, data structure, and code generation mappings for producing LaTeX, CSV, and Markdown tables designed for academic research publications.

## 1. Core Objectives
* **LaTeX Compatibility**: Output valid LaTeX tabular environments that require zero additional formatting for inclusion in research papers.
* **Statistical Rigour**: Display point estimates accompanied by 95% bootstrapped confidence intervals.
* **Taxonomy Consistency**: Align categorization of system errors and consensus disagreements with the taxonomies established in the research protocol.

---

## 2. Table Specifications

### A. Classification Performance Table (LaTeX / Markdown)
* **LaTeX Template**: `metrics_to_latex_table(metrics, confidence_intervals, caption)`
* **Columns**:
  * `Metric`: The binary classification metric (`ACCURACY`, `PRECISION`, `RECALL`, `F1-SCORE`).
  * `Point Estimate`: Calculated metric score on the complete dataset.
  * `95% Confidence Interval`: Bootstrapped lower and upper confidence bounds (e.g., `[0.8500, 0.9500]`).

### B. Modality Ablation Table (Markdown / CSV)
* **Columns**:
  * `Variant`: Ablation configuration name (e.g., `full_lumint`, `no_document_signal`).
  * `Records`: Sample size evaluated.
  * `Accuracy`: Calculated variant accuracy.
  * `F1-Score`: Calculated variant F1-score.
  * `Mean Latency (ms)`: Mean execution latency.
  * `Consensus Agreement`: Percentage prediction match with external consensus labels.

### C. Processing Latency Table (Markdown)
* **Columns**:
  * `Statistic`: Latency metrics (`Mean`, `Median`, `P95`, `P99`, `Min`, `Max`).
  * `Value (ms)`: Metric point estimate.
  * `95% Confidence Interval`: Bootstrapped confidence bounds (for mean latency).

### D. Consensus Agreement Table (Markdown)
* **Columns**:
  * `Metric`: Consensus alignment metrics (`Agreement Rate`, `High-Risk Agreement Rate`).
  * `Value`: Alignment rate percentages.
  * `Description`: Summary of evaluation scope.

### E. Error Taxonomy Summary Table (Markdown)
* **Columns**:
  * `Category`: Taxonomy category (e.g., `CORRELATION_MISS`, `NO_ACTIVE_SIGNALS`).
  * `Count`: Total number of error instances.
  * `Percentage`: Share of overall error occurrences.

---

## 3. Invocation CLI Mappings
Academic tables are automatically generated and appended to human-readable Markdown reports whenever the research benchmark CLI is run:
```bash
python scripts/run_research_benchmark.py --manifest research/fixtures/fusion_benchmark_manifest.json --module fusion --with-consensus
```
To run standalone ablation table reports:
```bash
python scripts/run_ablation_study.py --manifest research/fixtures/fusion_benchmark_manifest.json --module fusion
```
