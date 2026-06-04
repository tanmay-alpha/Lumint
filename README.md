# Lumint: AI-Powered Banking Fraud Intelligence Operating System

Lumint is a premium, state-of-the-art AI-Powered Banking Fraud Intelligence Operating System. It provides real-time detection, correlation, explanation, and tracking of banking fraud across multiple channels: document forgery, phishing websites, and UPI transaction receipts.

---

## 🚀 Key Modules & Capabilities

### 🛡️ 1. DocShield (Document Forensics)
- **Error Level Analysis (ELA)**: Re-saves image layers under specified quality levels to highlight compression differences, exposing digital image tampering.
- **Metadata Inspection**: Extracts EXIF data, creator software, producer metadata, and modification timestamps.
- **Layout & Typographic Audit**: Audits spacing discrepancies, font inconsistencies, and suspicious layout deviations.
- **Fraud Classifier**: Predicts forgery probability using a custom scikit-learn model with heuristic fallback.

### 🎣 2. PhishShield (Phishing Check)
- **Heuristic Engine**: Inspects lexical properties (IP-based domain names, typosquatting, subdomains count, suspicious TLDs).
- **Brand Mimicry Detector**: Measures similarity (via Levenshtein and Jaro-Winkler distances) against major Indian and global banking domain profiles.
- **Phishing Classifier**: Utilizes a TF-IDF character/word n-gram pipeline combined with Logistic Regression to calculate domain risk scores.

### 📲 3. UPI Shield (UPI Transaction Verifier)
- **Optical Character Recognition (OCR)**: Scans UPI receipts (PhonePe, Google Pay, Paytm) to parse transaction values, sender/receiver handles, timestamps, and UTR (Unique Transaction Reference) numbers.
- **UTR Validity Auditor**: Validates checksum structures and formats based on specific app protocols.
- **Template & Font Fraud Guard**: Inspects receipts for typographic manipulations or color discrepancies.
- **AI Fraud Explainer**: Employs an intelligent LLM / heuristic workflow to write clear analyst notes and trace transaction anomalies.

### 🧬 4. Fraud DNA (Threat Clustering)
- **Feature Fingerprinting**: Extracts structural characteristics of incoming documents/URLs into a unique vector signature.
- **Clustering Engine**: Groups related threat vectors into distinct Fraud Campaigns.
- **Network Graph Visualizer**: Renders interactive relational graphs connecting fraudulent actors, domains, file hashes, and active campaigns.

### 🧠 5. Explorable XAI (Explainable AI)
- **SHAP (SHapley Additive exPlanations)**: Calculates game-theoretic feature contributions for every model prediction, indicating which factors increased or decreased the risk.
- **Fallback Importance Metrics**: Smoothly falls back to feature coefficients or feature importances if SHAP requirements are not fully loaded.

---

## 📂 Project Structure

```
Lumint/
├── backend/                  # FastAPI Backend Application
│   ├── app/                  # Main Application logic
│   │   ├── core/             # Fusion and XAI integration
│   │   ├── database/         # SQLAlchemy DB models & connection
│   │   ├── routers/          # FastAPI routes (docs, phishing, upi, etc.)
│   │   └── services/         # Core business logic & Fraud DNA
│   ├── ml/                   # Machine Learning pipeline
│   │   ├── datasets/         # Pre-processed CSV datasets
│   │   ├── models/           # Trained .joblib classifiers and scalers
│   │   ├── registry.py       # Singleton ML model registry
│   │   └── train.py          # Unified classifier training pipeline
│   ├── reports/              # Generated JSON/MD research reports (R10-R14)
│   ├── scripts/              # Command-line seed and benchmark utilities
│   ├── tests/                # Test suite (pytest)
│   └── main.py               # Uvicorn server entry point wrapper
├── frontend/                 # Next.js 14 Dashboard UI
│   ├── app/                  # App Router components, pages & layouts
│   ├── components/           # Premium design components (GlassCard, XAIBar, etc.)
│   ├── lib/                  # Fetch client and mock data layers
│   ├── public/               # Asset files
│   └── types/                # Strongly-typed TypeScript interfaces
├── docs/                     # Research methodology and plans
├── paper/                    # LaTeX source & Markdown files for the research paper
├── DATASETS.md               # Details on UCI and Synthetic reference datasets
└── README.md                 # Project Overview & Guide (this file)
```

---

## ⚙️ Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- Git

### 1. Backend Setup
Navigate to the `backend/` directory:
```bash
cd backend
```

Create and activate a virtual environment:
```bash
python -m venv venv
# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# On macOS/Linux:
source venv/bin/activate
```

Install dependencies:
```bash
pip install -r requirements.txt
```

Create a `.env` file from the example:
```bash
cp ../.env.example .env
```
*(Open `.env` and fill in API keys. If `GROQ_API_KEY` is not provided, Lumint will gracefully fall back to heuristic AI descriptions).*

Run DB migrations and seed demo data:
```bash
python scripts/seed_demo_data.py
```

Start the FastAPI development server:
```bash
uvicorn main:app --reload
```
The API documentation will be available at `http://localhost:8000/docs`.

### 2. Frontend Setup
Navigate to the `frontend/` directory:
```bash
cd ../frontend
```

Install dependencies:
```bash
npm install
```

Start the Next.js development server:
```bash
npm run dev
```
Open `http://localhost:3000` to access the interactive Lumint dashboard.

---

## 🧪 Testing & Research Pipelines

### Running Unit Tests
All tests are located in `backend/tests/`. To run the full suite:
```bash
cd backend
venv\Scripts\python -m pytest --tb=short -q
```

### ML Pipeline Training
To re-train all models (phishing, document forensics, UPI receipt fraud, and fusion meta-learner):
```bash
cd backend
venv\Scripts\python ml\train.py --train-all
```

### Ablation Studies (R11)
To run ablation evaluation on the models:
```bash
venv\Scripts\python scripts\run_ablation_study.py --module fusion
```

### Benchmarks (R10)
To verify latency, accuracy, and consensus rates:
```bash
venv\Scripts\python scripts\run_research_benchmark.py --module fusion
```

### Cross-Dataset Generalization (R12)
To run cross-dataset experiments comparing synthetic and real-world models:
```bash
venv\Scripts\python ml\experiments\run_real_data.py
```

---

## 📊 Research Reports
Research artifacts, Ablation studies (R11), and Baseline benchmarks (R10) are located in the `backend/reports/` directory.

- **Statistical Table**: `backend/reports/r10_tables.md`
- **Ablation Tables**: `backend/reports/r11_ablation_tables.md`
- **Comparison Table**: `backend/reports/r12_comparison_table.md`
- **Cross-Dataset Results**: `backend/reports/r12_cross_dataset_table.md`
