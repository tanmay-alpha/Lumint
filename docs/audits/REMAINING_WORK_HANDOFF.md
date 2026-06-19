# Lumint — Remaining Work & Handoff

> **Last updated:** 2026-06-20  
> **Latest commits on `main`:** `4921568` (page split) and `09cec5c` (audit-phase4)  
> **Test status:** Backend 380/380 passing; `tsc --noEmit` 0 new errors.

This document is the **single source of truth for what is still open** in the Lumint repo. Update it as work progresses so the next session has zero context-recovery cost.

---

## 0. TL;DR

| Bucket | Count | Effort | Risk |
|---|---|---|---|
| **Severity 3 backend hardening** | 0 open | — | All closed in commit `09cec5c` |
| **Severity 4 polish** | ~5 untouched | Low | Low |
| **Frontend polish** | 1 minor (build verifier) | Low | Low |
| **IEEE paper deliverables** | ~25 items across 4 sections | Medium–High | None (no code) |
| **Research / dataset / eval** | ~14 items | High | None (separate track) |
| **Observability / multi-tenant / online learning** | 5 items | High | Future work |

**Roughly 50% of the work is "paper writing" and "external dataset acquisition"** — both are time-bounded but not code. The remaining code work is mostly small (~5–10 hours spread across a few sessions).

---

## 1. Recently Closed (P4 audit batch — landed in `09cec5c`)

For context only; do NOT re-fix.

- S3-03: UPI analyzer VPA sentinels → `None`
- S3-04: Per-app font-consistency threshold (PhonePe/GPay 160, others 110)
- S3-05: Multi-anchor color palette + primary-color guard
- S3-06: 12 MB per-endpoint upload cap (deliberate buffer below 20 MB global)
- S3-07: API-key rate-limit partition
- S3-08: `pool_recycle=300` for non-SQLite URLs
- S3-09: WebSocket per-connection message rate limit (100 ms min gap)
- S3-10: Pydantic `AgentAction` schema in `ai/agent.py`
- S3-11: `score_source` field on `PhishingCheckResponse`
- S3-12: `useReducedMotion` in upi-shield
- S4: removed dead `require_auth` stub; hoisted 4 utr regex patterns; updated cap test
- Frontend proxy: stripped user-supplied `X-Forwarded-*` headers; pinned `X-Forwarded-Proto=https`
- Playwright smoke test + `playwright.config.ts`

---

## 2. Severity 4 Polish — Low-Risk, Optional (1–2 hours total)

| Issue | File | Effort | Notes |
|---|---|---|---|
| `color_profile.app_hint` parameter unused (forward-compat) | `backend/app/services/upi/color_profile.py:74` | 5 min | `check_color_authenticity` doesn't accept it; signature change is additive |
| `validate_utr` returns `dict`, not `TypedDict` | `backend/app/services/upi/utr.py:80-111` | 10 min | Cosmetic type hint improvement |
| `analyzer.py` `_run_forensics` is ~230 lines | `backend/app/services/upi/analyzer.py:207-437` | 30 min | Extract `_compute_forgery_heuristics`, `_run_ml_path`, `_build_xai` — medium risk, test thoroughly |
| Move ML-train-only deps to `requirements-train.txt` | `backend/requirements.txt` | 15 min | `bitandbytes`, `peft`, `art`, `menelaus` — check with `pip show` first |
| `app/services/dashboard/stats.py` lightly used | `backend/app/services/dashboard/stats.py` | 10 min | Grep for imports; remove if dead |

**Recommended order:** stats.py cleanup first (no risk), then color_profile `app_hint` (additive), then `analyzer.py` split (test heavily).

---

## 3. Frontend Polish (1 hour total)

| Issue | File | Effort | Notes |
|---|---|---|---|
| Turbopack `next build` segfaults on this Windows box | `frontend/` (dev env) | 30 min | Pre-existing platform issue. Workaround: rely on `tsc --noEmit` for type-check; production build is verified in Vercel CI. If fixed, document the workaround in `frontend/README.md`. |
| Frontend `package.json` has untracked updates from agent | `frontend/package.json` | 5 min | `git diff frontend/package.json` and verify the new dep is what we want (likely `@playwright/test` already present) |
| ESLint config (`eslint.config.mjs`) was modified | `frontend/eslint.config.mjs` | 5 min | Verify the change is intentional (likely a rule relaxation for the page split) |

---

## 4. IEEE Paper Deliverables (highest non-code priority)

Source of truth: `docs/SUBMISSION_CHECKLIST.md`. Approximately 25 checkboxes across 4 sections. Below is the **executive view** with concrete next steps.

### 4.1 Manuscript Formatting (Section 1)
- [ ] **IEEEtran template verified** — check `paper/lumint_paper.tex` compiles to 8–10 pages
- [ ] **Abstract is 250 words** — count words, mention F1=1.0000, CMFA, FakePay +4.79%, drift 56 samples
- [ ] **References resolved** — `lumint_paper.bib` has 46 entries; ensure no undefined citation warnings
- [ ] **5 figures** — `paper/figures/`: Architecture, CMFA signals, ROC curves, SHAP beeswarm, Drift timeline
- [ ] **8 tables** — see §4.4 below for which already have data and which need regeneration

### 4.2 Experimental Rigor (Section 2)
- [ ] **Metric consistency** — F1=1.0000 (controlled) / 0.8853 (fused) must match across Abstract, Intro, Results, Discussion, Conclusion
- [ ] **Statistical tests** — DeLong AUC, bootstrap CIs (2000 replicates), McNemar (χ²=12.34, p=0.0004)
- [ ] **Cohen's d** — Color d=1.42, Font d=2.85, ELA d=1.68
- [ ] **Drift delay** — 56 samples (ADWIN+PHT+DDM consensus)
- [ ] **Adversarial ASR** — 1.000 pre-defense, 0.000 post-defense (HopSkipJump)
- [ ] **FakePay comparison** — +4.79% on hard-spoofed, McNemar p<0.05

### 4.3 Reproducibility Package (Section 3)
- [ ] **`reproduce.sh` works** — runs dataset gen, baselines, error analysis, eval
- [ ] **`REPRODUCE.md` complete** — step-by-step setup
- [ ] **HuggingFace release**:
  - [ ] UPI-FraudBench-2026 dataset (CC BY 4.0)
  - [ ] Trained CMFA checkpoints with Model Cards
  - [ ] Gradio Space running
- [ ] **Licenses**: dataset CC BY 4.0, code MIT

### 4.4 Tables (status by table)

| Table | Status | Source |
|---|---|---|
| I — Main Results | ✅ Exists | `research/reports/` |
| II — Module Ablation | ✅ Exists | R6 ablation engine |
| III — Feature Group Ablation | ✅ Exists | R6 ablation engine |
| IV — Class Balancing | ⚠️ Need to confirm | Raw / Class Weights / SMOTE |
| V — Cross-Dataset Generalization | ⚠️ Need UCI↔PhishTank run | `docs/research/research_roadmap.md §4` |
| VI — Concept Drift Delay | ✅ Exists (56 samples) | `ml/drift/registry.py` |
| VII — Adversarial ASR & F1 Cost | ⚠️ Need re-run | `paper/tables/` |
| VIII — Fine-Tuned LLM Quality | ⚠️ ROUGE + format compliance | `ai/` LoRA training |

### 4.5 Submission Package (Section 4)
- [ ] Cover letter drafted (`docs/COVER_LETTER.md` exists — review)
- [ ] `.zip` of source files: `lumint_paper.tex`, `.bib`, figures, tables, class files
- [ ] Compiled PDF visual review
- [ ] ORCID iDs linked for both authors
- [ ] IEEE Access ScholarOne upload

---

## 5. Research / Dataset / Evaluation Backlog (long-term)

Source: `docs/research/research_roadmap.md §4` + `docs/audits/2026-06-13-SUPER-DEEP-AUDIT.md`.

### 5.1 Datasets (high-effort, external dependency)
- [ ] **Real UPI receipt dataset (≥200 receipts)** — needs NPCI / bank partnership or CITI-Sec collaboration
- [ ] **Cross-dataset generalization run** (UCI ↔ PhishTank)
- [ ] **HuggingFace Space hosting** (UPI-FraudBench-2026 + Gradio app)
- [ ] **Multi-language UPI receipts** (Hindi / Tamil / Urdu)
- [ ] **Adversarial training dataset** for ASR defense

### 5.2 Evaluation & Statistical (medium-effort, internal)
- [ ] **Held-out test evaluation** in `ml/train.py`
- [ ] **Adversarial robustness table regeneration** with current models
- [ ] **SHAP summary plots** (beeswarm) at publication quality
- [ ] **Confusion matrices at multiple thresholds**
- [ ] **Inter-rater agreement study** for UPI receipt labeling
- [ ] **Bootstrapped CIs** (2000 replicates) for Table I
- [ ] **Synthetic data noise injection** (drop 1.0000 saturation to 0.95–0.98 to test generalization)

### 5.3 Models & Methods (medium-effort)
- [ ] **LoRA-fine-tuned Phi-3.5 analyst** in production
- [ ] **CMFA-VLM fusion paper section**
- [ ] **Adversarial-hardened baseline** trained with adversarial examples
- [ ] **Online learning + drift feedback loop**

---

## 6. Production / Future Engineering (lower priority)

| Item | Effort | Notes |
|---|---|---|
| **Multi-tenant auth** (per-tenant rate limits, real user accounts) | High | Currently single-tenant via `LUMINT_API_KEY` |
| **Observability** (Prometheus, OTel, structured logs at router level) | High | Currently `logger.info` only |
| **Online learning + drift feedback** (model auto-retrain on ground truth) | High | DriftRegistry already tracks signals |
| **Real-world deployment / partner dataset** | External | Publication rights required |
| **Per-tenant `LUMINT_API_KEY`** with revocation | Medium | Single key today |

---

## 7. Session Handoff — How to Continue

### What's healthy
- Backend: 380/380 tests, all Severity 3 issues closed, no dead code (except optional Severity 4)
- Frontend: page split done, tsc clean, Playwright smoke in place
- Proxy: hardened against user-supplied forwarded headers
- Database: pool_recycle + pool_pre_ping for stale-connection safety
- WS / Phishing: rate-limited by API key

### What needs attention next (recommended priority)
1. **Severity 4 cleanup** — 1–2 hours, no risk
2. **Table V (cross-dataset)** — pull UCI + PhishTank, run experiment_runner, regenerate table
3. **Table VII (adversarial ASR)** — re-run with current models
4. **Paper figures** — verify SHAP beeswarm + drift timeline at publication resolution
5. **`reproduce.sh` smoke test** — run end-to-end on a fresh machine
6. **HuggingFace Space deploy** — `hf_space/` directory
7. **Final PDF compile** — IEEEtran 8–10 page target

### Files most likely to need changes next
- `backend/research/experiment_runner.py` (Table V)
- `backend/research/paper_tables.py` (Table VII)
- `paper/figures/figure4_shap_beeswarm.png` (resolution)
- `paper/figures/figure5_drift_timeline.png` (resolution)
- `hf_space/app.py` (Gradio deployment)
- `reproduce.sh` (smoke test)
- `docs/COVER_LETTER.md` (final review)

### Files NOT to touch
- Anything in `backend/tests/test_audit_phase*_fixes.py` — these pin specific behaviors, do not relax
- `backend/app/services/upi/color_profile.py` — palette + primary guard is intentional, do not simplify
- `backend/app/services/upi/analyzer.py:248, 523` — sentinels are GONE; if you see `unknown@` in code it's a regression

### To resume from scratch in a new session
1. `cd C:\Users\TANMAY\OneDrive\Desktop\Lumint`
2. Read this file (`docs/audits/REMAINING_WORK_HANDOFF.md`)
3. Read `docs/audits/2026-06-13-SUPER-DEEP-AUDIT.md` for full audit context
4. Read `docs/SUBMISSION_CHECKLIST.md` for paper progress
5. `cd backend && source venv/Scripts/activate && pytest -q` — confirm 380/380
6. `cd frontend && npx tsc --noEmit` — confirm 0 new errors
7. Pick a task from §2 (Severity 4) or §4.4 (open tables) and go

### Quick command reference
```bash
# Backend tests
cd "C:/Users/TANMAY/OneDrive/Desktop/Lumint/backend" && source venv/Scripts/activate && python -m pytest -q

# Frontend type-check
cd "C:/Users/TANMAY/OneDrive/Desktop/Lumint/frontend" && npx tsc --noEmit 2>&1 | grep -v playwright.config.ts

# Recent commit history
cd "C:/Users/TANMAY/OneDrive/Desktop/Lumint" && git log --oneline -10

# Outstanding work status
cd "C:/Users/TANMAY/OneDrive/Desktop/Lumint" && git status --short

# Run paper reproduce script
cd "C:/Users/TANMAY/OneDrive/Desktop/Lumint" && bash reproduce.sh
```

---

## 8. Open Decisions / Questions for the User

1. **Page split scope** — The upi-shield page is now split. Do we want to extract a `<DashboardPageShell>` shared by all dashboard pages next, or leave the boilerplate duplication for now?
2. **Severity 4 cleanup** — Go through the 5 S4 items in this session, or defer?
3. **HuggingFace Space** — Is there an existing account, or do we need to set up `lumint-ai` HF org?
4. **Real UPI dataset** — Do we have a partner lined up, or is the synthetic UPI-FraudBench-2026 the submission dataset?
5. **Adversarial baseline** — Re-run with current models, or use the existing Table VII numbers?

---

**End of handoff document. Update this file as work completes.**
