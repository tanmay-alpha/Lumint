# Automated Stress & Real User Concurrency Test Report

Generated at: 2026-06-05 04:00:27

## Performance Telemetry

| Metric | Value |
| --- | --- |
| Total Simulated Requests | 100 |
| Successful Requests (200 OK) | 100 |
| Failed/Error Requests | 0 |
| Execution Duration | 3.41s |
| Avg Latency | 2.8736s |
| p95 Latency | 3.3906s |
| Min Latency | 2.0907s |
| Max Latency | 3.3996s |

## Status Code Distribution

- **HTTP 200**: 100 requests

## Endpoint Specific Metrics

- **/api/documents/analyze**: Avg Latency: 2.4763s, Min: 2.0907s, Max: 3.2516s
- **/api/upi/analyze**: Avg Latency: 3.2709s, Min: 3.1999s, Max: 3.3996s

## Error Logs & Diagnosis

✅ **No errors detected! All 100 concurrent requests processed successfully without database lockups or memory leaks.**
