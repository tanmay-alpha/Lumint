# Introduction

Digital payment mechanisms like UPI (Unified Payments Interface) have democratized financial access but have also created new surfaces for malicious actors. Fraud campaigns today are rarely unimodal. A typical scam campaign might involve:
1. Pushing a phishing link (URL) via SMS/WhatsApp.
2. Sharing forged transaction screenshots to claim fake payments (Image/Screenshot).
3. Using manipulated ID documents or invoices to deceive merchant portals (Document/PDF).

Traditional fraud detection engines fail to connect these disparate signals. Unimodal systems examine each vector in isolation, completely missing the unified footprint of a coordinated campaign.

To bridge this gap, we present **Lumint**, an open-source multimodal fraud intelligence framework. Lumint consolidates screenshot forensics, URL analysis, document validation, and graph-based relationships. 

### Contributions
- **Explainable Cross-Modal Risk Fusion**: A dynamic weighting engine that combines independent modality scores into a single risk probability while outputting feature contribution metrics.
- **UPI Screenshot Forensics Hardening**: Deep validation of transaction images using Error Level Analysis (ELA), font consistency checks, and automatic UTR (Unique Transaction Reference) validation.
- **External Consensus Layer**: Native wrappers for external indicators to compute inter-rater agreement (Cohen's & Fleiss' Kappa) against local predictions.
- **Reproducible Evaluation Infrastructure**: A dataset ingestion and anonymization layer allowing safe research on real-world datasets without privacy leaks.
