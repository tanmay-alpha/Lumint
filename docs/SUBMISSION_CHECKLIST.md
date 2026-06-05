# IEEE Access Submission Checklist

This checklist serves as the final validation tool before submitting the Lumint manuscript to **IEEE Access**.

---

## 1. Manuscript Formatting & Structure (IEEE Access Standards)
- [ ] **IEEEtran Template:** Verify that the paper matches the official IEEEtran double-column template.
- [ ] **Page Budget:** Ensure the final compiled PDF is between **8 and 10 pages** (inclusive of figures, tables, and references).
- [ ] **Abstract:** Verify that the abstract is exactly **250 words** and summarizes the methodology (CMFA), metrics (F1=1.0000 on screenshots), benchmarking (FakePay baseline comparison), drift detection (56 samples delay), and reproducibility.
- [ ] **Heading Hierarchy:** Confirm a single `\section` hierarchy with proper subsections and labels.
- [ ] **Author Details:** Validate author names and affiliations (Tanmay Mangal, Shiv Narayan Prasad; VIT Bhopal University).
- [ ] **References:** Ensure all 46 citations in `lumint_paper.bib` are properly resolved with no warnings or undefined labels in the compiled log.
- [ ] **Graphics:**
  - [ ] Figure 1 (Architecture Diagram) is clear.
  - [ ] Figure 2 (CMFA Signal Visualizations) has legible labels.
  - [ ] Figure 3 (ROC Curves comparing CMFA vs. FakePay) is correct.
  - [ ] Figure 4 (SHAP Beeswarm Plot) is high resolution.
  - [ ] Figure 5 (Drift Detection Timeline) displays clear delays.
- [ ] **Tables:** Verify captions are positioned *above* tables (IEEE style) and formatted correctly:
  - [ ] Table I: Main Results (F1-score, Precision, Recall, AUC, MCC with DeLong 95% CIs).
  - [ ] Table II: Module Ablation (Full system vs. single shields).
  - [ ] Table III: Feature Group Ablation (Lexical vs. TF-IDF, ELA vs. Metadata).
  - [ ] Table IV: Class Balancing (Raw vs. Class Weights vs. SMOTE).
  - [ ] Table V: Cross-Dataset Generalization.
  - [ ] Table VI: Concept Drift Delay.
  - [ ] Table VII: Adversarial ASR & F1 Cost.
  - [ ] Table VIII: Fine-Tuned LLM Quality (ROUGE & format compliance).

---

## 2. Experimental Rigor & Numerical Consistency
- [ ] **Metric Consistency:** F1-score (1.0000 on controlled benchmark, 0.8853 on fused pipeline) matches between Abstract, Introduction, Results, Discussion, and Conclusion.
- [ ] **Statistical Significance:** Verify that DeLong's AUC tests, bootstrap confidence intervals (2000 replicates), and McNemar's test ($\chi^2 = 12.34, p = 0.0004$) are accurately reported.
- [ ] **Cohen's d:** Confirm Discussion section reports correct effect sizes for CMFA signals:
  - [ ] Color distance: $d = 1.42$
  - [ ] Font height variance: $d = 2.85$ (highlighted as primary layout anchor)
  - [ ] ELA grid density: $d = 1.68$
- [ ] **Drift Delay:** Verify abrupt detection delay is reported as **56 samples** under ADWIN+PHT+DDM majority vote consensus.
- [ ] **Adversarial Robustness:** Confirm HopSkipJump ASR on UPIShield is 1.000 (pre-defense) and 0.000 (post-defense via adversarial training) with 0.000 F1 cost.
- [ ] **FakePay Comparison:** Confirm CMFA outperforms the FakePay baseline by **+4.79%** on hard-spoofed samples (McNemar $p < 0.05$).

---

## 3. Code & Dataset Reproducibility Package
- [ ] **GitHub Repository:**
  - [ ] Clean directory structure: `backend/`, `frontend/`, `hf_space/`, `paper/`, `dataset/`, `docs/`.
  - [ ] `reproduce.sh` runs successfully, executing dataset generation, baseline comparison, error analysis, and evaluation.
  - [ ] `REPRODUCE.md` provides clear step-by-step setup instructions.
- [ ] **HuggingFace Hub Release:**
  - [ ] UPI-FraudBench-2026 dataset is uploaded and matches CC BY 4.0 license.
  - [ ] Trained CMFA classifier checkpoints are uploaded with comprehensive Model Cards.
  - [ ] Gradio Space app is running and accessible on HuggingFace Spaces.
- [ ] **Licensing:**
  - [ ] Dataset: CC BY 4.0 (Creative Commons Attribution 4.0 International).
  - [ ] Codebase: MIT License.

---

## 4. Submission Package Preparation
- [ ] **Cover Letter:** Drafted and verified (`docs/COVER_LETTER.md`).
- [ ] **Source Files (.zip):** Package `lumint_paper.tex`, `lumint_paper.bib`, figures, tables, and class files.
- [ ] **PDF File:** Inspect compiled PDF for visual layout, orphan lines, or overlapping elements.
- [ ] **ORCID iDs:** Ensure both authors have linked their ORCID profiles.
- [ ] **IEEE Access Submission Portal:** Ready for upload at IEEE Access ScholarOne Manuscripts.
