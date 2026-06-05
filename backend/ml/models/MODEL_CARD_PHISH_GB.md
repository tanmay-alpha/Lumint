---
language: en
license: mit
library_name: scikit-learn
tags:
- security
- phishing-detection
- tabular-classification
metrics:
- f1
- roc_auc
- mcc
---

# Lumint-Phish-Detector

### Model Details
* **Model Name:** Lumint-Phish-Detector
* **Model Type:** Gradient Boosting Classifier (`scikit-learn`)
* **Task:** Binary classification (phishing vs. legitimate URL)
* **Dataset:** Phishing URL Dataset (part of UPI-FraudBench-2026)
* **Input:** TF-IDF URL character n-grams (dimension = 2025)
* **Output:** Probability of phishing URL in range `[0, 1]`

### Performance
* **F1-Score:** 1.0000
* **AUC-ROC:** 1.0000
* **MCC:** 1.0000

### Limitations
Trained on known phishing domain features. Highly evasive, zero-day subdomains might require supplementary threat intelligence checks.

### Citation
```bibtex
@article{alpha2026lumint,
  title={Lumint: Cross-Modal Forensic Alignment for UPI Payment Screenshot Forgery Detection},
  author={Alpha, Tanmay and others},
  journal={arXiv preprint arXiv:2603.XXXXX},
  year={2026}
}
```
