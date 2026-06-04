# How to Cite Lumint

If you use Lumint in your research, please cite the following:

## BibTeX

```bibtex
@article{lumint2025,
  author    = {Tanmay},
  title     = {{Lumint}: A Multimodal Fraud Intelligence Framework with
               Explainable {AI}, Concept Drift Monitoring, and Adversarial
               Robustness for {India} {UPI} Payments},
  journal   = {arXiv preprint},
  year      = {2025},
  url       = {https://github.com/tanmay-alpha/lumint},
  note      = {Open-source repository: \url{https://github.com/tanmay-alpha/lumint}}
}
```

## IEEE Style

> Tanmay, "Lumint: A Multimodal Fraud Intelligence Framework with Explainable AI, Concept Drift Monitoring, and Adversarial Robustness for India UPI Payments," *arXiv preprint*, 2025. [Online]. Available: https://github.com/tanmay-alpha/lumint

## APA Style

> Tanmay. (2025). *Lumint: A Multimodal Fraud Intelligence Framework with Explainable AI, Concept Drift Monitoring, and Adversarial Robustness for India UPI Payments*. arXiv preprint. https://github.com/tanmay-alpha/lumint

---

## Key Research Contributions to Cite

| Contribution | Paper Section | Key Result |
|---|---|---|
| Multimodal Fusion (C1) | §4.1–4.6 | F1=0.885, AUC=0.902 |
| LLM Analyst + LoRA (C2) | §4.9 | ROUGE-L +61% over baseline |
| SHAP + LLM Bridge (C3) | §5.2 | 96% format compliance |
| Concept Drift Monitor (C4) | §4.7, Table 4 | 56-sample delay, 0 false alarms |
| Adversarial Robustness (C5) | §4.8, Table 5 | ASR=0.000 (FGSM, high-dim) |
| Statistical Validation (C6) | §4.3, Table 3 | McNemar p=0.0004 |

---

## Dependencies to Cite

If you use specific components, also cite their original papers:

- **SHAP**: Lundberg & Lee (NeurIPS 2017)
- **SMOTE**: Chawla et al. (JAIR 2002)
- **ADWIN**: Bifet & Gavalda (SDM 2007)
- **Page-Hinkley**: Page (Biometrika 1954)
- **DDM**: Gama et al. (SBIA 2004)
- **FGSM**: Goodfellow et al. (ICLR 2015)
- **HopSkipJump**: Chen et al. (IEEE S&P 2020)
- **LoRA**: Hu et al. (ICLR 2022)
- **Phi-3.5-mini**: Microsoft (arXiv 2024)
- **scikit-learn**: Pedregosa et al. (JMLR 2011)

Full BibTeX for all dependencies: `paper/lumint_paper.bib`
