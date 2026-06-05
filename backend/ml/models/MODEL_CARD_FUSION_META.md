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

# Lumint-Fusion-Meta-Learner

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
