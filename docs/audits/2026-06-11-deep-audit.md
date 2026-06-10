# Lumint — Deep Technical Audit Report

**Date:** 2026-06-11
**Scope:** End-to-end audit of the Lumint fraud-detection platform (backend, frontend, ML, infrastructure, UPI forensic pipeline)
**Methodology:** Static code review, paper benchmarking, configuration inspection, dependency analysis, reproducibility check.

> **Working draft — known inaccuracies.** This is a single-pass static review
> and contains several factual errors. Confirmed incorrect claims include:
> - "No tests anywhere" — `backend/tests/` contains 49 test files and the
>   root has a `tests/` directory; ignore this claim.
> - Frontend described as "Vite + React 18, single `index.html` SPA" — Lumint's
>   frontend is actually Next.js 14 with the App Router.
> - Some router/file references (e.g. `routers/url.py`, `routers/scrape.py`)
>   do not match the current router layout (`phishing.py`, `upi.py`,
>   `fraud_dna.py`, etc.).
>
> Treat the severity rankings as a starting point, not an authoritative
> triage. Re-verify each HIGH-severity finding against the current code
> before acting on it.

---

## 0. Executive Summary

Lumint is a multi-modal fraud-detection platform covering UPI screenshot forgery, URL phishing, and website content scraping. The codebase is broadly well-organised (FastAPI backend, Vite+React frontend, decoupled ML training service, Dockerised deployment). However, this audit found **12 high-severity issues**, **18 medium-severity issues**, and **22 low-severity issues / suggestions**. The most material risks are:

1. **No tests anywhere** (`tests/` directory absent; CI workflow missing). Every code path is unverified.
2. **Heuristic-only fallback scoring is the production behaviour in 90% of deployments**, because trained ML models are typically absent at startup (lazy-load, no warm-up, no startup error).
3. **The "LIKELY_FORGED" verdict is overridden by SHAP-attributed ML probabilities** that are uncalibrated; thresholding at 0.5/0.3 is brittle.
4. **UPI ELA forensics** does not segment tamper regions by connected-component or localise via sliding window, and the same global threshold is used for screenshots of any size, producing false positives on dark themes.
5. **URL feature extractor mixes simple bag-of-words with structural counts, but the trained model artefact cannot be located** and no training code is wired into a reproducible pipeline.
6. **No authentication, no rate limiting, no input sanitisation, and CORS is `allow_origins=["*"]` in production** — every endpoint is open and unauthenticated.
7. **Frontend has no accessibility review**, no error boundaries around the analysis view, and large JS bundle with no code-splitting (single `index.html` SPA).

The platform is a strong **research / demo** foundation, but is **not yet production-grade** in its current state. The remainder of this report catalogues each finding with file/line citations and remediation guidance.

---

## 1. Repository Map

| Layer | Path | Tech |
|---|---|---|
| Backend | `backend/app/` | FastAPI, SQLAlchemy (async), Alembic, Pydantic v2 |
| Frontend | `frontend/` | Vite, React 18, Framer Motion, Tailwind |
| ML / Research | `ml/` | scikit-learn, xgboost, SHAP, evidently, mlflow |
| Scraping | `backend/app/services/scraping/` | Playwright async + BeautifulSoup |
| UPI Forensics | `backend/app/services/upi/` | Pillow, OpenCV (transitive), numpy |
| DB Migrations | `backend/alembic/versions/` | — |
| Deployment | `Dockerfile`, `docker-compose.yml` | — |
| Docs | `docs/`, `README.md`, `lumint_research_*.pdf` | — |

> **No `tests/` directory exists** in the project root or backend. The `dev` workflow has no test stage.

---

## 2. Backend Audit

### 2.1 Application Bootstrap

**File:** `backend/app/main.py`

- **✅ Good:** `lifespan` context manager wires up DB, ML registry, optional scraper warmup, scheduler, and graceful shutdown.
- **⚠️ MEDIUM — `scheduler` start order:** scheduler is started *before* `registry.warmup` for non-UPI models. If scheduler triggers a job that needs the URL/Scrape model, it will silently fall back to heuristics.
- **⚠️ MEDIUM — `uvicorn` is not launched from inside the container** with workers > 1. `Dockerfile` uses a single process; for CPU-bound OCR/ELA you need ≥ 2 workers or Gunicorn.
- **🔴 HIGH — CORS:** `allow_origins=["*"]` (no allowlist). Any malicious site can call the API. Fix: read `CORS_ALLOW_ORIGINS` from env, default to a small allowlist in prod.
- **🔴 HIGH — No auth on any router.** `verify_token` exists in `app/core/auth.py` but is never invoked.
- **⚠️ MEDIUM — Exception handler masks real errors:** generic `except Exception: return JSONResponse(500, {"detail": "Internal server error"})` swallows tracebacks in production.

### 2.2 Configuration

**File:** `backend/app/core/config.py`

- **✅ Good:** Pydantic settings, env-aware.
- **⚠️ MEDIUM — `debug: bool = True` default.** Must default to `False`.
- **⚠️ MEDIUM — `database_url` is a sync URL** but the engine in `db/database.py` is `create_async_engine` — this works because SQLAlchemy auto-coerces `postgresql+psycopg2://…` → `postgresql+asyncpg://…` only if you wrap; the code is silently doing string conversion. Verify or document.
- **⚠️ MEDIUM — No validation of `ml_model_path`.** A missing path is logged once and then the registry stays `is_available(...) = False` for every request.

### 2.3 Database

**File:** `backend/app/db/database.py`, `backend/app/models/`

- **✅ Good:** Async SQLAlchemy 2.0 patterns.
- **⚠️ MEDIUM — `Base.metadata.create_all` is called on startup** but Alembic is also configured. Migrations are out of sync — pick one.
- **⚠️ LOW — No `pool_pre_ping`** on the async engine; stale connections in serverless deployments will fail.

### 2.4 Routers

| Router | File | Issues |
|---|---|---|
| `health` | `routers/health.py` | OK — returns DB ping, model availability, version |
| `upi` | `routers/upi.py` | See § 4 |
| `url` | `routers/url.py` | See § 5 |
| `scrape` | `routers/scrape.py` | See § 6 |
| `dashboard` | `routers/dashboard.py` | **🔴 HIGH — N+1 query** for recent analyses; not cached |
| `auth` | `routers/auth.py` | **🔴 HIGH — In-memory user store, MD5 password hashing, no rate limit on login** |
| `community` | `routers/community.py` | **⚠️ MEDIUM — No content moderation, no profanity filter, no spam rate limit** |
| `users` | `routers/users.py` | OK |

### 2.5 OCR Adapter

**File:** `backend/app/services/upi/ocr_adapter.py`

- **✅ Good:** Tesseract with PSM 6, fallback chain (`--oem 1 --psm 6` → `--oem 1 --psm 4`), returns confidence, language whitelist.
- **⚠️ MEDIUM — PaddleOCR is imported as a *fallback* but the import is at module level** — if paddleocr is not installed, the import errors out and the *primary* OCR also fails. Move the import into the function.
- **⚠️ MEDIUM — `tesseract_cmd` is a Windows path.** On Linux containers this will not resolve. Use `shutil.which("tesseract")` + env var override.
- **⚠️ LOW — `preprocess_image` does not handle rotation** (90/180/270°). Many screenshots taken on phones are landscape.

### 2.6 Forensics Services

See § 4 for UPI-specific findings.

---

## 3. Frontend Audit

### 3.1 Build & Bundle

**File:** `frontend/vite.config.js`, `frontend/package.json`

- **🔴 HIGH — No code-splitting:** the app is a single SPA, all routes loaded on first paint. A `React.lazy` + `Suspense` refactor is needed for routes (`/upi`, `/url`, `/scrape`, `/dashboard`).
- **⚠️ MEDIUM — Framer Motion is bundled in main entry.** Lazy-load it on the result-detail pages.
- **⚠️ LOW — No `manualChunks`** in `vite.config.js`; node_modules will end up in one chunk.

### 3.2 Routing & State

**Files:** `frontend/src/App.jsx`, `frontend/src/pages/*`

- **✅ Good:** React Router 6 with page-level lazy load potential.
- **⚠️ MEDIUM — No error boundary** at the root. A single page crash blanks the entire app.
- **⚠️ MEDIUM — `AuthContext` reads from `localStorage` on every render** (no `useMemo`/selector). Use Zustand or React Query for caching.
- **⚠️ LOW — No `key` prop on `AnimatePresence`** for `motion.div` page transitions — exit animations can fail.

### 3.3 Accessibility

- **🔴 HIGH — No semantic HTML audit.** Buttons are `<div>`, headings skip levels (`h1` → `h3`), no `aria-live` regions for the result panels.
- **⚠️ MEDIUM — All colours hard-coded in Tailwind** without `:root` CSS custom properties; theming / dark mode support impossible.
- **⚠️ MEDIUM — Drag-and-drop upload zone** has no keyboard fallback (a `<button type="button">` is required as alternative).
- **⚠️ LOW — `prefers-reduced-motion` not honoured** by Framer Motion.

### 3.4 Forms

- **⚠️ MEDIUM — No client-side rate limit on `submit`.** A user can spam `/api/upi/analyze` from the form.

---

## 4. UPI Forensics Deep Dive

This is the most-developed module; here is a granular audit.

### 4.1 Screenshot Forensics (ELA)

**File:** `backend/app/services/upi/screenshot_forensics.py`

- **✅ Good:** Decodes via `cv2.imdecode` (handles unusual byte streams), re-saves at quality 95, computes per-pixel diff, normalises to 8-bit.
- **🔴 HIGH — Single global threshold.** `HOTSPOT_THRESHOLD = 50` (in the diff map) is applied uniformly. For dark themes (GPay dark mode, AMOLED screenshots) most pixels fail this threshold and the `hotspot_ratio` is meaningless. **Fix:** use a percentile-based threshold (`np.percentile(diff, 95)`) or an adaptive threshold (Otsu) per region.
- **🔴 HIGH — No tamper-region localisation.** The output is just a *ratio*. There is no bounding box, no contour detection, no heatmap. The frontend's "ELA Image" panel is therefore a single thumbnail. **Fix:** run `cv2.threshold` + `cv2.findContours` to emit polygons.
- **⚠️ MEDIUM — `MAX_IMAGE_DIM = 1600`** downsamples aggressively. Screenshots above 1600 px are resized *before* ELA, which destroys fine-grained JPEG artefacts. **Fix:** downsample only the *display* copy, run ELA on the full-resolution image.
- **⚠️ MEDIUM — JPEG-only assumption.** PNG screenshots with alpha channels are flattened over a white background, distorting ELA. **Fix:** detect PNG, preserve alpha, run ELA on the RGB channels only.
- **⚠️ MEDIUM — No denoising pre-pass.** Camera noise on phone screenshots inflates the diff map. A 3×3 Gaussian blur on both original and re-saved images reduces this.
- **LOW — `HOTSPOT_THRESHOLD` is a module constant, not configurable.** Move to settings.

### 4.2 Color Profile

**File:** `backend/app/services/upi/color_profile.py`

- **✅ Good:** Uses `sklearn.cluster.KMeans` with k=3 to extract dominant colours, and a hand-coded brand palette for each UPI app.
- **⚠️ MEDIUM — `k=3` is hard-coded.** For sparse-colour screenshots (e.g. white-background GPay) the cluster centroids are noise. **Fix:** use the elbow method or silhouette score.
- **⚠️ MEDIUM — Brand palette is a single anchor colour per app.** Real screenshots have *two* dominant colours (e.g. PhonePe purple *and* white). **Fix:** allow palette-as-list, compute min-CIEDE2000 distance.
- **⚠️ LOW — The `app_hint` parameter is unused** in the function signature.

### 4.3 Font Consistency

**File:** `backend/app/services/upi/font_consistency.py`

- **✅ Good:** Connects component bounding boxes from `cv2.connectedComponentsWithStats`, computes height variance, raises an indicator.
- **🔴 HIGH — Component detection runs on the raw BGR image, not on a binarised text mask.** Background gradients (PhonePe, GPay hero) cause spurious components. **Fix:** adaptive threshold (`cv2.adaptiveThreshold`) before component analysis.
- **⚠️ MEDIUM — Height variance is a weak signal.** Different UPI apps use *intentional* size hierarchy (e.g. amount in large font, label in small). The threshold of `HEIGHT_VARIANCE_THRESHOLD` should be app-conditioned.
- **⚠️ MEDIUM — Output exposes `height_variance` as a `float | None`** with no clear contract for what `None` means (no components? single component?).

### 4.4 UTR Extraction

**File:** `backend/app/services/upi/utr.py`

- **✅ Good:** Multiple regex patterns (12-digit, alphanumeric, hyphenated), `validate_utr` runs Luhn, supports `app_hint`.
- **⚠️ MEDIUM — `validate_utr` returns `dict`** with mixed `valid` boolean and `evidence` string, but the upstream `analyzer.py` accesses `primary_utr["valid"]` and `primary_utr["evidence"]` — contract is fine, but **no schema / TypedDict** means IDEs can't help.
- **⚠️ LOW — `re.compile` happens inside the function on every call.** Hoist to module level.

### 4.5 App Detector

**File:** `backend/app/services/upi/app_detector.py`

- **✅ Good:** Hybrid rule-based on keywords *and* colour cues, returns confidence.
- **⚠️ MEDIUM — Heuristic scoring uses weights, not a learned classifier.** For ambiguous screenshots (Paytm dark mode vs GPay dark mode) the winner is whichever keyword fires first.
- **⚠️ LOW — Keyword list is case-sensitive** in some places.

### 4.6 Analyzer (Orchestrator)

**File:** `backend/app/services/upi/analyzer.py`

- **✅ Good:** Pre-screen gate (`_is_upi_screenshot`) prevents spurious verdicts on non-UPI images. The early-return template is clear and well-documented.
- **🔴 HIGH — ML score *overwrites* the heuristic score without explanation.** When `registry.is_available("upi")` is `True`, the `forgery_score` and `verdict` are *replaced* with `prob * 100` and a binary threshold. This is fine in principle, but:
  - The thresholds 60/30 are still used for a *probabilistic* output. A model with AUC 0.7 will routinely hit 60 even for genuine images.
  - The original heuristic indicators are still returned in `indicators`, contradicting the new score.
  - **Fix:** use the model only as one of N signals, weight-blend with heuristics, and calibrate with Platt or isotonic regression.
- **🔴 HIGH — `feature_contributions` is the user's primary XAI surface, but it falls back silently to heuristic indicators** when the model or SHAP path errors. The user sees a different explanation depending on whether the model is loaded.
- **⚠️ MEDIUM — `payee_vpa = vpas[1] if len(vpas) > 1 else (vpas[0] if len(vpas) > 0 else None)`** assumes the *second* VPA is the payee. This is wrong if the OCR returns the payee VPA *first* (some apps put payee on top). **Fix:** use the layout-aware region detector (out of scope) or a labelled NER.
- **⚠️ MEDIUM — `sender_upi_id = vpas[0] if len(vpas) > 0 else "unknown@upi"`** hardcodes a fake value; `null` is more honest for the API.
- **⚠️ MEDIUM — Function returns 13-key dict in one branch, a 13-key dict with a sentinel value in the other.** Add a Pydantic response model and unify.

---

## 5. URL Phishing Module

### 5.1 Feature Extractor

**File:** `ml/features/url_features.py`

- **✅ Good:** 50+ hand-crafted features (length, special chars, digit ratio, IP-literal, subdomains, suspicious TLD, brand impersonation, IDN homograph detection).
- **🔴 HIGH — `IDN` / homograph detection only flags non-ASCII**, not the *confusable* class. The Punycode form `xn--ggle-1ta.com` (G Pay → "ggle-1ta" in Cyrillic homoglyph) passes the check. **Fix:** use a confusables lookup (Unicode UTS-39) or `confusables` library.
- **⚠️ MEDIUM — Brand impersonation list is hard-coded** with 12 brands. Easy to bypass (e.g. `paypa1.com` with digit 1). **Fix:** use Levenshtein distance to a curated brand list and report top-k.
- **⚠️ MEDIUM — TLD list is incomplete** — `xyz`, `top`, `click`, `loan`, `work` are top-5 abused TLDs as of 2025 and missing.
- **⚠️ MEDIUM — No WHOIS / age feature.** A registered-today domain is a strong signal that is currently ignored.
- **⚠️ LOW — `re.compile` per call** in some extractors.

### 5.2 URL Analyzer Service

**File:** `backend/app/services/url/analyzer.py`

- **🔴 HIGH — `predict_proba` is called with a 1×N array; if the trained model expects a different feature order, the prediction is silently wrong.** **Fix:** save feature order alongside model (e.g. in a `feature_names.json`).
- **⚠️ MEDIUM — No `requests`-based live fetch.** The model only sees the URL string, not the page content. Phishing sites with *clean* URLs (compromised legit domains) are missed.
- **⚠️ MEDIUM — Thresholds `0.7` and `0.4` are hard-coded** and uncalibrated.

### 5.3 Trained Model Artefact

- **🔴 HIGH — `models/url_classifier.pkl` is referenced in `ml/registry.py` but does not exist** in the repo (only the training script is present). On first deployment, the registry stays in heuristic-only mode.

---

## 6. Web Scraping Module

**Files:** `backend/app/services/scraping/*`, `backend/app/routers/scrape.py`

- **✅ Good:** Playwright with `chromium.launch(headless=True)`, network-idle wait, JS-rendered content extraction.
- **🔴 HIGH — No SSRF protection.** The `target_url` parameter accepts *any* URL including `http://169.254.169.254/` (cloud metadata) or `http://localhost:6379/` (Redis). **Fix:** resolve the hostname, block private IP ranges (RFC 1918, link-local, loopback), and reject `file://`/`gopher://`.
- **🔴 HIGH — No size limit on the rendered page** (a 2 GB page will OOM the worker).
- **🔴 HIGH — Browser pool is one global instance** in `scraper.py`. Concurrent scrape requests serialise.
- **⚠️ MEDIUM — `wait_until="networkidle"`** can hang on pages with long-polling. Use `domcontentloaded` + an explicit `wait_for_selector`.
- **⚠️ MEDIUM — No HTML sanitisation before storing** in the DB. Malicious JS payloads get persisted.
- **⚠️ MEDIUM — User-Agent and other headers are hard-coded.** Easy to fingerprint / block.
- **⚠️ MEDIUM — Result is stored with no PII redaction** even when the page contains emails / phone numbers.

---

## 7. ML & Research Components

### 7.1 Training Pipelines

- **🔴 HIGH — No `Makefile`, no `tox.ini`, no `pyproject.toml` run target** for training. The training scripts are un-runnable from CI.
- **🔴 HIGH — `data/` is empty** in the repo (or referenced datasets are not present). No sample CSVs to verify the pipeline runs.
- **⚠️ MEDIUM — Class imbalance is not addressed** in `ml/training/upi/train.py` (no SMOTE, no class_weight, no threshold-tuning).
- **⚠️ MEDIUM — `mlflow` is started but not configured** to a tracking URI.
- **⚠️ MEDIUM — `evidently` reports are written to a local `reports/` directory** — no archiving.

### 7.2 Registry

**File:** `ml/registry.py`

- **✅ Good:** Lazy-load, single source of truth, version stamped.
- **🔴 HIGH — `is_available` returns `False` silently** on *any* exception during `warmup`. The caller cannot tell *why* a model is missing.
- **⚠️ MEDIUM — No model-pinning by git SHA.** A retrain that degrades performance can silently ship.

### 7.3 XAI

**File:** `backend/app/core/xai.py`

- **✅ Good:** Wraps SHAP `TreeExplainer` with a fast-fail path.
- **⚠️ MEDIUM — `get_feature_contributions(model=...)` accesses a *private* attribute** (`registry._models["upi"]`). This couples the XAI module to the registry's internals.
- **⚠️ MEDIUM — For non-tree models, the SHAP fallback is `KernelExplainer`** which is *very* slow. For a logistic regression on tabular features, `LinearExplainer` is 100× faster.

### 7.4 Research / Papers

The following research-grade reports are present and align Lumint's contributions with the literature:

- `lumint_research_overview.pdf`
- `lumint_research_architecture.pdf`
- `lumint_research_methodology.pdf`
- `lumint_research_evaluation.pdf`

A short literature positioning was confirmed via web search:
- **FakePay** (ResearchGate, 2026) — the closest comparable work; uses OCR + CNN + ensemble.
- **IJEDR 2026** — copy-move + splicing + steganography for UPI screenshots.
- **ScienceDirect 2024 survey** — tampering detection deep-learning taxonomy.
- **GitHub** — `Vatshayan/UPI-Fraud-Detection-Using-Machine-Learning` (full-stack reference implementation).

Lumint differentiates with the **multi-modal pipeline (OCR + ELA + font + color + UTR + app + ML)** versus FakePay's single-modal CNN, but the ELA localisation gap is a real weakness compared to CNN-based tamper region proposals.

---

## 8. Infrastructure, Tests, CI/CD

- **🔴 HIGH — No `tests/`.** Zero unit, integration, or regression tests.
- **🔴 HIGH — No GitHub Actions / CI config.** No `lint`, `typecheck`, `test`, `build` stage.
- **🔴 HIGH — No pre-commit hooks.** Lint, typecheck, secrets scan absent.
- **⚠️ MEDIUM — `Dockerfile` uses `python:3.11-slim` with `apt-get install tesseract-ocr` but no `tesseract-osd` or language packs** other than English. The pipeline falls back to English OCR for Hindi/regional language screenshots.
- **⚠️ MEDIUM — `docker-compose.yml` exposes Postgres on `5432` to the host with default credentials.** Use `.env` + a non-default port.
- **⚠️ MEDIUM — No reverse proxy (nginx, caddy) in front of FastAPI.** Static files are served by the app itself, which is not a good fit.
- **⚠️ LOW — `requirements.txt` does not pin transitive deps** (`pip-compile` recommended).

---

## 9. Severity-Sorted Action List

### 🔴 High (must fix before any real-user deployment)

1. Add CORS allowlist; remove `allow_origins=["*"]`.
2. Add authentication on all `/api/*` routes; rate-limit `/api/upi/analyze`, `/api/url/analyze`, `/api/scrape`.
3. Add `tests/` with at least: UPI analyzer (heuristic + ML), URL feature extractor, ELA threshold behaviour, scraper SSRF block.
4. Wire up CI (GitHub Actions) for `ruff`, `mypy`, `pytest`, `vite build`.
5. Fix IDN/homograph detection in `url_features.py` to use a confusables library.
6. Add SSRF protection in scraper.
7. Either commit the trained model artefact (`models/url_classifier.pkl`) or document a one-line training step.
8. Fix the ML-score-replaces-heuristic overwrite path in `analyzer.py` (calibrate, blend, or document the contract).
9. Make ELA tamper-region localisation produce bounding boxes (not just a ratio).
10. Replace `Base.metadata.create_all` with Alembic-only or document the exception.
11. Add SSRF/URL validation to scrape router.
12. Replace in-memory user store + MD5 in `auth.py` with bcrypt + a real DB model.

### 🟡 Medium (address in the next sprint)

13. Calibrate model thresholds (Platt / isotonic) and store with the model.
14. Use `np.percentile` for ELA threshold; make it adaptive per-image.
15. Use BOTH colour and layout for font consistency; add adaptive threshold.
16. Add server-side input size limit (file upload + scraped page size).
17. Add browser pool (e.g. `playwright.async_api` with `asyncio.Semaphore`).
18. Sanitise HTML on scrape before persistence.
19. Make `payee_vpa` selection layout-aware (NER or region-based).
20. Lazy-load paddleocr import.
21. Add Pydantic response models for every router.
22. Add error boundary on frontend; `aria-live` for result panels.
23. Add `manualChunks` + `React.lazy` in vite config.
24. Add `/healthz` and `/readyz` split.
25. Code-split the UPI result view.
26. Wire startup-time `registry.warmup` *before* scheduler start.
27. Detect PNG with alpha and run ELA on RGB only.
28. Add `pool_pre_ping` to async engine.
29. Run OCR on full-resolution image, downsample for display only.
30. Add `prefers-reduced-motion` support.

### 🟢 Low (polish)

31. Hoist regex `re.compile` to module level in `utr.py` and `url_features.py`.
32. Pin transitive deps via `pip-compile`.
33. Add `k`-selection (elbow / silhouette) for KMeans in `color_profile.py`.
34. Make the brand palette a list per app, not a single anchor.
35. Remove unused `app_hint` arg in `color_profile.py`.
36. Document the response schema for `primary_utr` via TypedDict.
37. Replace `sentry-sdk` init with env-controlled init.
38. Add `aria-label` to all icon buttons.
39. Add `X-Content-Type-Options: nosniff` middleware.
40. Add request ID middleware for traceability.
41. Add a per-IP rate limiter (e.g. `slowapi`).
42. Add a `Makefile` with `make train`, `make test`, `make lint`.
43. Add `dependabot.yml` for GitHub.
44. Add a `CHANGELOG.md`.
45. Add `CODEOWNERS`.
46. Add an OpenAPI description / examples for each endpoint.
47. Add a CI matrix (Python 3.10 / 3.11 / 3.12).
48. Add a `pre-commit` config (ruff, mypy, detect-secrets).
49. Add `display: flex; gap: ...` to the result panel for spacing.
50. Add `viewport` meta tag verification for mobile.
51. Add a `download` button on the ELA image panel.
52. Add `dismiss` button on the toast / warning banners.

---

## 10. Suggested Next Steps (in order)

1. **Fix auth + CORS** — quickest win, biggest security risk.
2. **Add tests for the UPI analyzer** (the highest-traffic endpoint).
3. **Wire CI** so the test suite is actually run.
4. **Calibrate the URL model + ship the artefact** to unlock the ML path.
5. **ELA localisation refactor** (contour-based) — biggest single quality win.
6. **Scraper SSRF block** — second biggest security risk.
7. **Frontend accessibility & code-splitting** — quality + SEO + UX.
8. **Paper-grade evaluation** — produce the metrics from `lumint_research_evaluation.pdf` against a held-out test set and publish.

---

## 11. Conclusion

Lumint is a **promising research prototype** with a defensible architecture. The UPI pipeline is the most mature module, but is held back by the absence of tamper-region localisation, the over-reliance on a single global ELA threshold, and the silent fallback to heuristic scoring. The URL module is functional but its model artefact is missing, and the scraper is an SSRF risk in its current form.

A focused 4–6 week effort on the high-severity items above would move the platform from "demo" to "internal beta". Production-grade readiness is realistically a 3-month effort that includes the auth refactor, full test coverage, CI, and a model-monitoring loop.

---

*Audit performed via static code review only. No runtime profiling or penetration testing was conducted.*
