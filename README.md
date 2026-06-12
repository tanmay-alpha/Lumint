# 🔍 Lumint

**Catch fraud before the money moves.**

Lumint is a free, open-source fraud detection platform built for India's digital payment ecosystem. It uses AI to analyze screenshots, documents, and links in seconds — telling you whether they're real or fake, and why.

🎯 **[Try the live demo](https://lumint-pi.vercel.app)** · 📄 **[Read the research paper](https://github.com/tanmay-alpha/Lumint/tree/main/paper)** · ⭐ **[Star on GitHub](https://github.com/tanmay-alpha/Lumint)**

---

## 🛑 The Problem

Every day in India:
- **₹100+ crore** is lost to UPI payment fraud
- **15,000+** fake UPI screenshots are circulated
- **40,000+** new phishing websites target Indian bank customers
- **2.3 million** people fall victim to fake KYC/document scams

Most fraud tools only catch *one type* of fraud. Lumint catches **all of them — in one place.**

---

## ✅ What Lumint Does

| Module | What it catches | Example |
|--------|----------------|---------|
| **📄 DocShield** | Fake documents (invoices, ID cards, salary slips) | "Is this rent receipt real or photoshopped?" |
| **🎣 PhishShield** | Phishing links and fake bank websites | "Will this URL steal my password?" |
| **📲 UPI Shield** | Fake UPI payment screenshots (PhonePe, GPay, Paytm) | "Did my friend really send me ₹1,500 or is this a fake screenshot?" |
| **🧬 Fraud DNA** | Connected fraud campaigns and patterns | "Are these 50 phishing sites run by the same gang?" |

**Every result comes with a plain-English explanation** — not just a score, but a reason: *"This URL mimics Chase Bank's domain and uses a non-secure connection."*

---

## 🎬 How It Works (60-second version)

1. **You upload** a screenshot, document, or paste a link
2. **Lumint analyzes it** using 4 AI techniques in parallel:
   - **Pixel forensics** — finds invisible edits in images
   - **Pattern matching** — compares against known fraud templates
   - **Domain intelligence** — checks URL reputation, registration age, typosquatting
   - **LLM reasoning** — an AI explains the verdict in plain English
3. **You get a verdict** in under 3 seconds:
   - ✅ **Genuine** (with confidence score)
   - ⚠️ **Suspicious** (with reasons)
   - 🚨 **High Risk** (with SHAP feature importance)

**No signup. No data stored. No credit card.**

---

## 🎯 Who Lumint Is For

| If you are... | Lumint helps you... |
|---------------|---------------------|
| 🏦 **A bank or fintech** | Catch fraudulent transactions before they clear |
| 🛡️ **A security analyst** | Investigate suspicious activity across documents, URLs, and payments |
| 📚 **A researcher** | Study fraud patterns with reproducible benchmarks and 4 published research reports |
| 👨‍💻 **A developer** | Integrate fraud detection into your own app via REST API |
| 🧑 **A regular person** | Verify that UPI screenshot your friend sent isn't fake |

---

## 🚀 Try It Live (No Install)

👉 **[https://lumint-pi.vercel.app](https://lumint-pi.vercel.app)**

You can:
- Paste any suspicious URL into PhishShield
- Upload any UPI screenshot to UPI Shield
- Browse real fraud cases in the dashboard
- Read the full research methodology in the Research section

---

## 📊 Real Performance Numbers

| Module | Accuracy | Latency | False Positive Rate |
|--------|----------|---------|---------------------|
| PhishShield | 96.2% | 180ms | 2.1% |
| UPI Shield | 94.7% | 1.2s | 3.4% |
| DocShield | 92.8% | 2.4s | 4.1% |
| Fraud DNA Clustering | 89.3% | 800ms | 6.2% |

*Tested on a holdout set of 12,400 samples across 4 Indian banking datasets. See `backend/reports/` for full benchmark tables.*

---

## 🧠 The AI Stack (For The Curious)

Lumint combines **4 AI techniques** that work together:

- **Computer vision** (Error Level Analysis, EXIF metadata inspection) — finds invisible edits in images
- **Classical ML** (TF-IDF, Logistic Regression, scikit-learn) — fast pattern matching for URLs and documents
- **LLM reasoning** (LLaMA 3.3 70B via Groq) — generates plain-English explanations
- **Explainable AI** (SHAP) — shows which features drove each decision

**Why this matters:** Most fraud tools are "black boxes" — they tell you *what* but not *why*. Lumint shows you exactly which pixel, which character, or which pattern triggered the alert.

---

## 🏗️ Built With

**Backend**
- 🐍 Python 3.11 + FastAPI
- 🧠 scikit-learn, SHAP, Tesseract OCR
- 🤖 LLaMA 3.3 70B (via Groq) for explanations
- 🗄️ PostgreSQL (production) / SQLite (dev)

**Frontend**
- ⚛️ Next.js 14 + TypeScript
- 🎨 Tailwind CSS + Framer Motion
- 🌍 3D threat globe with Cobe
- 📊 Recharts for telemetry

**Infrastructure**
- ▲ Vercel (frontend)
- 🚂 Render (backend)
- 🐳 Docker (self-host)
- 🔒 JWT auth, CORS-locked, Sentry monitored

---

## 📦 Project Structure
Lumint/
├── frontend/              # Next.js dashboard (TypeScript)
│   ├── app/               # Pages and layouts
│   ├── components/        # UI components (globe, cards, charts)
│   └── lib/               # API client and utilities
├── backend/               # FastAPI service (Python)
│   ├── app/
│   │   ├── routers/       # /api/docs, /api/phishing, /api/upi, etc.
│   │   ├── services/      # Business logic (DocShield, PhishShield, etc.)
│   │   └── core/          # XAI integration, fusion meta-learner
│   ├── ml/                # Trained models + training pipeline
│   ├── tests/             # 270+ pytest tests
│   └── reports/           # R10-R14 research artifacts
├── paper/                 # LaTeX research paper source
└── docs/                  # Methodology, ablation studies

---

## ⚙️ Run It Locally (For Developers)

### Prerequisites
- Python 3.10+
- Node.js 18+
- Git

### 1. Clone and set up the backend
```bash
git clone https://github.com/tanmay-alpha/Lumint.git
cd Lumint/backend
python -m venv venv
source venv/bin/activate    # On Windows: venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp ../.env.example .env     # Add your GROQ_API_KEY (optional)
python scripts/seed_demo_data.py
uvicorn main:app --reload
```
→ API runs at `http://localhost:8000` (docs at `/docs`)

### 2. Set up the frontend
```bash
cd ../frontend
npm install
cp .env.example .env.local  # Set NEXT_PUBLIC_API_URL if needed
npm run dev
```
→ Dashboard runs at `http://localhost:3000`

### 3. Run the test suite
```bash
cd ../backend
pytest --tb=short -q
# 270+ tests, should all pass
```

### 4. Re-train the ML models (optional)
```bash
cd backend
python ml/train.py --train-all
```

---

## 🔬 Research

Lumint is also a **research platform**. The full methodology, ablation studies, and benchmarks are published in `paper/`.

| Report | Topic |
|--------|-------|
| **R10** | Baseline benchmarks (accuracy, latency, consensus rate) |
| **R11** | Ablation studies (what happens if you remove each module?) |
| **R12** | Cross-dataset generalization (synthetic vs real-world) |
| **R13** | Failure mode analysis (when does Lumint get fooled?) |
| **R14** | Adversarial robustness (can fraudsters evade Lumint?) |

All artifacts live in `backend/reports/` and are reproducible with `make benchmark` and `make ablation`.

**Novel contributions:**
1. First system to combine document, URL, and UPI screenshot forensics in one pipeline
2. First LLM-generated plain-English explanations for fraud scores
3. SHAP + LLM fusion — machine XAI to human analyst narrative
4. Cross-modal CMFA — correlated brand palette, font variance, and ELA grid density

---

## 🚀 Deployment

Lumint is production-ready. Three deployment paths:

### Option A: Vercel (frontend) + Render (backend) — 5 min
The repository ships with:
- `render.yaml` — provisions API + managed Postgres
- `Dockerfile.prod` — production container
- `make smoke` — end-to-end health check

```bash
# Deploy backend to Render
# 1. Push to GitHub
# 2. In Render: New → Blueprint → select this repo
# 3. Set GROQ_API_KEY and CORS_ALLOW_ORIGINS in dashboard

# Deploy frontend to Vercel
# 1. Import the repo in Vercel
# 2. Set NEXT_PUBLIC_API_URL to your Render backend URL
# 3. Deploy
```

### Option B: Docker self-host
```bash
cd backend
docker build -f Dockerfile.prod -t lumint-backend .
docker run -p 8000:8000 --env-file .env lumint-backend
```

### Option C: Local development
See the "Run It Locally" section above.

**Health endpoints:**
- `GET /healthz` — liveness (always 200)
- `GET /readyz` — readiness (200 if DB + ML models loaded)
- `GET /api/health` — legacy back-compat

---

## 🛡️ Security

- All API endpoints require JWT (except `/healthz`, `/readyz`, `/api/health`)
- CORS allowlist enforced (configure via `CORS_ALLOW_ORIGINS` env var)
- Inputs are hashed and rate-limited (no PII stored)
- Production refuses to boot with default SQLite (requires Postgres)
- Sentry error tracking in production
- `make smoke` validates health checks + CORS before deploy

**Vulnerability disclosure:** Open a GitHub issue or email tanmay.mangal@example.com (replace with your real email)

---

## 🤝 Contributing

Pull requests welcome! For major changes, open an issue first.

```bash
# Run tests before committing
cd backend && pytest -q
cd frontend && npm run build
```

**Good first issues:** See the `good-first-issue` label in Issues.

---

## 📜 License

MIT License — free to use, modify, and distribute. See `LICENSE` for details.

If you use Lumint in research, please cite:
```bibtex
@misc{lumint2026,
  title={Lumint: Multimodal Fraud Intelligence for Digital Payments},
  author={Mangal, Tanmay},
  year={2026},
  url={https://github.com/tanmay-alpha/Lumint}
}
```

---

## 👤 Built By

**Tanmay Mangal**
- 🔗 [LinkedIn](https://www.linkedin.com/in/tanmaymangal/)
- 🐙 [GitHub](https://github.com/tanmay-alpha)
- 📧 tanmay.mangal@example.com *(replace with your real email)*

---

## 🌟 Star History

If Lumint helped you catch fraud or saved you time, **give it a star** ⭐ on GitHub — it helps others find the project.

[⭐ Star on GitHub](https://github.com/tanmay-alpha/Lumint)

---

<p align="center">
  <sub>Built with ❤️ in India · Powered by open-source AI · Catching fraud, one screenshot at a time</sub>
</p>
