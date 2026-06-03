# Paper Outline

## Title
Lumint: A Unified Multimodal Fraud Intelligence Framework with Explainable Risk Fusion for Digital Payment Fraud

## Proposed Outline

1. **Introduction**
   - Growth of digital payment fraud (UPI, QR codes, social engineering).
   - Limitation of existing unimodal systems (text-only, URL-only, image-only).
   - Contributions: Explainable cross-modal fusion, UPI screenshot forensic validation, external consensus aggregation.

2. **Related Work**
   - Fraud detection in financial transactions.
   - Multimodal machine learning for threat intelligence.
   - Explainable AI (XAI) in cybersecurity.
   - TODO: Add specific citations for state-of-the-art models.

3. **System Architecture**
   - DocShield: Document and identity proof forgery detection.
   - PhishShield: Phishing and malicious link assessment.
   - UPI Shield: Forensic analysis of transaction screenshots (UTR verification, ELA, font consistency).
   - Fraud DNA: Contextual relationship graphs.

4. **Methodology**
   - Explainable Cross-Modal Risk Fusion engine.
   - Consensus and Agreement Layer (Cohen's Kappa, Fleiss' Kappa, Weighted Agreement).
   - Ablation framework formulation.

5. **Experimental Evaluation**
   - Evaluation protocol: Synthetic fixtures vs. Real-world datasets.
   - Metrics: F1-Score, Precision, Recall, Latency, Confidence Intervals.
   - Ablation Studies: Removing modalities to measure performance degradation.

6. **Results & Discussion**
   - Synthetic benchmark results.
   - Feature contributions and XAI outputs.
   - Consensus adapter analysis.

7. **Limitations & Future Work**
   - OCR reliability limitations in low-resolution screens.
   - Latency overhead of cross-modal reasoning.
   - Generalizability to non-UPI platforms.

8. **Ethical Considerations & Privacy**
   - Anonymization protocol (redacting phone numbers, emails, UPI IDs, UTRs).
   - Data minimisation principles.

9. **Conclusion**
   - Summary of outcomes.
