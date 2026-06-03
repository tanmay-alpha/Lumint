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

## 3. Current Implementation Status (Milestone R1)
* **Dataset Manifest Engine**: Standardized schemas (`DatasetRecord`, `DatasetManifest`) for document, URL, UPI, and graph records.
* **Metrics Suite**: Custom computation of classification performance (Accuracy, Precision, Recall, F1, FPR, FNR) and performance latency percentiles (P50, P95, P99) without heavy dependencies.
* **Baseline Heuristics**: Controlled, reproducible baselines (`url_keyword_baseline`, `url_domain_length_baseline`, `document_metadata_baseline`, `upi_utr_format_baseline`).
* **Evaluation Pipeline**: Experiment runner and markdown report generator.

---

## 4. Pending Research Items
* **Labeled Benchmark Ingestion**: Loading and labeling standardized fraud datasets.
* **Ablation Studies**: Quantifying the contribution of individual modalities (e.g. comparing URL-only check vs URL+Graph checks).
* **Baseline Comparison**: Running benchmark runs against external baselines (e.g., standard regex parsers or basic classifiers) on real-world datasets.
* **Cross-Modal Fusion Modeling**: Formalizing the fusion weights using analytical models (e.g., Logistic Regression, SVM, or Random Forest).
