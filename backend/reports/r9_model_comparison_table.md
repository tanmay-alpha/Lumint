# Table R9.1: ML Model Performance Comparison (Stratified 5-Fold CV)

| Module | Model | Precision | Recall | F1 | AUC | MCC | Log-Loss |
|--------|-------|-----------|--------|-----|-----|-----|----------|
| PhishShield | LogisticRegression **[Best]** | 1.0000 | 1.0000 | **1.0000** | 1.0000 | 1.0000 | 0.0002 |
| PhishShield | RandomForest | 1.0000 | 1.0000 | **1.0000** | 1.0000 | 1.0000 | 0.0016 |
| PhishShield | GradientBoosting | 1.0000 | 1.0000 | **1.0000** | 1.0000 | 1.0000 | 0.0000 |
| DocShield | LogisticRegression **[Best]** | 1.0000 | 1.0000 | **1.0000** | 1.0000 | 1.0000 | 0.0006 |
| DocShield | RandomForest | 1.0000 | 1.0000 | **1.0000** | 1.0000 | 1.0000 | 0.0000 |
| DocShield | GradientBoosting | 1.0000 | 1.0000 | **1.0000** | 1.0000 | 1.0000 | 0.0000 |
| UPI Shield | LogisticRegression **[Best]** | 1.0000 | 1.0000 | **1.0000** | 1.0000 | 1.0000 | 0.0014 |
| UPI Shield | RandomForest | 1.0000 | 1.0000 | **1.0000** | 1.0000 | 1.0000 | 0.0000 |
| UPI Shield | GradientBoosting | 1.0000 | 1.0000 | **1.0000** | 1.0000 | 1.0000 | 0.0000 |
| Cross-modal Fusion | LogisticRegression (Meta) | 1.0000 | 1.0000 | **1.0000** | 1.0000 | 1.0000 | 0.0000 |

> **[Best]** = Best model selected for deployment (by F1 score)
> All results: random_state=42, SMOTE on training folds only


# Table R9.2: Cross-Modal Ablation - Fusion vs. Individual Modules

| Configuration | F1 | AUC | Precision | Recall |
|---------------|-----|-----|-----------|--------|
| Lumint Fusion (All Modules) | **1.0000** | 1.0000 | 1.0000 | 1.0000 |
| PhishShield Only | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| DocShield Only | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| UPI Shield Only | 1.0000 | 1.0000 | 1.0000 | 1.0000 |

## Fusion Meta-Learner Coefficients

| Input Signal | Coefficient | Weight (%) |
|-------------|-------------|------------|
| phish_prob | 3.3049 | 35.5% |
| doc_prob | 3.0027 | 32.3% |
| upi_prob | 2.9931 | 32.2% |