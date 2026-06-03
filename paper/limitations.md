# Limitations

Although Lumint provides a robust multimodal detection pipeline, several limitations apply:

1. **OCR Quality Dependency**: UPI Shield screenshot forensics depend on OCR extraction quality. Low-resolution, blurry, or dark images might produce text candidates with spelling anomalies, reducing UTR extraction success.
2. **Computational Latency**: Because Lumint performs multi-stage fusion (including image ELA and document structure analysis), its mean latency is higher than single-modality checks.
3. **Consensus Key Expiry**: Evaluation against external services (VirusTotal, Urlscan) relies on API key availability and query quotas. If keys expire or rate limits are reached, the system falls back to cached results.
4. **Generalizability**: The screenshot parsing rules in UPI Shield are optimized for the most popular Indian UPI banking applications (e.g., Google Pay, PhonePe, Paytm). Formatting changes in these apps might require custom template updates.
