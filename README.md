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
