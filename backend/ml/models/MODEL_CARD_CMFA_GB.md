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

# Lumint-CMFA-UPI-Detector (Gradient Boosting)

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
