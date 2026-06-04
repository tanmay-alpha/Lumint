# Lumint Research Dataset Documentation

This document lists and describes all real-world and synthetic datasets integrated into the Lumint ML research platform for reproducing evaluation results.

---

## 1. Real-World Datasets

### A. UCI Phishing Websites Dataset
* **Name**: Phishing Websites Dataset
* **Source**: UCI Machine Learning Repository
* **URL**: [https://archive.ics.uci.edu/dataset/327/phishing+websites](https://archive.ics.uci.edu/dataset/327/phishing+websites)
* **DOI**: [10.24432/C51W2X](https://doi.org/10.24432/C51W2X)
* **License**: Creative Commons Attribution 4.0 International (CC BY 4.0)
* **Size**: 11,055 instances (30 precomputed structural attributes + 1 class label)
* **Usage in Lumint**: We reconstruct representative URL strings based on the pre-computed attribute values to evaluate PhishShield.
* **BibTeX Citation**:
```bibtex
@misc{uci_phishing_2015,
  author       = {Mohammad, Rami and Thabtah, Fadi and McCluskey, Lee},
  title        = {{Phishing Websites}},
  year         = {2015},
  howpublished = {UCI Machine Learning Repository},
  note         = {{DOI}: 10.24432/C51W2X}
}
```

### B. PhishTank Reference Dataset
* **Name**: PhishTank Verified Phishing URLs
* **Source**: PhishTank (OpenDNS / Cisco)
* **URL**: [https://www.phishtank.com](https://www.phishtank.com)
* **License**: PhishTank Terms of Use (Academic and non-commercial research use)
* **Size**: Dynamic (constantly updated database of verified online phishing URLs)
* **Usage in Lumint**: Serves as a domain-reference and validation checkpoint for live phishing signatures.
* **BibTeX Citation**:
```bibtex
@misc{phishtank_2026,
  author       = {{PhishTank}},
  title        = {PhishTank: An Out-of-the-Box Phishing URL Verification System},
  year         = {2026},
  howpublished = {\url{https://www.phishtank.com}}
}
```

---

## 2. Synthetic Reference Datasets

To ensure deterministic testing, reproducible ablation analysis, and robust continuous integration, Lumint employs structured synthetic datasets. All generators use seed `random_state=42`.

### A. PhishShield Synthetic URL Dataset (`phishing_dataset.csv`)
* **Size**: 4,500 samples
* **Features**: 25 lexical features + 2,000 TF-IDF character n-gram dimensions
* **Structure**: Replicates lexical distributions of IP-based redirection, typosquatting, suspicious TLDs, and brand keyword abuse.

### B. DocShield Forensic Dataset (`doc_dataset.csv`)
* **Size**: 1,500 samples
* **Features**: 13 forensic features (4 Error Level Analysis metrics + 9 metadata-structural markers)
* **Structure**: Simulates tampered image regions, altered EXIF metadata fields, and compression inconsistencies.

### C. UPIShield Transaction Dataset (`upi_dataset.csv`)
* **Size**: 1,500 samples
* **Features**: 8 transaction verification features (font authenticity, OCR confidence, ELA tampering, app signatures, UTR integrity)
* **Structure**: Mimics tampered UPI receipt templates, font mismatches, and synthetic validation responses.

---

## 3. Generalization Summary

As shown in `backend/reports/r12_cross_dataset_table.md`, cross-evaluation across these synthetic and real-world datasets demonstrates a reliable baseline of security auditing, proving that features engineered in Lumint translate robustly to real-world threats.
