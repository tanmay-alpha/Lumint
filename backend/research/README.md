# Lumint Research & Evaluation Layer

This directory contains the non-invasive research evaluation layer for the **Lumint** fraud intelligence platform. It provides the foundation for benchmark datasets, metrics computation, baseline models, and reproducible experiment execution.

## Directory Layout
* `dataset_manifest.py`: Models, enums, and helpers for representing structured datasets in a reproducible way.
* `metrics.py`: Standard classification and performance metrics (Precision, Recall, F1, Accuracy, FPR, FNR, latency percentiles).
* `baselines.py`: Simple heuristic baselines for URL phishing, metadata spoofing, and UPI format validation.
* `experiment_runner.py`: Execution pipeline for running baselines and models against dataset manifests.
* `report_writer.py`: Markdown report generator for compiling research-paper-ready evaluations.
