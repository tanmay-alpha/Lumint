# Lumint Dataset Plan

This document outlines the acquisition, formatting, privacy preservation, and labeling procedures for datasets used to benchmark Lumint's components.

## 1. Planned Benchmark Datasets

### A. PhishShield Benchmark Dataset
* **Source**:
  * Active phishing feeds from PhishTank (live CSV dump).
  * Benign Alexa Top 10k domains to evaluate false positives.
* **Size**: 1,000 active phishing URLs + 1,000 benign URLs.
* **Labels**: `CLEAN` (benign), `HIGH` (verified phishing).

### B. DocShield Forensics Dataset
* **Source**:
  * Mendeley Document Tampering Dataset.
  * Custom generated PDFs and JPEG scans created using Adobe Acrobat Pro, Photoshop, and GIMP to represent typical invoice forgery styles.
* **Size**: 100 authentic invoices + 100 forged/edited invoices.
* **Labels**: `CLEAN` (no edit signature or metadata mismatch), `HIGH` (contains editing signatures or ELA anomalies).

### C. UPI Receipt Verification Dataset
* **Source**:
  * Synthesized UPI receipts matching the visual layouts of Google Pay, PhonePe, and Paytm.
  * Real payment screenshots anonymized to prevent PII leakage.
* **Size**: 150 authentic transaction screens + 50 counterfeit receipts.
* **Labels**: `CLEAN` (correct format, valid UTR), `SUSPICIOUS` (unusual layout / fonts), `HIGH` (duplicate/non-numeric UTR).

---

## 2. Privacy & Anonymization Standards
All datasets containing personal data (such as bank receipts, scans, or usernames) must undergo strict anonymization before registration in the manifest:
1. **PII Masking**: Sender/receiver name, phone number, and account number fields must be blurred or overwritten with static dummy values (e.g. `XXXXXX1234`).
2. **IP/Domain Scrubbing**: Live user IP addresses or sensitive intranet domains must not be committed to the code repository.
3. **No Database Commits**: No raw database files containing active user fraud records or upload files will be committed to git.

---

## 3. Standard Labeling Schema
* **`CLEAN`**: Safe, authenticated, correct structure, zero suspicious indicators.
* **`SUSPICIOUS`**: Missing non-critical metadata, borderline domain length, or slightly mismatched layout.
* **`HIGH`**: Editing signatures found, typosquatted brand match, invalid UTR format, or confirmed phishing feed matches.
