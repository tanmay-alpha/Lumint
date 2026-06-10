# Lumint — Deep Codebase Analysis

A comprehensive, opinionated review of the **Lumint** project at `C:\Users\TANMAY\OneDrive\Desktop\Lumint` as of 2026-06-11. This covers purpose, architecture, code quality, scientific rigor, gaps, and concrete recommendations.

> **Working draft.** This is a single-pass analysis. Several of the criticisms
> (e.g. "tests cover the easy ground" in §4.8) deserve to be checked against the
> current `backend/tests/` test count (49 files) and the more recent research
> artifacts in `backend/reports/` before any of the recommendations are acted
> on. Treat it as one engineer's notes, not a final audit verdict.

---

## 1. What Lumint Actually Is

Lumint is a **multi-modal fraud-detection platform** specifically aimed at the Indian digital-payments threat surface. It accepts three evidence types and fuses them into a single explainable risk verdict:

- **PhishShield** — phishing URL analyzer (lexical heuristics + TF-IDF character n-grams + ML classifier).
- **DocShield** — KYC document forensics (Error Level Analysis, EXIF/metadata inspection, font/layout audit).
- **UPI Shield** — UPI receipt screenshot verification (OCR → app detection → UTR validation → font/color/ELA forensics → ML scoring).

On top of those three detectors it layers:

- **Cross-modal Fusion** — heuristic weighted score *or* a trained Logistic-Regression meta-learner that consumes `[phish_prob, doc_prob, upi_prob]`.
- **Fraud DNA** — DBSCAN clustering of structural fingerprints plus cosine-similarity graph (nodes = events, edges = similar fingerprints) for campaign attribution.
- **Explorable XAI** — SHAP values with a graceful heuristic fallback when SHAP is unavailable or fails.
- **AI Analyst Agent** — a ReAct-style autonomous investigator that calls `check_url`, `check_upi_receipt`, `search_database_cases`, and `check_kyc_document` tools, returning a structured diagnostic brief.
- **Live Threat Stream** — WebSocket broadcast of events as they enter the system.
- **Next.js Dashboard** — premium glassmorphism UI for fraud analysts with 8 routes (dashboard, docshield, phishshield, upi-shield, fraud-dna, events, activity, research, settings).
- **HuggingFace Space** — a stand-alone Gradio demo of the CMFA UPI detector that loads `tanmay-alpha/lumint-cmfa-upi-detector` from the Hub (with heuristic fallback).

The repo markets itself as both a **production fraud intelligence platform** and a **publication-grade research artifact** for an arXiv paper.

---

## 2. Repository Structure

```
Lumint/
├── backend/                  FastAPI app
│   ├── ai/                   Groq client + per-shield AI briefs + ReAct agent
│   ├── app/
│   │   ├── core/             fusion.py, xai.py, event_publisher.py
│   │   ├── database.py       SQLAlchemy engine + SessionLocal
│   │   ├── models/           ORM models (UPI event, Case, ThreatFeedAlert)
│   │   ├── routers/          13 FastAPI routers
│   │   ├── schemas/          Pydantic request/response models
│   │   └── services/         Domain logic (phishshield, docshield, upi, fraud_dna, dashboard)
│   ├── data/                 Dataset CSVs + real-data downloader
│   ├── ml/                   ML research & training
│   │   ├── ablation/         Feature, module, SMOTE, SHAP ablations
│   │   ├── adversarial/      FGSM (tabular) + HopSkipJump
│   │   ├── baselines/        FakePay baseline + comparison runner
│   │   ├── drift/            ADWIN + Page-Hinkley + DDM ensemble
│   │   ├── experiments/      Cross-dataset / real-data runners
│   │   ├── features/         Lexical / doc / UPI feature extractors
│   │   ├── figures/          Paper figure generator
│   │   ├── llm/              LoRA fine-tuning + local Phi-3.5 inference
│   │   ├── stats/            McNemar, DeLong, bootstrap CI
│   │   ├── vlm/              Optional vision-language model helpers
│   │   ├── registry.py       Singleton .joblib model registry with heuristic fallback
│   │   └── train.py          Unified 5-model training pipeline
│   ├── research/             Research harness (runners, manifests, paper tables, consensus)
│   ├── reports/              R9–R16 JSON + Markdown tables
│   ├── scripts/              Seed, ablation runner, paper bundle builder
│   ├── tests/                49 test files (pytest)
│   ├── main.py               Uvicorn wrapper for `app.main:app`
│   └── requirements.txt
├── frontend/                 Next.js 16 + React 19 + Tailwind 4 dashboard
├── hf_space/app.py           Stand-alone Gradio demo
├── paper/                    LaTeX + Markdown source for the research paper
├── docs/                     Research roadmap, threat model, evaluation protocol
├── dataset/                  UPI-FraudBench generator + 1,200 synthetic UPI screenshots
├── tests/                    Repository-level test (dataset generator)
├── .github/workflows/        CI (pytest) + Gitleaks secret-scan
├── reproduce.sh              End-to-end reproduction script
├── vercel.json               Vercel deploy config
└── *.md                      README, AGENTS, DEMO, REPRODUCE, CITE, DATASETS, etc.
```

Scale: **202 Python modules**, **59 TS/TSX files**, **11 trained .joblib artifacts**, **8 Markdown reports + 13 JSON research artifacts**, **49 test files**.

---

## 3. Architectural Strengths

### 3.1 Clean separation of concerns
The backend is well factored: routers handle HTTP shape, services hold domain logic, `ml/registry.py` wraps the trained models with heuristic fallback, and `app/core/fusion.py` + `xai.py` provide shared cross-cutting concerns. New shields can be added by dropping a service module and a router without touching the others.

### 3.2 Defense-in-depth at the boundary
The `ModelRegistry` is the textbook example here. It loads each `.joblib` (model, scaler, optional TF-IDF, metrics, feature names) at import time, exposes `is_available` / `predict_proba` / `get_feature_importances`, and quietly falls back to heuristic scoring if anything is missing. Combined with the `validate_database_url` and `validate_production_db` validators in `app/config.py`, the system refuses to start in obviously broken states.

### 3.3 Rich, opinionated research layer
- **Drift detection** runs ADWIN + Page-Hinkley + DDM in parallel with majority voting and a 200-sample active window (`ml/drift/monitor.py`).
- **Adversarial suite** implements a tabular FGSM (with per-feature epsilon scaling) and a black-box HopSkipJump attack via ART (`ml/adversarial/attacks.py`).
- **Statistical rigor** goes beyond simple train/test: `McNemar` with mid-p exact correction for n<25, `DeLong` for AUC variance, bootstrap CIs, all behind a unified `ml/stats` package.
- **Cross-dataset evaluation** in `ml/experiments/run_real_data.py` honestly reports the synthetic→real F1 drop from 1.0000 to 0.6439 rather than hiding it.

### 3.4 Honest UPI gate
`analyze_upi_screenshot` runs `_is_upi_screenshot` *before* the expensive pipeline, so memes, selfies, or LinkedIn screenshots are flagged `NOT_UPI_SCREENSHOT` with a 95 forgery score instead of producing garbage indicators. That single change probably kills 80% of the false positives that would otherwise plague an UPI detector.

### 3.5 XAI that's actually used
`get_feature_contributions` first attempts SHAP, falls back to `feature_importances_`/`coef_`, then to rule-based indicator aggregation, and only returns an empty list if everything fails. The endpoint contract is stable across the three paths, which is the right call for a UI that has to render bars no matter what.

### 3.6 WebSocket live threat stream
`app/routers/stream_router.py` plus `app/core/event_publisher.py` keep a persistent in-process broadcaster for threat events. The frontend `useThreatStream` hook consumes them and the activity page reflects new threats in real time.

### 3.7 Verifiable reproduction
`reproduce.sh` (11 steps) plus `REPRODUCE.md` document a deterministic path to all R9–R16 paper tables. Random seeds are pinned at 42 across training, evaluation, drift simulation, and adversarial generation. The same script is referenced from `DEMO.md`, `REPRODUCE.md`, and the paper outline.

---

## 4. Architectural Weaknesses & Risks

### 4.1 Synthetic-data performance is suspiciously perfect
Every model in `r9_model_comparison_table.md` reports F1 = AUC = MCC = **1.0000** with zero-variance CIs. The SMOTE ablation shows recall of 0.78 → 0.98 → 0.99, but the *combined* feature group lands on 1.0000 every time. This is a strong signal that the synthetic datasets have features that are linearly separable from their labels (the generator probably bakes the label into a feature). For a research paper, this is a problem:

- McNemar and DeLong come back with p=1.0 and "not significantly different" because there is no signal to compare.
- A reviewer will spot the 1.0000 row immediately. R12 only partially rescues this by reporting synthetic→real F1=0.6439.

**Fix:** add realistic noise / overlap to the synthetic generators, or use them only as smoke tests and lead with the R12 cross-dataset numbers.

### 4.2 Adversarial results are too clean
`r16_adversarial_table.md` shows ASR = 0.0000 across PhishShield, DocShield, *and* UPI for both FGSM and HopSkipJump, with no F1 cost. Combined with 1.0000 clean F1, this reads as "untestable inputs." The FGSM generator limits perturbations to ~3 lexical features for phishing (out of 2,025), so attackers can only nudge a small subspace, which guarantees the attack fails. For UPI, FGSM even "succeeds" with ASR=1.0 for HopSkipJump, but the defense brings it back to 0.0 — there is no ablation showing what changed.

**Fix:** report per-feature-class ASR, add a worst-case bound, and use a *defended* model as the actual benchmark.

### 4.3 Drift detection is ungrounded in production signal
`ml/drift/monitor.py` is correct academically but its input (`update(y_true, y_pred)`) requires a labeled ground-truth stream. In production Lumint has only predictions and downstream feedback. The `last_drift_at`, `delta`, and `error_rate_*` fields are meaningful only when there is a feedback channel — and there is no evidence in the code that feedback flows back into the monitor. Without that plumbing, "recommended_action: retrain" is theatre.

**Fix:** either (a) wire the monitor to the events router and gate it behind a `feedback` flag, or (b) drop the recommendation claim from the API response.

### 4.4 Fusion is a 3-feature meta-learner trained on synthetic data
`fusion_meta.joblib` was trained on 2,000 hand-crafted `[phish_prob, doc_prob, upi_prob]` vectors. The coefficients are exported as `phish=3.30, doc=3.00, upi=2.99`, which suspiciously matches the heuristic weights `(0.35, 0.35, 0.30)`. The ablation table (`r11_ablation_tables.md`) is the only one with realistic numbers: full system F1=0.8853, dropping any single shield costs ~0.02–0.03, single-shield drops to ~0.77.

**Fix:** either train the meta-learner on real (or at least more diverse synthetic) data, or document explicitly that the meta-learner is illustrative and the heuristic fallback is the production default.

### 4.5 The ReAct agent is shallow
`backend/ai/agent.py` parses `Action: tool_name(arg)` with a regex, runs at most 4 steps, and falls back to "Investigation timeout" with no reflection. Tools are mostly stubs (`check_upi_receipt` only checks UTR length). The Groq call uses `MODEL_ID` with a 12-second timeout but no JSON-mode for the action parsing, so it can return anything and the agent will try to parse it.

**Fix:** add a Pydantic-validated action schema, increase to ~6 steps with explicit self-critique, and either enrich the tools or make the agent stop early with a clearer answer.

### 4.6 Security and config hygiene
- `.env` is **committed** to the repo (present in `git status` as modified but tracked). The keys are redacted above, but the file is on disk. Combined with `gitleaks` CI, this is a layered defense; still, `.gitignore` should be enforcing `.env` exclusion (and `git rm --cached .env` is overdue).
- `ALLOWED_ORIGINS` includes a regex `https://.*\.vercel\.app` which is convenient but lets any Vercel preview impersonate your origin. For a security product this is worth tightening.
- The database path is dynamically rewritten depending on cwd (`./backend/data/` vs `./data/`). That's clever, but it's a latent footgun — anyone running tests from the wrong directory will silently use a different DB.

### 4.7 Frontend bundle and runtime risk
- The Next.js 16 + React 19 + Tailwind 4 stack is bleeding-edge (released late 2025). The lockfile and `optionalDependencies` (lightningcss, oxide, swc) suggest a cross-platform build that won't work everywhere. The `npm install` step on a fresh Windows machine will pull a *lot*.
- `recharts ^3.8.1` and `framer-motion ^12.40.0` are heavy; there's no bundle-size budget enforced.
- The layout uses `localStorage` to set the theme via a `dangerouslySetInnerHTML` script in `<head>`. This is fine for SSR-avoidance but blocks adoption in environments where `localStorage` is unavailable (some embedded browsers).

### 4.8 Tests cover the easy ground
49 test files is a lot, but the heavy ones are infrastructure (`test_config`, `test_health`, `test_dashboard`) and there's no e2e test that drives a full analyze→fuse→xai flow with real (or real-looking) artifacts. Adversarial, drift, and ablations have unit tests but not "the numbers are non-trivial" tests. A regression that quietly flips a 0.8853 F1 to 0.6 would not be caught by CI.

**Fix:** add a smoke test that ingests the demo fixtures (`tests/fixtures/tampered_kyc.jpg`, `fake_receipt.png`) and asserts expected verdict bands. Pin a small set of R9 numbers as guardrails.

---

## 5. Scientific & Publication Assessment

| Dimension | Verdict | Notes |
|---|---|---|
| **Statistical validity** | Excellent in code, weak in story | McNemar, DeLong, bootstrap are all correct; but the synthetic data makes the tests vacuous (p=1.0 everywhere). |
| **XAI** | Very good | Real SHAP + importance + heuristic fallback. Output shape is stable. |
| **Robustness & generalization** | Honest | R12 cross-dataset and real-data runs are present and the F1 drop is reported truthfully. |
| **Drift monitoring** | Advanced code, weak integration | The detector is right, but the production feedback loop is missing. |
| **Local LLM / LoRA** | Stated, not exercised | `ml/llm/train_lora.py` and `local_inference.py` exist but the run logs and `MODEL_CARD` make no claim of an actually-finetuned model being shipped. |
| **Reproducibility** | Excellent | `reproduce.sh` is deterministic, seeds are pinned, all reports are regenerated. |
| **Real-world generalization** | Mixed | Synthetic-only = 1.0000. Real-data = 0.84. The 0.16 gap is the most important number in the project and deserves a section of its own. |
| **Adversarial robustness** | Claimed but not stress-tested | ASR=0.0000 with a constrained FGSM is not a robustness claim a security venue will accept. |

The `RESEARCH_LEVEL_AUDIT.md` verdict ("Advanced Research Level / Publication Ready") is correct in code quality but premature in claims. To get into a top venue, the project needs (1) realistic noise in the synthetic data, (2) per-feature adversarial ablations, (3) a deployed LLM card with eval numbers, and (4) a real-world deployment or partner dataset with permission to publish.

---

## 6. Code Quality Audit

| Area | Status |
|---|---|
| **Imports** | Clean. No circulars. `ml/registry.py` is correctly lazy-imported in services to keep import cost down. |
| **Logging** | Logger per module with `lumint.*` namespaces. No `print()` left in `app/`. |
| **Error handling** | Defensive. Fusion, UPI analyzer, OCR adapter all use try/except + heuristic fallback. |
| **Type hints** | Strong in Pydantic schemas; weaker in ML scripts (NumPy types leak). |
| **Pydantic v2** | Used correctly. `model_validator(mode="after")` and `field_validator` are idiomatic. |
| **Test coverage** | Wide breadth, shallow on adversarial/drift integration. 49 test files, but the test count per file is small. |
| **Dead/unused code** | `backend/ai/__init__.py`, `app/services/dashboard/stats.py`, some `vlm/` modules look lightly used. Worth a sweep. |
| **Dependency hygiene** | `bitsandbytes`, `peft`, `trl`, `transformers`, `art`, `menelaus`, `river` are heavy; verify they are actually required at runtime vs. only by training scripts. |
| **Secrets in repo** | `.env` is tracked. `gitleaks` CI is the only thing protecting the keys. |
| **Reproducibility** | 100% via `reproduce.sh`. |

---

## 7. Specific Files Worth a Closer Look

| File | Why it matters |
|---|---|
| `backend/app/core/fusion.py` | The whole point of Lumint. Treats missing scores gracefully, supports both heuristic and ML fusion, and surfaces correlation flags. Worth a unit test for every combination. |
| `backend/app/core/xai.py` | Implements a 3-tier fallback (SHAP → importance → heuristic). The contract is stable; that's the hard part. |
| `backend/ml/registry.py` | Singleton loading of all `.joblib` artifacts with graceful failure. The pattern you'd want in any production ML service. |
| `backend/app/services/upi/analyzer.py` | The clearest end-to-end pipeline: gate → OCR → app detect → UTR → ELA → font → color → heuristic → ML → XAI. Read this first to understand the design philosophy. |
| `backend/app/services/fraud_dna/clusterer.py` | DBSCAN over a precomputed TF-IDF similarity matrix. Campaign IDs are MD5 over sorted event IDs, which is deterministic and cheap. |
| `backend/ai/agent.py` | ReAct loop. Works, but the tools are stubs and the parser is regex-fragile. |
| `backend/ml/drift/monitor.py` | Textbook ensemble of three drift detectors with majority vote. The 200-sample active window is a sensible choice. |
| `hf_space/app.py` | The whole CMFA pipeline in 200 lines: 3 features + heuristic ML + Gradio. Great minimal demonstration. |
| `frontend/app/layout.tsx` | Theme bootstrap via `dangerouslySetInnerHTML`; works, but consider `next-themes` for production. |
| `backend/reports/r11_ablation_tables.md` | The only table with believable, non-saturated numbers. Lead the paper with it. |

---

## 8. Concrete Recommendations (Prioritized)

### High-impact, low-effort
1. **Drop `.env` from the index.** Run `git rm --cached .env`, add `.env` to `.gitignore`, then rotate any key that has ever been pushed. The CI gitleaks scan is a backstop, not a substitute.
2. **Replace 1.0000-everywhere tables** with the cross-dataset R12 numbers in the README and paper front matter. The 0.16 F1 gap is the most interesting story.
3. **Add a real-data smoke test** that hits `phish/analyze`, `upi/analyze`, and `fusion/analyze` with a handful of demo fixtures and asserts verdict bands. This is the only test that will catch regressions that matter.
4. **Document the GROQ fallback path** at the top of `ai/agent.py` and `ai/client.py`. Heuristic-only is a perfectly valid deployment mode and should be advertised as a feature.
5. **Pin a Next.js lockfile** with `npm ci` in CI. The current `package.json` uses `^` ranges for `next`, `react`, and `tailwindcss`, which means a `npm install` a year from now could pull breaking changes.

### Medium-impact, medium-effort
6. **Train `fusion_meta` on real outputs.** Generate predictions from the real-data split and re-fit the meta-learner. Report the new F1.
7. **Wire drift monitoring to the events stream.** Even a synthetic feedback loop in the test suite would make the `recommended_action` field defensible.
8. **Strengthen the adversarial evaluation.** Attack each feature group separately, report per-group ASR, and add a "hardened" baseline trained with adversarial examples.
9. **Add noise to the synthetic generators.** If a logistic regression can hit 1.0000 F1, the labels are not realistic. Drop the gap to 0.95–0.98 with a noise term, and re-run all R9–R11 tables.
10. **Enrich the agent's tools** with the actual UPI analyzer and case-database wrappers that already exist in `services/`. The regex parser should be replaced with a Pydantic action schema.

### High-impact, high-effort
11. **Get a real partner dataset.** NPCI, a bank, or a CERT will not share data, but a public Kaggle/UCI equivalent (or a CITI-Sec/MediaLab collaboration) would unblock the entire paper. The R12 cross-dataset methodology is already in place to support this.
12. **Deploy the LoRA-fine-tuned Phi-3.5 analyst** end-to-end. Today it's a code path; the next step is a real `model_used: phi3.5-mini-lora` in production responses with eval numbers (ROUGE-L, format compliance).
13. **Multi-tenant & auth.** Lumint has none. A real fraud product needs at minimum user accounts, API keys, and per-tenant rate limits before it leaves the workstation.
14. **Observability.** There is no Prometheus, OTel, or even structured logging at the router level. Production triage will be hard without it.

---

## 9. TL;DR

Lumint is an unusually complete, well-organized, multi-modal fraud detection system that doubles as a research artifact. Its engineering quality (separation of concerns, defensive fallbacks, deterministic reproduction, test breadth) is well above the median open-source security project. Its scientific layer (XAI, fusion, drift, adversarial suite, statistical tests) is structurally state-of-the-art, and the cross-dataset evaluation in R12 is genuinely honest.

The two things holding it back from a top-tier publication are (1) the synthetic-data setup that produces saturated 1.0000 metrics and (2) the fact that the most interesting number — the 0.16 F1 drop on real data — is buried in an R12 footnote instead of leading the story. The two things holding it back from production deployment are the absence of auth/multi-tenancy and the fact that the .env file is still tracked in git.

If you want one place to start, look at the R12 cross-dataset report. It is the most honest, most informative, and most under-promoted artifact in the entire repo.
