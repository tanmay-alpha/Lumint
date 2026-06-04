# R10: Model Uncertainty & Significance Reports


## PHISH Module Statistical Evaluation

### Classifier Performance with 95% Confidence Intervals

| Model | F1-Score (95% CI) | Precision (95% CI) | Recall (95% CI) | AUC (DeLong 95% CI) | MCC (95% CI) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Logistic Regression (Baseline) | 1.0000 (1.0000-1.0000) | 1.0000 (1.0000-1.0000) | 1.0000 (1.0000-1.0000) | 1.0000 (1.0000-1.0000) | 1.0000 (1.0000-1.0000) |
| Random Forest | 1.0000 (1.0000-1.0000) | 1.0000 (1.0000-1.0000) | 1.0000 (1.0000-1.0000) | 1.0000 (1.0000-1.0000) | 1.0000 (1.0000-1.0000) |
| Gradient Boosting | 1.0000 (1.0000-1.0000) | 1.0000 (1.0000-1.0000) | 1.0000 (1.0000-1.0000) | 1.0000 (1.0000-1.0000) | 1.0000 (1.0000-1.0000) |

### Model-to-Model Statistical Significance Comparison

| Comparison | McNemar Exact mid-p p-value | DeLong AUC p-value | Significant (α=0.05)? | Interpretation |
| :--- | :---: | :---: | :---: | :--- |
| Random Forest vs Logistic Regression | 1.0000 | 1.0000 | No | Model A is not significantly different from Model B |
| Gradient Boosting vs Random Forest | 1.0000 | 1.0000 | No | Model A is not significantly different from Model B |
| Gradient Boosting vs Logistic Regression | 1.0000 | 1.0000 | No | Model A is not significantly different from Model B |

**Best Model Justification:** LogisticRegression was selected as the best model because it achieved the highest mean F1-score during stratified 5-fold cross-validation. Significance tests (McNemar and DeLong AUC) were conducted to verify if the performance improvements are statistically significant.

---


## DOC Module Statistical Evaluation

### Classifier Performance with 95% Confidence Intervals

| Model | F1-Score (95% CI) | Precision (95% CI) | Recall (95% CI) | AUC (DeLong 95% CI) | MCC (95% CI) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Logistic Regression (Baseline) | 1.0000 (1.0000-1.0000) | 1.0000 (1.0000-1.0000) | 1.0000 (1.0000-1.0000) | 1.0000 (1.0000-1.0000) | 1.0000 (1.0000-1.0000) |
| Random Forest | 1.0000 (1.0000-1.0000) | 1.0000 (1.0000-1.0000) | 1.0000 (1.0000-1.0000) | 1.0000 (1.0000-1.0000) | 1.0000 (1.0000-1.0000) |
| Gradient Boosting | 1.0000 (1.0000-1.0000) | 1.0000 (1.0000-1.0000) | 1.0000 (1.0000-1.0000) | 1.0000 (1.0000-1.0000) | 1.0000 (1.0000-1.0000) |

### Model-to-Model Statistical Significance Comparison

| Comparison | McNemar Exact mid-p p-value | DeLong AUC p-value | Significant (α=0.05)? | Interpretation |
| :--- | :---: | :---: | :---: | :--- |
| Random Forest vs Logistic Regression | 1.0000 | 1.0000 | No | Model A is not significantly different from Model B |
| Gradient Boosting vs Random Forest | 1.0000 | 1.0000 | No | Model A is not significantly different from Model B |
| Gradient Boosting vs Logistic Regression | 1.0000 | 1.0000 | No | Model A is not significantly different from Model B |

**Best Model Justification:** LogisticRegression was selected as the best model because it achieved the highest mean F1-score during stratified 5-fold cross-validation. Significance tests (McNemar and DeLong AUC) were conducted to verify if the performance improvements are statistically significant.

---


## UPI Module Statistical Evaluation

### Classifier Performance with 95% Confidence Intervals

| Model | F1-Score (95% CI) | Precision (95% CI) | Recall (95% CI) | AUC (DeLong 95% CI) | MCC (95% CI) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Logistic Regression (Baseline) | 1.0000 (1.0000-1.0000) | 1.0000 (1.0000-1.0000) | 1.0000 (1.0000-1.0000) | 1.0000 (1.0000-1.0000) | 1.0000 (1.0000-1.0000) |
| Random Forest | 1.0000 (1.0000-1.0000) | 1.0000 (1.0000-1.0000) | 1.0000 (1.0000-1.0000) | 1.0000 (1.0000-1.0000) | 1.0000 (1.0000-1.0000) |
| Gradient Boosting | 1.0000 (1.0000-1.0000) | 1.0000 (1.0000-1.0000) | 1.0000 (1.0000-1.0000) | 1.0000 (1.0000-1.0000) | 1.0000 (1.0000-1.0000) |

### Model-to-Model Statistical Significance Comparison

| Comparison | McNemar Exact mid-p p-value | DeLong AUC p-value | Significant (α=0.05)? | Interpretation |
| :--- | :---: | :---: | :---: | :--- |
| Random Forest vs Logistic Regression | 1.0000 | 1.0000 | No | Model A is not significantly different from Model B |
| Gradient Boosting vs Random Forest | 1.0000 | 1.0000 | No | Model A is not significantly different from Model B |
| Gradient Boosting vs Logistic Regression | 1.0000 | 1.0000 | No | Model A is not significantly different from Model B |

**Best Model Justification:** LogisticRegression was selected as the best model because it achieved the highest mean F1-score during stratified 5-fold cross-validation. Significance tests (McNemar and DeLong AUC) were conducted to verify if the performance improvements are statistically significant.

---
