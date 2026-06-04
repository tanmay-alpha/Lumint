# Lumint Research Paper Compilation Instructions

This directory contains the LaTeX draft and bibliography for the academic paper:
**"Lumint: A Unified Multimodal Fraud Intelligence Framework with LLM-Powered Explainability for India's Digital Payment Ecosystem"**

## Directory Structure
```
paper/
├── lumint_paper.tex       # Main paper draft (LaTeX)
├── lumint_paper.bib       # References and bibliography
├── figures/               # Figures folder
│   ├── architecture.pdf   # System architecture diagram (valid PDF placeholder)
│   ├── roc_curves.pdf     # ROC curve comparison (valid PDF placeholder)
│   └── shap_beeswarm.pdf  # SHAP global importance (valid PDF placeholder)
└── README.md              # This file
```

## Compilation Instructions
To compile the document to PDF, execute the following commands in order:

```bash
pdflatex lumint_paper.tex
bibtex lumint_paper
pdflatex lumint_paper.tex
pdflatex lumint_paper.tex
```

## Required LaTeX Packages
Make sure your TeX distribution has the following packages installed:
* `IEEEtran` document class (or put the `IEEEtran.cls` file in the same directory)
* `amsmath`, `amssymb` (for typesetting equations)
* `graphicx` (for figures)
* `booktabs` (for professional tables)
* `cite` (for bibliographical references)
* `url` (for formatting web links)
* `hyperref` (for hyperlinks)

## Figures Note
The files in the `figures/` directory are valid minimalist vector PDF placeholders. They will compile without bounding box or format errors in `pdflatex`. Replace these files with actual export graphics for final submission.
