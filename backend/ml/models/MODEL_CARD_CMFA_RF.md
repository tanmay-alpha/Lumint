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

# Lumint-CMFA-UPI-RF-Detector

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
