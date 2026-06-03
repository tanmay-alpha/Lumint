# Ethical Considerations

Multimodal fraud detection engines process highly sensitive user data, including personal phone numbers, bank accounts, emails, transaction amounts, and identity proofs. We address these ethical concerns through the following safeguards:

## Privacy & Anonymization
All real-world dataset ingestion is subjected to strict anonymization utilities prior to being written to manifest files:
- Emails are masked or replaced with hash identifiers.
- Phone numbers and transaction amounts are redacted.
- UPI IDs and Unique Transaction References (UTRs) are hashed using a salted HMAC algorithm to prevent re-identification.
- URL paths and query parameters are stripped, preserving only domain-level features for benign/malicious classification.

## Dual-Use Risks
While forensic analysis of screenshots (e.g., font consistency, ELA) is designed to detect fraud, detailed publication of check thresholds could be used by malicious actors to design more convincing fake screenshots. To mitigate this:
1. We present methodology at a high level without revealing specific heuristic threshold values.
2. The codebase operates defensively, validating structural formats rather than attempting to catalog every potential spoofing technique.
