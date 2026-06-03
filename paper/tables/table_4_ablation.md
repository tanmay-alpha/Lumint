# Table 4: Multimodal Ablation Study

Evaluating the degradation of F1-Score when individual modal signals are ablated from the Fusion layer.

| Variant Name | Description | Record Count | Accuracy | F1 Score | Mean Latency (ms) |
|---|---|---|---|---|---|
| **full_lumint** | Full multi-modal integration using all DocShield, PhishShield, and UPI Shield signals. | 16 | 0.5000 | **0.3333** | 0.00 |
| **no_document_signal** (Best) | Ablates the DocShield document forensics score, relying on phishing and payment layers. | 16 | 0.5000 | **0.3333** | 0.00 |
| **no_phishing_signal** | Ablates the PhishShield URL risk score, relying on document forensics and payment layers. | 16 | 0.5000 | **0.3333** | 0.00 |
| **no_upi_signal** | Ablates the UPI Shield layout check forensics, relying on document and URL checks. | 16 | 0.5000 | **0.3333** | 0.00 |
| **equal_weights** | Equal weights assigned to all active modalities instead of standard dynamic priority weighting. | 16 | 0.5000 | **0.3333** | 0.00 |