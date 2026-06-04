# Lumint Research Milestone R11 — Ablation Study & Feature Analysis

This document contains the systematic ablation studies and feature importances for Lumint's sub-shields and fusion layer.

## Table A: Module Ablation (Cross-Modal Fusion)
Tests the performance contribution of individual shields in the cross-modal fusion meta-learner.

| Configuration | Features / Shields | F1 Score | AUC-ROC | MCC | &Delta; F1 |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Full System** | DocShield + PhishShield + UPIShield | 0.8853 | 0.9022 | 0.7731 | -- |
| **No DocShield** | PhishShield + UPIShield only | 0.8648 | 0.8978 | 0.7343 | -0.0205 |
| **No PhishShield** | DocShield + UPIShield only | 0.8543 | 0.8951 | 0.7221 | -0.0310 |
| **No UPI Shield** | DocShield + PhishShield only | 0.8573 | 0.8940 | 0.7229 | -0.0280 |
| **PhishShield Only** | PhishShield single modal | 0.7719 | 0.8599 | 0.6205 | -0.1134 |
| **DocShield Only** | DocShield single modal | 0.7697 | 0.8482 | 0.5980 | -0.1156 |
| **UPI Shield Only** | UPIShield single modal | 0.7684 | 0.8496 | 0.6143 | -0.1169 |

## Table B: Feature Group Ablation
Evaluates the synergy between feature groups within PhishShield and DocShield.

| Module / Shield | Feature Group | Feature Count | F1 Score | AUC-ROC | MCC | &Delta; F1 |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **PhishShield** | Group A: Lexical Only | 25 | 0.9105 | 0.9406 | 0.8647 | -0.0895 |
| **PhishShield** | Group B: TF-IDF Only | 2000 | 0.9355 | 0.9532 | 0.9030 | -0.0645 |
| **PhishShield** | Group C: Combined | 2025 | 1.0000 | 1.0000 | 1.0000 | -- |
| **DocShield** | Group A: ELA Only | 4 | 0.9151 | 0.9475 | 0.8723 | -0.0849 |
| **DocShield** | Group B: Metadata Only | 9 | 0.9234 | 0.9512 | 0.8846 | -0.0766 |
| **DocShield** | Group C: Combined | 13 | 1.0000 | 1.0000 | 1.0000 | -- |

## Table C: Class Balancing Strategy Comparison
Compares default imbalanced training to SMOTE and balanced class weights. Focuses heavily on Recall.

| Module / Shield | Strategy / Configuration | Precision | Recall (Fraud) | F1 Score | AUC-ROC |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **PhishShield** | Raw (Imbalanced / No SMOTE) | 1.0000 | 0.7767 | 0.8743 | 1.0000 |
| **PhishShield** | Class Weight (Balanced) | 1.0000 | 0.9367 | 0.9673 | 1.0000 |
| **PhishShield** | SMOTE Oversampling (Proposed) | 1.0000 | 0.9800 | 0.9899 | 1.0000 |
| **DocShield** | Raw (Imbalanced / No SMOTE) | 1.0000 | 0.7750 | 0.8732 | 1.0000 |
| **DocShield** | Class Weight (Balanced) | 1.0000 | 0.9400 | 0.9691 | 1.0000 |
| **DocShield** | SMOTE Oversampling (Proposed) | 1.0000 | 0.9850 | 0.9924 | 1.0000 |
| **UPIShield** | Raw (Imbalanced / No SMOTE) | 1.0000 | 0.7600 | 0.8636 | 1.0000 |
| **UPIShield** | Class Weight (Balanced) | 1.0000 | 0.9800 | 0.9899 | 1.0000 |
| **UPIShield** | SMOTE Oversampling (Proposed) | 1.0000 | 0.9867 | 0.9933 | 1.0000 |

## Table D: Global Feature Importance (Top 10 SHAP Values)
Presents the global mean absolute SHAP values and impact directions for the top 10 features of each shield.

### PhishShield Top Features
| Rank | Feature Name | Mean Absolute SHAP | Direction of Impact | Interpretation / Paper Context |
| :---: | :--- | :---: | :---: | :--- |
| 1 | `tfidf_p:` | 0.18390 | Positive (Higher -> Fraud) | Frequency of character n-gram 'p:' characteristic of phishing domain structures |
| 2 | `tfidf_p:/` | 0.18390 | Positive (Higher -> Fraud) | Frequency of character n-gram 'p:/' characteristic of phishing domain structures |
| 3 | `tfidf_p://` | 0.18390 | Positive (Higher -> Fraud) | Frequency of character n-gram 'p://' characteristic of phishing domain structures |
| 4 | `tfidf_tp:` | 0.18390 | Positive (Higher -> Fraud) | Frequency of character n-gram 'tp:' characteristic of phishing domain structures |
| 5 | `tfidf_tp:/` | 0.18390 | Positive (Higher -> Fraud) | Frequency of character n-gram 'tp:/' characteristic of phishing domain structures |
| 6 | `tfidf_ttp:` | 0.18390 | Positive (Higher -> Fraud) | Frequency of character n-gram 'ttp:' characteristic of phishing domain structures |
| 7 | `has_https` | 0.17991 | Negative (Higher -> Clean) | Missing HTTPS signals insecure transmission, though phishing sites may use free SSL |
| 8 | `tfidf_ps:` | 0.16271 | Negative (Higher -> Clean) | Frequency of character n-gram 'ps:' characteristic of phishing domain structures |
| 9 | `tfidf_ps:/` | 0.16271 | Negative (Higher -> Clean) | Frequency of character n-gram 'ps:/' characteristic of phishing domain structures |
| 10 | `tfidf_s:` | 0.16271 | Negative (Higher -> Clean) | Frequency of character n-gram 's:' characteristic of phishing domain structures |

### DocShield Top Features
| Rank | Feature Name | Mean Absolute SHAP | Direction of Impact | Interpretation / Paper Context |
| :---: | :--- | :---: | :---: | :--- |
| 1 | `metadata_anomaly_score` | 1.33846 | Positive (Higher -> Fraud) | Multiple contradictory flags in document metadata suggest structural forgery |
| 2 | `ela_max` | 1.23768 | Positive (Higher -> Fraud) | Maximum localized error level peak signals presence of sharp digitally added borders |
| 3 | `ela_std` | 1.22521 | Positive (Higher -> Fraud) | High variance in error levels suggests localized copy-paste manipulation of elements |
| 4 | `ela_mean` | 1.20786 | Positive (Higher -> Fraud) | Elevated average ELA density points to systematic modifications in the document |
| 5 | `ela_high_pixel_ratio` | 1.10537 | Positive (Higher -> Fraud) | High density of high-frequency error pixels confirms localized tampering |
| 6 | `creation_to_mod_delta_days` | 0.65979 | Negative (Higher -> Clean) | Large mismatch between creation and modification times implies retroactively edited files |
| 7 | `font_count` | 0.63951 | Negative (Higher -> Clean) | High font counts signify composite documents created from multiple distinct sources |
| 8 | `page_count` | 0.59944 | Negative (Higher -> Clean) | Atypical page count deviations indicate document modification or replacement |
| 9 | `file_size_kb` | 0.53371 | Negative (Higher -> Clean) | Abnormally large file size compared to content length suggests appended hidden data |
| 10 | `image_count` | 0.42957 | Negative (Higher -> Clean) | Excessive embedded image count is typical of scanned documents hiding editable text |

### UPIShield Top Features
| Rank | Feature Name | Mean Absolute SHAP | Direction of Impact | Interpretation / Paper Context |
| :---: | :--- | :---: | :---: | :--- |
| 1 | `ocr_confidence` | 1.74186 | Negative (Higher -> Clean) | Low OCR confidence scores suggest poor quality text rendering typical of editing overlays |
| 2 | `forgery_score_heuristic` | 1.72552 | Positive (Higher -> Fraud) | Higher heuristic score flags suspicious layouts and text alignment anomalies |
| 3 | `ela_tamper_regions` | 1.44191 | Positive (Higher -> Fraud) | Error Level Analysis isolates localized modifications near transaction amounts |
| 4 | `font_consistent` | 1.07760 | Negative (Higher -> Clean) | Inconsistent font rendering suggests overlaying fake text on an original screenshot |
| 5 | `color_authentic` | 0.92090 | Negative (Higher -> Clean) | Atypical brand color deviations signify color space conversion from edits |
| 6 | `utr_valid` | 0.81882 | Negative (Higher -> Clean) | Invalid UTR sequence confirms the transaction ID is fabricated |
| 7 | `app_detected_encoded` | 0.58441 | Positive (Higher -> Fraud) | Mismatch between layout structure and detected UPI app brand patterns indicates tampering |
| 8 | `utr_length` | 0.55230 | Negative (Higher -> Clean) | Incorrect UTR length deviates from standard bank message protocols |
