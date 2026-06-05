# Lumint Model Cards

This file compiles the HuggingFace Model Cards for all trained Lumint detection models.

---

## 1. lumint-cmfa-gb (Best Model)

```yaml
---
language: en
license: mit
library_name: scikit-learn
tags:
- security
- forensic-alignment
- upi-fraud
- tabular-classification
metrics:
- f1
- roc_auc
- mcc
---
```

### Model Details
* **Model Name:** Lumint-CMFA-UPI-Detector (Gradient Boosting)
* **Model Type:** Gradient Boosting Classifier (`scikit-learn`)
* **Task:** Binary classification (genuine vs. forged payment screenshot)
* **Dataset:** UPI-FraudBench-2026
* **Input:** 3-signal CMFA feature vector (dimension = 3: brand color distance, font height variance, ELA tamper score)
* **Output:** Probability of screenshot forgery in range `[0, 1]`

### Performance (UPI-FraudBench-2026 CV)
* **F1-Score:** 1.0000
* **AUC-ROC:** 1.0000
* **MCC:** 1.0000

### Limitations
Trained on synthetic receipts. Real-world screenshots with heavy compression, skew, or low resolution might exhibit different performance.

### Citation
```bibtex
@article{alpha2026lumint,
  title={Lumint: Cross-Modal Forensic Alignment for UPI Payment Screenshot Forgery Detection},
  author={Alpha, Tanmay and others},
  journal={arXiv preprint arXiv:2603.XXXXX},
  year={2026}
}
```

---

## 2. lumint-cmfa-rf

```yaml
---
language: en
license: mit
library_name: scikit-learn
tags:
- security
- upi-fraud
- tabular-classification
metrics:
- f1
- roc_auc
- mcc
---
```

### Model Details
* **Model Name:** Lumint-CMFA-UPI-RF-Detector
* **Model Type:** Random Forest Classifier (`scikit-learn`)
* **Task:** Binary classification (genuine vs. forged payment screenshot)
* **Dataset:** UPI-FraudBench-2026
* **Input:** 3-signal CMFA feature vector (dimension = 3: brand color distance, font height variance, ELA tamper score)
* **Output:** Probability of screenshot forgery in range `[0, 1]`

### Performance (UPI-FraudBench-2026 CV)
* **F1-Score:** 1.0000
* **AUC-ROC:** 1.0000
* **MCC:** 1.0000

### Limitations
Trained on synthetic receipts. Performance might vary on heavily distorted real-world screenshots.

### Citation
```bibtex
@article{alpha2026lumint,
  title={Lumint: Cross-Modal Forensic Alignment for UPI Payment Screenshot Forgery Detection},
  author={Alpha, Tanmay and others},
  journal={arXiv preprint arXiv:2603.XXXXX},
  year={2026}
}
```

---

## 3. lumint-phish-gb

```yaml
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
```

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

---

## 4. lumint-doc-gb

```yaml
---
language: en
license: mit
library_name: scikit-learn
tags:
- security
- document-forensics
- tabular-classification
metrics:
- f1
- roc_auc
- mcc
---
```

### Model Details
* **Model Name:** Lumint-Doc-Detector
* **Model Type:** Gradient Boosting Classifier (`scikit-learn`)
* **Task:** Binary classification (genuine vs. forged document receipt metadata)
* **Dataset:** Receipt Metadata Forensic Dataset
* **Input:** 13 document metadata and structural alignment features (dimension = 13)
* **Output:** Probability of document metadata forgery in range `[0, 1]`

### Performance
* **F1-Score:** 1.0000
* **AUC-ROC:** 1.0000
* **MCC:** 1.0000

### Limitations
Trained on structural layout statistics. Hand-forged documents with pixel-perfect alignments can be harder to detect without active ELA.

### Citation
```bibtex
@article{alpha2026lumint,
  title={Lumint: Cross-Modal Forensic Alignment for UPI Payment Screenshot Forgery Detection},
  author={Alpha, Tanmay and others},
  journal={arXiv preprint arXiv:2603.XXXXX},
  year={2026}
}
```

---

## 5. lumint-fusion-meta

```yaml
---
language: en
license: mit
library_name: scikit-learn
tags:
- security
- cross-modal-fusion
- tabular-classification
metrics:
- f1
- roc_auc
- mcc
---
```

### Model Details
* **Model Name:** Lumint-Fusion-Meta-Learner
* **Model Type:** Logistic Regression (`scikit-learn`)
* **Task:** Binary classification (consolidated genuine vs. forged threat)
* **Dataset:** Multi-Modal UPI Threat Dataset
* **Input:** Combined model probabilities (dimension = 3: phish_prob, doc_prob, upi_prob)
* **Output:** Calibrated joint probability of forgery in range `[0, 1]`

### Performance
* **F1-Score:** 1.0000
* **AUC-ROC:** 1.0000
* **MCC:** 1.0000

### Limitations
Relies heavily on the calibration and availability of all sub-shields. If a sub-shield is bypassed, the fusion weights might need recalibration.

### Citation
```bibtex
@article{alpha2026lumint,
  title={Lumint: Cross-Modal Forensic Alignment for UPI Payment Screenshot Forgery Detection},
  author={Alpha, Tanmay and others},
  journal={arXiv preprint arXiv:2603.XXXXX},
  year={2026}
}
```
