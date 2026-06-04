# Lumint Demo Guide

A step-by-step 9-stage walkthrough to showcase the full Lumint system in ~15 minutes.

---

## Prerequisites

```bash
# 1. Clone and set up
git clone https://github.com/tanmay-alpha/lumint
cd lumint

# 2. Backend
cd backend
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env          # Add GROQ_API_KEY

# 3. Frontend
cd ../frontend && npm install
```

---

## Stage 1 — Start the Backend

```bash
cd backend
venv\Scripts\activate
uvicorn main:app --reload --port 8000
```

Expected: `Uvicorn running on http://127.0.0.1:8000`

---

## Stage 2 — Start the Frontend

```bash
cd frontend
npm run dev
```

Open: [http://localhost:3000](http://localhost:3000)

---

## Stage 3 — Live Threat Stream (WebSocket)

Navigate to the **Dashboard** tab. The live threat monitor auto-connects to `ws://localhost:8000/ws/stream`.

- Watch real-time threat events appear every ~2 seconds
- Each card shows: threat type, risk score, timestamp
- The stats bar updates: total threats, high-risk count, last detection time

**Demo tip:** Open browser DevTools → Network → WS to show the raw WebSocket frames.

---

## Stage 4 — PhishShield URL Analysis

```bash
curl -X POST http://localhost:8000/api/phish/analyze \
  -H "Content-Type: application/json" \
  -d '{"url": "http://paypal-secure-login.xyz/verify?id=12345"}'
```

Expected output:
```json
{
  "prediction": "phishing",
  "confidence": 0.97,
  "risk_score": 0.97,
  "top_features": ["tfidf_login", "url_entropy", "digit_ratio"]
}
```

---

## Stage 5 — DocShield Document Forensics

```bash
# Upload a test document (tampered PDF/image)
curl -X POST http://localhost:8000/api/doc/analyze \
  -F "file=@tests/fixtures/tampered_kyc.jpg"
```

Expected output:
```json
{
  "prediction": "tampered",
  "confidence": 1.0,
  "ela_max": 189.4,
  "metadata_mismatch": true
}
```

---

## Stage 6 — UPIShield Receipt Validation

```bash
curl -X POST http://localhost:8000/api/upi/analyze \
  -F "file=@tests/fixtures/fake_receipt.png"
```

Expected output:
```json
{
  "prediction": "fake",
  "confidence": 1.0,
  "utr_valid": false,
  "ocr_confidence": 0.31
}
```

---

## Stage 7 — Cross-Modal Fusion Score

```bash
curl -X POST http://localhost:8000/api/fusion/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "url": "http://paypal-secure-login.xyz/verify",
    "phish_score": 0.97,
    "doc_score": 1.0,
    "upi_score": 1.0
  }'
```

Expected output:
```json
{
  "fusion_score": 0.98,
  "verdict": "HIGH_RISK",
  "confidence_interval": [0.96, 1.00]
}
```

---

## Stage 8 — LLM Analyst Report

```bash
curl -X POST http://localhost:8000/api/llm/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "module": "phish",
    "features": {"url_entropy": 4.2, "digit_ratio": 0.31},
    "shap_values": {"tfidf_login": 0.45, "url_entropy": 0.38}
  }'
```

Expected output (truncated):
```json
{
  "report": {
    "verdict": "HIGH RISK - Phishing Detected",
    "confidence": "97%",
    "key_indicators": ["Suspicious TF-IDF n-grams", "High entropy URL"],
    "recommendation": "Block URL and alert user immediately.",
    "model_used": "phi3.5-mini-lora"
  }
}
```

---

## Stage 9 — Run Full Evaluation (Paper Tables)

```bash
cd backend
venv\Scripts\activate
python -m ml.final_eval
```

Output: `backend/reports/final/` — 6 tables + 3 figure JSONs + summary.json

---

## Video Recording Tips

1. Use a 1920×1080 window
2. Show stages in order 1 → 9
3. Pause 3 seconds on each JSON response
4. Highlight the WebSocket live feed (Stage 3) — most visually impressive
5. End on the paper table output (Stage 9)

---

## API Documentation

Interactive Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
