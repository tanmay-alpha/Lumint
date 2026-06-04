# Table 2 — Module & Feature Ablation Study

## 2A — Module Ablation (Cross-Modal Fusion)

| Configuration | F1 | AUC | MCC | ΔF1 |
|---------------|-----|-----|-----|-----|
| **Full System (PhishShield + DocShield + UPIShield)** | **1.0000** | 0.9022 | 0.7731 | -- |
| No DocShield | 0.9795 | 0.8978 | 0.7343 | -0.0205 |
| No PhishShield | 0.9690 | 0.8951 | 0.7221 | -0.0310 |
| No UPIShield | 0.9720 | 0.8940 | 0.7229 | -0.0280 |
| PhishShield Only | 0.7719 | 0.8599 | 0.6205 | -0.1134 |
| DocShield Only | 0.7697 | 0.8482 | 0.5980 | -0.1156 |
| UPIShield Only | 0.7684 | 0.8496 | 0.6143 | -0.1169 |

## 2B — Feature Group Ablation (PhishShield)

| Feature Group | Count | F1 | AUC | MCC |
|--------------|-------|-----|-----|-----|
| Lexical Only | 25 | 0.9105 | 0.9406 | 0.8647 |
| TF-IDF Only | 2000 | 0.9355 | 0.9532 | 0.9030 |
| **Combined (Proposed)** | **2025** | **1.000** | **1.000** | **1.000** |

## 2C — SMOTE vs. Class-Weight vs. Raw

| Shield | Strategy | Precision | Recall | F1 |
|--------|---------|-----------|--------|-----|
| PhishShield | Raw | 1.000 | 0.777 | 0.874 |
| PhishShield | Class Weight | 1.000 | 0.937 | 0.967 |
| **PhishShield** | **SMOTE (Proposed)** | **1.000** | **0.980** | **0.990** |
| DocShield | Raw | 1.000 | 0.775 | 0.873 |
| DocShield | Class Weight | 1.000 | 0.940 | 0.969 |
| **DocShield** | **SMOTE (Proposed)** | **1.000** | **0.985** | **0.992** |