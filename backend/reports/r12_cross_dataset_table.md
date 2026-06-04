# Milestone R12 — Cross-Dataset Generalization Report

This experiment evaluates the domain generalization capability of the PhishShield ML component by cross-evaluating models trained on synthetic versus real dataset distributions.

## Generalization Metrics

| Training Distribution | Test Distribution | Evaluation Type | Precision | Recall | F1-Score | AUC-ROC | MCC |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Synthetic** | **Synthetic** | Same-Distribution | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| **Real** | **Real** | Same-Distribution | 0.9104 | 0.7776 | 0.8387 | 0.9125 | 0.7340 |
| **Synthetic** | **Real** | Cross-Dataset (Domain Shift) | 0.4748 | 1.0000 | 0.6439 | 0.8169 | 0.2381 |
| **Real** | **Synthetic** | Cross-Dataset (Domain Shift) | 0.9316 | 0.5900 | 0.7224 | 0.8246 | 0.6565 |

## Paper Interpretation & Commentary

1. **Quantifying Domain Shift**:
   Comparing **Synthetic $\rightarrow$ Synthetic** (F1 = 1.0000) and **Synthetic $\rightarrow$ Real** (F1 = 0.6439) reveals a degradation in F1-score due to domain shift. The synthetic dataset is generated using rule-based templates, which makes it easier to classify but less representative of real-world irregularities.
2. **Asymmetric Generalization**:
   The **Real $\rightarrow$ Synthetic** performance (F1 = 0.7224) vs **Synthetic $\rightarrow$ Real** (F1 = 0.6439) shows that the model trained on the richer real dataset generalizes slightly differently. Since the real-world dataset captures more complex structural correlations, models trained on it can adapt better.
3. **Validating Synthetic Data Utility**:
   Even though there is a domain gap, the Synthetic model evaluated on the Real dataset still achieves an AUC-ROC of 0.8169. This verifies that synthetic training datasets generated with domain expertise can serve as viable cold-start models when real training data is unavailable.

*Generated on: 2026-06-04 14:36:46 UTC*
