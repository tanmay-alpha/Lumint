# Lumint Evaluation Protocol

This protocol defines the formal methodology for evaluating and benchmarking individual fraud detection modules and the unified Lumint risk scoring system.

## 1. Module-Specific Evaluation Procedures

### A. PhishShield (URL Phishing Detection)
* **Goal**: Measure the accuracy of flagging lookalike domains, brand-spoofing subdomains, and malicious paths.
* **Input**: List of URLs (phishing and benign).
* **Baseline Comparison**: `url_keyword_baseline` & `url_domain_length_baseline`.
* **Ground Truth Validation**: Cross-reference against PhishTank and Brave Search API labels.

### B. DocShield (Document Forensics)
* **Goal**: Detect image tampering, photoshop signatures, metadata anomalies, and spoofed extensions.
* **Input**: Labeled PDFs and images (untampered vs edited).
* **Baseline Comparison**: `document_metadata_baseline` (checking for tool-specific signatures in metadata).
* **Ground Truth Validation**: Artificially tampered document set with recorded ELA edits.

### C. UPI Shield (UPI Screenshot & Receipt Analysis)
* **Goal**: Identify layout counterfeits, invalid UTR formats, and transaction mismatches.
* **Input**: Simulated or anonymized UPI payment receipts (GPay, PhonePe, Paytm).
* **Baseline Comparison**: `upi_utr_format_baseline` (checking UTR structure and format).
* **Ground Truth Validation**: Bank statement verification.

### D. Fraud DNA (Graph Clustering & Campaign Attributions)
* **Goal**: Verify community detection performance in linking isolated fraud events to single threat campaigns.
* **Metrics**: Graph centrality, modularity, and clustering coefficients.
* **Ground Truth Validation**: Manually mapped campaign threat clusters.

---

## 2. Evaluation Metrics & Latency Reporting
* **Classification Accuracy**: Report Accuracy, Precision, Recall, and F1-Score.
* **FPR and FNR**: Explicitly report False Positive Rate (FPR) and False Negative Rate (FNR) to assess usability in low-tolerance financial environments.
* **Latency Profile**: Profile API response and processing latency using Mean, Median, P95, and P99 percentiles in milliseconds.

---

## 3. Reproducibility Guidelines
* All benchmark datasets must be registered via the `DatasetManifest` schema.
* Experiments must be run using the `experiment_runner` to produce deterministic results.
* Results must be exported as JSON (`ExperimentResult`) and human-readable Markdown (`write_markdown_report`) to support peer review.
