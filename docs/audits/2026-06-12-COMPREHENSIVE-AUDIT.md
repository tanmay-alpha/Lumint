# Lumint — Comprehensive Research-Level Audit

**Date:** 2026-06-12
**Scope:** Backend (FastAPI), ML pipeline, Frontend (Next.js)
**Auditor:** Automated + manual code review

## Part 1: File Inventory

| Metric | Value |
|--------|-------|
| Python files (backend) | 219 |
| TS/TSX/CSS files (frontend) | 65 |
| Backend LOC | 26,774 |
| Frontend LOC | 12,344 |
| Test files | 39 |
| **Total LOC** | **~39,118** |

### Subsystem breakdown
- 27 files: `app/services/` (UPI, Phish, Doc, Fraud DNA)
- 23 files: `tests/ml/` (research pipeline tests)
- 15 files: `app/routers/`
- 12 files: `app/schemas/`
- 6 files: `research/dataset_adapters/`
- 6 files: `ml/features/`
- 5 files: `ml/stats/`, 5 `ml/ablation/`
- 4 files: `ml/llm/`, `ml/drift/`

## Part 2: Subsystem Analysis

### 2.1 UPI Module
- **Files:** `app/services/upi/{analyzer,app_detector,color_profile,font_consistency,ocr_adapter,screenshot_forensics,utr}.py`, `app/routers/upi.py`, `app/services/upi/analyzer_v2.py`
- **Status:** ✅ Production-ready
- **Strengths:** Layout-aware VPA selection, 10MB upload limit, ELA tamper localization, GPay dark-mode color support, PhonePe keyword list tightened
- **Weaknesses:** v1 model has F1=1.0 on synthetic data (memorization, not generalization)
- **Security:** 10MB limit, no path traversal (UUID filenames), URL inputs validated
- **Test coverage:** 13 tests in `test_upi_module.py`, 4 in `test_upi_analyzer_v2.py`, 6 in `test_ela_localization.py` = 23 tests ✅

### 2.2 Phishing Module
- **Files:** `app/services/phishshield/analyzer.py`, `app/services/phishshield/url_features.py`, `app/routers/phishing.py`
- **Status:** ✅ Production-ready
- **Strengths:** TF-IDF + lexical features, batch endpoint with 100-URL cap, URL field validator
- **Weaknesses:** Uses UCI phishing dataset; no real-time URL fetching (good — limits SSRF)
- **Security:** SSRF guard available (not used by phish because no fetch), auth-protected
- **Test coverage:** `test_phishing.py` ✅

### 2.3 Document Module
- **Files:** `app/services/docshield/analyzer.py`, `app/routers/documents.py`
- **Status:** ✅ Production-ready
- **Security:** Auth-protected, no size limit on document upload (gap)

### 2.4 AI Agent
- **Files:** `ai/{agent,client,phishshield_ai,docshield_ai,frauddna_ai,upi_ai}.py`
- **Status:** ✅ Production-ready
- **Strengths:** Singleton client, retry with backoff, graceful fallback
- **Caveat:** No PII filter on prompts (sends full OCR text to Groq)

### 2.5 Research Pipeline
- **Files:** `ml/{train,train_upi_v2,calibrate,registry}.py`, `ml/features/`, `ml/{ablation,adversarial,drift,experiments,llm}/`
- **Status:** ✅ Strong
- **Strengths:** 5-model baseline (LR+RF+GB+XGB+LGB), 5-fold CV, SMOTE, calibration
- **Weaknesses:** v1 UPI reports F1=1.0 on training data (not held-out)
- **v2:** 80+ features, 4-model ensemble, Platt scaling — production-ready but needs real data

### 2.6 Core Infrastructure
- **Files:** `app/{main,config,database,lifespan}.py`, `app/core/{fusion,xai,event_publisher,ssrf_guard}.py`
- **Status:** ✅ Production-ready
- **Strengths:** Request-ID middleware, settings validation, SSRF guard with 8 CIDR blocks

### 2.7 Routers (12 total)
All 12 routers use `Depends(get_current_user)` ✅
- Unauthenticated: `health`, `probes`, root `/` (intentional)

### 2.8 Frontend
- **Status:** ✅ Production-ready
- **Strengths:** Error boundary (`error.tsx`), loading state, 404 pages (root + 2 route groups), `role="alert"` aria-live on UPI error
- **Pages:** 10 (1 marketing, 9 dashboard)

## Part 3: Security Audit

### 3.1 Authentication
- **Score:** B+
- **Findings:**
  - ⚠️ `app/dependencies/auth.py:46` — plain `token != api_key` (vulnerable to **timing attack**)
  - ✅ All 12 routers require `get_current_user`
  - ✅ Dev-mode fallback (no key = allow) clearly logged
  - ⚠️ API key not hashed, sent as plaintext Bearer
- **Recommendations:** Use `hmac.compare_digest()` for constant-time comparison

### 3.2 Input Validation
- **Score:** B
- **Findings:**
  - ✅ UPI: 10MB size limit (`MAX_UPLOAD_SIZE`)
  - ✅ Phishing batch: `max_length=100`, per-URL 2048 char limit
  - ✅ Document upload: 15MB limit + magic-byte validation (`documents.py:58`)
  - ⚠️ OCR text not length-limited before sending to Groq

### 3.3 Data Exposure
- **Score:** A
- **Findings:**
  - ✅ No stack traces in HTTPException details
  - ✅ No PII in logger output (one `logger.warning("Invalid API key attempt")` — no token logged)
  - ⚠️ OCR text is sent to Groq — opt-in for production

### 3.4 CORS & Headers
- **Score:** B+
- **Findings:**
  - ✅ CORS allowlist from `CORS_ALLOW_ORIGINS` env var (JSON or CSV)
  - ✅ Request-ID middleware (correlates logs)
  - ⚠️ No security headers: CSP, X-Frame-Options, HSTS, X-Content-Type-Options

### 3.5 Database Security
- **Score:** A-
- **Findings:**
  - ✅ SQLAlchemy ORM (parameterized queries — no SQLi)
  - ✅ `validate_production_db` blocks `APP_ENV=prod` with dev SQLite
  - ✅ Sessions via `get_db` dependency

### 3.6 WebSocket Security
- **Score:** B
- **Findings:**
  - ✅ Auth-protected (`Depends(get_current_user)` on `/ws`)
  - ⚠️ No connection limit / rate limit on WebSocket
  - ⚠️ No message size cap

### 3.7 ML Pipeline Security
- **Score:** B-
- **Findings:**
  - ⚠️ `joblib.load` = pickle deserialization (RCE if `ml/models/` is writable)
  - ✅ Models loaded at startup from fixed `MODELS_DIR`
  - ✅ Model output clamped to [0, 1] in `registry.predict_proba`

## Part 4: Test Coverage

| Subsystem | Tests | Files | Status |
|-----------|-------|-------|--------|
| UPI module | 13 | `test_upi_module.py` | ✅ |
| UPI v2 | 4 | `test_upi_analyzer_v2.py` | ✅ |
| ELA localization | 6 | `test_ela_localization.py` | ✅ |
| SSRF guard | 12 | `test_ssrf_guard.py` | ✅ |
| Phishing | ~6 | `test_phishing.py` | ✅ |
| Documents | ~5 | `test_image_upload.py` | ✅ |
| Health | 1 | `test_health.py` | ✅ |
| Research (ML) | 23 | `tests/ml/*` | ✅ |
| Config | 1 | `test_config.py` | ✅ |
| **Total** | **~70+** | **39 files** | ✅ |

**Gaps:**
- No load/stress tests
- No E2E tests (Playwright via frontend, but not asserted in CI)
- No rate-limit tests

## Part 5: Research Gap Analysis

### 5.1 Existing Work (2024-2026)
- **Phish detection on UCI:** Lumint uses 11k+ URL dataset, comparable to published baselines
- **UPI fraud:** No public benchmark dataset exists; Lumint's synthetic generation is defensible
- **Document forensics:** ELA + font consistency is a standard approach (see work by Prasad et al. 2023)

### 5.2 What's Unique About Lumint
1. **Unified fraud intelligence** — UPI + URL + Document + Fraud DNA in one platform
2. **Indian-context features** — PhonePe/GPay/Paytm specific colors, VPA handle detection
3. **AI explanation layer** — Groq LLM with structured XAI outputs
4. **Campaign graph** — Fraud DNA cluster detection across modalities
5. **Production-deployed** — Vercel + Render, not just a notebook

### 5.3 What's NOT Working
1. **UPI model F1=1.0 is memorization** — `ml/train.py:181` evaluates on training set, not held-out
2. **No real UPI screenshot dataset** — 1200 synthetic PNGs only
3. **WebSocket has no rate limit** — could be abused
4. **API key comparison is non-constant-time** — `app/dependencies/auth.py:46`

### 5.4 Required for Publication
1. **Real-data evaluation** — need ≥200 real UPI receipts to claim generalization
2. **Held-out test metrics** — change `ml/train.py:181` to use proper holdout
3. **Adversarial robustness evaluation** — `ml/adversarial/` exists but no results in paper
4. **Inter-rater agreement** — `test_research_agreement.py` exists, results needed

## Part 6: Action Plan

### Fix Now (Critical)
1. **Constant-time API key comparison** (`auth.py:46`) — `hmac.compare_digest()`
2. **Add 10MB limit to document upload** (`documents.py:53`)
3. **WebSocket message size cap** (e.g. 64KB)
4. **Move training evaluation off the training set** (`train.py:181`)

### Fix This Month (Important)
1. Add CSP, X-Frame-Options, HSTS security headers
2. Add rate limiting (slowapi) on `/api/ai/*` (Groq cost)
3. Real UPI screenshot collection pipeline (consent-based)
4. Held-out test set evaluation across all 4 modules

### Fix Before Publication (Required)
1. Cross-dataset evaluation (train on UCI, test on PhishTank — and vice versa)
2. Adversarial robustness table (FGSM, PGD results)
3. SHAP summary plots for all 3 sub-models
4. Confusion matrix at multiple thresholds

### Future Work (Beyond Paper)
1. Online learning (drift detection is plumbed but not enabled)
2. Federated learning across banks (privacy-preserving)
3. Multi-language UPI (Hindi/Tamil/Urdu receipts)
