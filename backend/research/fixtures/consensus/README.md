# Lumint Offline Consensus Fixtures

This directory contains offline validation fixtures representing consensus decisions from simulated external threat engines (VirusTotal, Urlscan.io, AbuseIPDB) and baseline ground truth.

## Files
* `url_consensus_fixture.json`: Consensus classifications for PhishShield URL endpoints.
* `upi_consensus_fixture.json`: Consensus classifications for UPI Shield receipts and screenshots.
* `fusion_consensus_fixture.json`: Consensus classifications for Cross-Modal Fusion cases.

## Format Schema
Every consensus fixture matches the following structure:
```json
{
  "provider": "fixture",
  "version": "r5-offline-v1",
  "items": [
    {
      "record_id": "unique-record-id",
      "target": "target-value-or-path",
      "consensus_label": "CLEAN" | "SUSPICIOUS" | "HIGH",
      "confidence": 0.95,
      "raw_score": 85.0,
      "evidence": ["Evidence log entry 1", "Evidence log entry 2"],
      "metadata": {
        "provider": "original-external-engine-reference",
        "custom_key": "custom_value"
      }
    }
  ]
}
```
