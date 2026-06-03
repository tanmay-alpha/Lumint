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

---

## 4. Ground Truth Agreement & Consensus Layer (R5)
To ensure research-grade evaluation rigour, predictions are compared with an **External Ground-Truth Consensus Layer** composed of multi-engine intelligence (e.g. VirusTotal, Urlscan.io, AbuseIPDB):
* **Consensus Resolution**: External API labels are normalized (`CLEAN`, `SUSPICIOUS`, `HIGH`) to align with Lumint metrics, resolving discrepancies using majority voting or provider priority.
* **Agreement Performance Metrics**:
  * *Agreement Rate*: Match rate between predicted label and consensus label.
  * *High-Risk Agreement Rate*: Agreement rate focused purely on critical positive cases (`HIGH`/`SUSPICIOUS`).
  * *Agreement Confusion Matrix*: Binary metrics mapping predictions against normalized consensus.
* **Disagreement Analysis**: All records with label mismatches are exported into a structured disagreement report to isolate false-positive edge-cases or identify superior engine coverage.

---

## 5. Ablation Studies, Statistical Confidence, and Error Taxonomy (R6)

To quantify evaluation certainty and analyze system robustness, the research protocol integrates statistical confidence estimation and error categorization:

### A. Systematic Ablation Studies
* **Modality Ablation**: Disable individual inputs (e.g., document, url, upi) to measure their direct effect on classification performance.
* **Weight Override**: Adjust weights in the weighted fusion algorithm to evaluate the sensitivity of the overall fusion model.
* **Selection Criteria**: Select the best-performing variant based on highest F1-score with latency as a tie-breaker.

### B. Statistical Bootstrap Confidence Intervals
* **Methodology**: Apply non-parametric bootstrapping (default `n=1000` resamples) to predictions and latencies.
* **Reporting**: Produce 95% confidence intervals (lower bound, point estimate, upper bound) for accuracy, precision, recall, F1, and mean processing latency.

### C. Error Taxonomy Analysis
All prediction errors (false negatives and false positives) are heuristically categorized to identify architectural limitations:
* `NO_ACTIVE_SIGNALS`: No indicators matched the sample.
* `CORRELATION_MISS`: Multi-modal indicators were present, but final score calculation did not cross the threshold.
* `FORENSICS_FAILURE`: Signatures failed to trigger, or false positive triggered on clean input.
* `OVER_SENSITIVE`: Borderline scores incorrectly crossed the verdict threshold.
* `API_ERROR`: Underlying adapter or consensus API call failed.
* `OTHER`: Miscellaneous edge cases.

