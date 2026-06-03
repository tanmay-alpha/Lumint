# Lumint Research Roadmap

This document outlines the roadmap for transitioning the **Lumint** platform into a research-paper-grade fraud intelligence framework.

## 1. Current Lumint Modules
* **DocShield**: Metadata extraction, error level analysis (ELA), and spoof signature checks for document forensics.
* **PhishShield**: Typosquatting detection, lookalike domain extraction, and brand impersonation heuristics.
* **UPI Shield**: Screenshot OCR parsing, layout classification, and UTR verification for mobile banking receipts.
* **Fraud DNA**: Behavioral graph mapping, linking fraud events into attributed campaigns using graph clustering.
* **Analyst Explainability**: Groq LLaMA-based automated analyst briefs for Explainable AI (XAI) and explanation routing.

---

## 2. Research Contribution Candidates
* **Unified Cross-Modal Risk Fusion**: Mathematical model for combining multi-modal indicators (URL heuristics + Document structure + UPI OCR + Graph centrality) into a single risk score.
* **Graph-based Fraud Campaign Attribution**: Unsupervised community detection to identify campaign-level coordination across multiple separate phishing vectors.
* **XAI Explanation Verification**: Quantitative framework to evaluate LLM-generated fraud explanations against structured metadata rules to ensure accuracy and prevent hallucination.

---

## 3. Current Implementation Status
* **Milestone R1 (Research Foundation)**:
  * Dataset Manifest Engine: Standardized schemas (`DatasetRecord`, `DatasetManifest`) for document, URL, UPI, and graph records.
  * Metrics Suite: Custom computation of classification performance (Accuracy, Precision, Recall, F1, FPR, FNR) and performance latency percentiles (P50, P95, P99).
  * Baseline Heuristics: Controlled, reproducible baselines.
  * Evaluation Pipeline: Experiment runner and markdown report generator.
* **Milestone R2 (Explainability & Fusion Engine)**:
  * SHAP-compatible Feature Contribution Engine (`app/core/xai.py`).
  * Cross-Modal Weighted Score Fusion & Renormalization (`app/core/fusion.py`).
  * Correlation flag engine mapping cross-modal heuristics.
  * Integration into DocShield and PhishShield API response schemas.
* **Milestone R3 (UPI Shield Forensics Hardening & Benchmark Fixtures)**:
  * Transaction hash correlation and metadata extraction.
  * Rule-based UPI Receipt classifier engine.
  * Standardized UPI benchmark dataset manifest fixtures.
* **Milestone R4 (Benchmark Experiment Runner)**:
  * Modular system adapters routing dataset records to core models.
  * Multi-dataset evaluation orchestration (`research/experiment_runner.py`).
  * Automatic markdown/JSON report writer (`research/report_writer.py`).
* **Milestone R5 (External Consensus Agreements)**:
  * Integration layer for external consensus providers (VirusTotal, Urlscan, AbuseIPDB).
  * Automated mapping from predictions to agreement/disagreement metrics.
* **Milestone R6 (Ablation, Confidence, and Error Taxonomy)**:
  * Ablation Engine (`research/ablation.py`) to systematically disable individual signals.
  * Bootstrapped confidence intervals for latencies and classification metrics (`research/statistics.py`).
  * Error taxonomy heuristics to classify prediction errors (`research/error_analysis.py`).
  * Automated LaTeX/CSV/Markdown paper table generator (`research/paper_tables.py`).

---

## 4. Pending Research Items
* **Labeled Benchmark Ingestion**: Loading and labeling standardized fraud datasets.
* **Ablation Studies**: Quantifying the contribution of individual modalities using the R2 cross-modal weights API.
* **Baseline Comparison**: Running benchmark runs against external baselines on real-world datasets.
* **Cross-Modal Fusion Modeling**: Formalizing the fusion weights using analytical models (e.g., Logistic Regression, SVM, or Random Forest) compared against the heuristic weights baseline.

