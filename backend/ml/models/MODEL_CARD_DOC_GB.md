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

# Lumint-Doc-Detector

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
