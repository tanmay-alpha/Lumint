# Lumint

**AI-powered multimodal fraud intelligence platform for document forensics, phishing detection, UPI payment screenshot analysis, fraud campaign clustering, explainable risk fusion, and research-grade fraud evaluation.**

Lumint is a full-stack fraud intelligence system built for portfolio, hackathon, and academic research use. It combines a **FastAPI backend**, a **premium Next.js frontend**, and a dedicated **research evaluation layer** for benchmarking, ablation studies, consensus comparison, and paper-ready report generation.

The platform is designed around one core idea:

> Fraud should not be detected through isolated signals. Lumint correlates document evidence, phishing indicators, payment screenshot forensics, campaign fingerprints, and explainable risk contributions into a unified intelligence workflow.

---

## Project Status

| Area                            | Status                                 |
| ------------------------------- | -------------------------------------- |
| Backend API                     | Complete and tested                    |
| Frontend UI                     | Premium Lumint interface implemented   |
| DocShield                       | Implemented                            |
| PhishShield                     | Implemented                            |
| Fraud DNA                       | Implemented                            |
| UPI Shield                      | Implemented and research-hardened      |
| Groq AI Analyst Layer           | Implemented with fallback behavior     |
| XAI Contribution Engine         | Implemented                            |
| Cross-Modal Fusion Score        | Implemented                            |
| Research Evaluation Foundation  | Implemented                            |
| Paper Scaffold                  | Implemented                            |
| Real-world benchmark execution  | Planned / local-only datasets required |
| Production deployment hardening | In progress                            |

Lumint is currently an **active research prototype**. It is not yet a production fraud prevention system.

---

## Core Features

### DocShield — Document & Image Forensics

DocShield analyzes uploaded PDFs, PNGs, and JPGs for fraud signals.

Capabilities include:

* Metadata extraction and inconsistency checks
* PDF/image forensic signal extraction
* Error Level Analysis style tamper detection
* Layout and text irregularity analysis
* Risk scoring with human-readable indicators
* AI-generated analyst explanation through Groq
* Feature contribution output for explainability

---

### PhishShield — URL Phishing Intelligence

PhishShield checks suspicious URLs using deterministic security heuristics.

Capabilities include:

* Domain normalization
* HTTP/HTTPS checks
* Bank impersonation and typosquatting detection
* Suspicious keyword analysis
* Long domain and excessive hyphen checks
* Suspicious TLD detection
* Official bank domain whitelisting
* Risk scoring and triggered-rule reporting
* AI-generated phishing explanation

---

### UPI Shield — Indian Digital Payment Screenshot Forensics

UPI Shield focuses on India-specific payment fraud patterns.

Capabilities include:

* PNG/JPG screenshot analysis
* OCR adapter with safe fallback behavior
* UTR extraction and validation
* PhonePe / GPay / Paytm / BHIM detection
* Payment app color profile checks
* ELA-style screenshot tamper scoring
* Font consistency heuristics
* Amount, payee, and transaction reference extraction
* UPI forensic benchmark support
* Optional Groq AI analyst review

---

### Fraud DNA — Campaign Fingerprinting & Clustering

Fraud DNA turns isolated fraud events into reusable intelligence.

Capabilities include:

* Event fingerprint generation
* Local event storage for demo/research use
* Campaign clustering
* Graph-ready network output
* Common indicator extraction
* Campaign-level AI brief generation
* Support for document, URL, and UPI signals

---

### Cross-Modal Lumint Risk Score

Lumint includes a fusion engine that combines multiple fraud modalities.

Default fusion weights:

| Modality             | Weight |
| -------------------- | -----: |
| Document / DocShield |   0.35 |
| URL / PhishShield    |   0.35 |
| UPI / UPI Shield     |   0.30 |

The fusion engine returns:

* Unified score
* Risk level
* Dominant signal
* Per-modality score breakdown
* Correlation flags
* Explainable summary

---

### XAI Contribution Engine

Lumint includes a deterministic, SHAP-compatible contribution engine.

It maps triggered rules and model-like features into normalized contribution percentages.

Important note:

> This layer is currently a deterministic SHAP-compatible attribution schema. It should not be described as real SHAP over trained ML models unless a trained model and SHAP runtime are explicitly added.

---

### AI Analyst Layer

Lumint uses Groq / LLaMA 3.3 70B for natural-language fraud explanations.

AI endpoints are designed with safe fallback behavior so the system does not fail when the API key is missing.

Use cases:

* Document fraud summary
* Phishing explanation
* Campaign brief
* UPI screenshot forensic explanation

---

## System Architecture

```text
User
  ↓
Next.js Frontend
  ↓
FastAPI Backend
  ↓
Fraud Intelligence Modules
  ├── DocShield
  ├── PhishShield
  ├── UPI Shield
  ├── Fraud DNA
  ├── Case Manager
  ├── Threat Feed
  └── AI Analyst Layer
  ↓
Risk / XAI / Fusion Layer
  ├── Feature Contributions
  ├── Cross-Modal Score
  ├── Correlation Flags
  └── AI Explanation
  ↓
Research Layer
  ├── Dataset Manifests
  ├── Metrics Engine
  ├── Benchmark Runner
  ├── Consensus Agreement
  ├── Ablation Studies
  ├── Paper Tables
  └── Paper Scaffold
```

---

## Tech Stack

### Backend

* Python 3.11
* FastAPI
* Pydantic v2
* SQLAlchemy
* SQLite for local development
* Pillow
* NumPy
* OpenCV where available
* Groq SDK
* Pytest

### Frontend

* Next.js App Router
* TypeScript
* Tailwind CSS
* Framer Motion
* Lucide icons
* Custom Lumint design system

### Research Layer

* Pure Python metrics
* Dataset manifests
* Benchmark experiment runner
* Consensus agreement layer
* Ablation study runner
* Paper table generator
* Dataset ingestion and anonymization utilities

---

## Frontend Design Direction

Lumint uses a premium light visual system:

* Background: `#F7F8FA`
* Cards: white / cool-white / glass surfaces
* Accent: ice blue `#0EA5E9`
* Typography:

  * Instrument Serif for headings
  * Geist for body text
  * DM Mono for data and technical values
* Motion: Framer Motion
* AI cards: dashed border, cool-white background, `LLaMA 3.3 70B · Groq` badge

The design intentionally avoids the generic dark-purple AI SaaS aesthetic.

---

## Main Frontend Pages

| Route          | Purpose                          |
| -------------- | -------------------------------- |
| `/`            | Premium product landing page     |
| `/dashboard`   | Platform overview and stats      |
| `/docshield`   | Document/image forensics         |
| `/upi-shield`  | UPI screenshot fraud analysis    |
| `/phishshield` | URL phishing checker             |
| `/fraud-dna`   | Campaign graph and clusters      |
| `/events`      | Recent event activity            |
| `/settings`    | Platform configuration and notes |

---

## API Overview

Representative backend endpoints include:

### Health

```http
GET /api/health
```

### DocShield

```http
POST /api/documents/analyze
```

### PhishShield

```http
POST /api/phishing/check
```

### UPI Shield

```http
POST /api/upi/analyze
POST /api/upi/analyze-screenshot
```

### Fraud DNA

```http
GET  /api/fraud-dna/fingerprints
GET  /api/fraud-dna/campaigns
GET  /api/fraud-dna/graph
POST /api/fraud-dna/recluster
```

### Dashboard

```http
GET /api/dashboard/stats
GET /api/dashboard/recent-events
GET /api/dashboard/risk-distribution
GET /api/dashboard/indicator-summary
```

### Fusion

```http
POST /api/fusion/score
```

### AI Analyst

```http
POST /api/ai/analyze-document
POST /api/ai/analyze-phishing
POST /api/ai/campaign-brief
```

For the latest exact API contract, run the backend and open:

```text
http://127.0.0.1:8000/docs
```

---

## Repository Structure

```text
Lumint/
├── backend/
│   ├── app/
│   │   ├── core/
│   │   ├── routers/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── ai/
│   │   └── main.py
│   ├── research/
│   │   ├── dataset_manifest.py
│   │   ├── metrics.py
│   │   ├── baselines.py
│   │   ├── experiment_runner.py
│   │   ├── report_writer.py
│   │   ├── consensus_adapters.py
│   │   ├── agreement.py
│   │   ├── ablation.py
│   │   ├── statistics.py
│   │   ├── paper_tables.py
│   │   └── fixtures/
│   ├── scripts/
│   ├── tests/
│   └── requirements.txt
│
├── frontend/
│   ├── app/
│   ├── components/
│   ├── services/
│   ├── types/
│   ├── lib/
│   ├── package.json
│   └── vercel.json
│
├── docs/
│   └── research/
│
├── paper/
│   ├── abstract.md
│   ├── introduction.md
│   ├── methodology.md
│   ├── evaluation.md
│   ├── results.md
│   ├── limitations.md
│   └── references/
│
└── README.md
```

---

## Local Development

### 1. Clone the repository

```powershell
git clone https://github.com/tanmay-alpha/lumint.git
cd lumint
```

---

## Backend Setup

```powershell
cd backend
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Backend URLs:

```text
API:      http://127.0.0.1:8000
Swagger:  http://127.0.0.1:8000/docs
Health:   http://127.0.0.1:8000/api/health
```

---

## Frontend Setup

```powershell
cd frontend
npm install
npm run dev
```

Frontend URL:

```text
http://localhost:3000
```

---

## Environment Variables

### Backend `.env`

Create:

```text
backend/.env
```

Example:

```env
GROQ_API_KEY=your_groq_api_key_here
DATABASE_URL=sqlite:///./data/lumint_dev.db
```

Do not commit `.env`.

### Frontend `.env.local`

Create:

```text
frontend/.env.local
```

Example:

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

For production, set `NEXT_PUBLIC_API_BASE_URL` to the deployed backend URL.

---

## Testing

### Backend tests

```powershell
cd backend
venv\Scripts\Activate.ps1
pytest tests/ -v
```

### Backend import and compile check

```powershell
cd backend
venv\Scripts\Activate.ps1
python -c "import app.main; print('MAIN IMPORT OK')"
python -m compileall app research
```

### Frontend production build

```powershell
cd frontend
npm run build
```

---

## Research Evaluation

Lumint includes a dedicated research layer for reproducible experiments.

### Run URL benchmark

```powershell
cd backend
python scripts/run_research_benchmark.py --manifest research/fixtures/url_benchmark_manifest.json --module url
```

### Run UPI benchmark

```powershell
cd backend
python scripts/run_research_benchmark.py --manifest research/fixtures/upi_benchmark_manifest.json --module upi
```

### Run fusion benchmark

```powershell
cd backend
python scripts/run_research_benchmark.py --manifest research/fixtures/fusion_benchmark_manifest.json --module fusion
```

### Run ablation study

```powershell
cd backend
python scripts/run_ablation_study.py --manifest research/fixtures/fusion_benchmark_manifest.json --module fusion
```

### Collect paper tables

```powershell
cd backend
python scripts/collect_paper_tables.py --registry research/fixtures/paper_experiments.json --outputs-dir research_outputs --paper-dir ../paper --dry-run
```

Generated research outputs are ignored by Git.

---

## Research Milestones

| Milestone | Description                                                          | Status                |
| --------- | -------------------------------------------------------------------- | --------------------- |
| R1        | Dataset manifest, metrics engine, baselines, report writer           | Complete              |
| R2        | XAI contribution engine and cross-modal fusion score                 | Complete              |
| R3        | UPI Shield forensic hardening and synthetic benchmark fixtures       | Complete              |
| R4        | Benchmark experiment runner and paper-ready reports                  | Complete              |
| R5        | External consensus adapter and agreement layer                       | Complete              |
| R6        | Ablation studies, confidence intervals, error taxonomy, paper tables | Complete              |
| R7        | Paper scaffold and real dataset ingestion layer                      | Complete              |
| R8        | Public dataset adapters and full paper experiment orchestration      | Planned / in progress |

---

## Paper Direction

Working title:

**Lumint: A Unified Multimodal Fraud Intelligence Framework with Explainable Risk Fusion for Digital Payment Fraud**

The `paper/` directory contains a draft scaffold for:

* Abstract
* Introduction
* Related Work
* Methodology
* System Architecture
* Evaluation
* Results
* Limitations
* Ethics
* Conclusion

Important:

> Current synthetic benchmark results are not final real-world research results. Real dataset evaluation and external validation are still required before publication claims.

---

## Security and Privacy

Lumint is designed with privacy-aware research workflows.

The repository should not contain:

* API keys
* `.env` files
* Uploaded documents
* Real UPI screenshots
* Private datasets
* Local database files
* Generated research outputs
* Node modules
* Python virtual environments

Ignored examples:

```text
backend/uploads/
backend/data/*.db
backend/data/fraud_events.json
backend/research_outputs/
backend/real_datasets/
datasets/
data/raw/
data/private/
frontend/.next/
frontend/node_modules/
backend/venv/
.env
.env.local
```

Dataset ingestion utilities include anonymization helpers for:

* Emails
* Phone numbers
* UPI IDs
* UTR numbers
* Amount values
* URL paths and query strings

---

## Deployment

### Frontend

Target platform:

```text
Vercel
```

Recommended Vercel settings:

```text
Root Directory: frontend
Framework Preset: Next.js
Build Command: default or next build
Output Directory: default
```

Set environment variable:

```env
NEXT_PUBLIC_API_BASE_URL=https://your-backend-url
```

### Backend

Target platform:

```text
Railway or any FastAPI-compatible host
```

Backend command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Make sure backend secrets are configured only in the backend deployment environment.

---

## Roadmap

Upcoming work:

* Run real PhishTank / Mendeley phishing dataset experiments
* Build real UPI screenshot benchmark dataset with anonymization
* Add live VirusTotal / Urlscan / AbuseIPDB adapters for controlled evaluation
* Run large-scale ablation studies
* Generate final paper tables from real datasets
* Add reviewer-grade citations and related work
* Harden production auth, rate limiting, and file storage
* Deploy backend to Railway and connect Vercel frontend to production API

---

## Limitations

Lumint is currently a research prototype.

Known limitations:

* Synthetic fixtures are useful for reproducibility but not sufficient for publication-level claims
* External consensus adapters are currently fixture/stub based unless API keys are configured
* UPI OCR performance must be validated on real screenshots
* ELA and forensic signals are risk indicators, not proof of tampering
* Local SQLite and local file uploads are suitable for development, not production scale
* Final paper results require real datasets, baselines, and statistical validation

---

## License

License: TBD

---

## Status

Lumint is under active development as a research-oriented fraud intelligence platform and portfolio project.
