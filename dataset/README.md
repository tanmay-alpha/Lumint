# UPI-FraudBench-2026: First Open Benchmark for UPI Payment Screenshot Forensics

[![Dataset License](https://img.shields.io/badge/License-CC%20BY%204.0-blue.svg)](https://creativecommons.org/licenses/by/4.0/)
[![HuggingFace Hub](https://img.shields.io/badge/%F0%9F%A4%97%20HuggingFace-Dataset-orange.svg)](https://huggingface.co/datasets/tanmay-alpha/upi-fraudbench-2026)

## Dataset Summary
**UPI-FraudBench-2026** is the first public, open-source benchmark dataset specifically designed for detecting fraud in Unified Payments Interface (UPI) success screen screenshots. UPI is India's premier real-time payment system, processing billions of transactions monthly. Along with this growth, screenshot-based merchant fraud—where malicious actors present forged or simulated payment success screens to merchants—has risen significantly. 

Due to strict financial data protection laws, bank-level privacy requirements, and the presence of Personally Identifiable Information (PII) on real transaction screens, public release of real screenshots is legally and ethically infeasible. UPI-FraudBench-2026 addresses this gap using a **privacy-preserving synthetic generation methodology**. The pipeline produces high-fidelity, statistically equivalent screenshots modeled after four major UPI payment apps: **PhonePe, Google Pay, Paytm, and BHIM**, complete with realistic transaction metadata, recipient names, amounts, and timestamps.

## Dataset Structure

### Split Statistics
The dataset contains **1,200 samples** balanced exactly 50/50 between genuine and forged screenshots:
- **Total Size**: 1,200 samples
- **Splits**: 
  - **Train (70%)**: 840 samples (420 genuine, 420 forged)
  - **Val (15%)**: 180 samples (90 genuine, 90 forged)
  - **Test (15%)**: 180 samples (90 genuine, 90 forged)
- **App Distribution**: Balanced equally (300 samples per app: 150 genuine, 150 forged).

### Label Schema
Each sample is represented in a single unified JSONL annotation line with the following structure:

```json
{
  "id": "upi_0001",
  "split": "train",
  "label": 0,           // 0 = genuine, 1 = forged
  "app": "phonepay",    // phonepay | googlepay | paytm | bhim
  "forgery_type": null, // null | splice | overlay | regenerated | filter
  "utr": "421856789012",
  "amount": "₹450.00",
  "features": {
    "brand_palette_distance": 0.0021,
    "text_height_variance": 0.12,
    "ela_hotspot_density": 0.005,
    "utr_valid": true,
    "ocr_confidence": 0.98,
    "font_consistent": true
  },
  "image_path": "images/train/upi_0001.png",
  "generation_method": "synthetic_v1",
  "difficulty": "easy"  // easy | medium | hard (for stratified evaluation)
}
```

---

## Forgery Types & Hard Negatives
To train robust models capable of generalized out-of-distribution detection, the forged splits include four distinct classes of forensic manipulation:

1. **Splice Forgery (`splice`)**:
   - *Description*: The transaction amount or Unique Transaction Reference (UTR) is copied and pasted from a different transaction screenshot.
   - *Detection Signal*: ELA (Error Level Analysis) hotspots showing compression inconsistencies at boundary edges; micro-misalignment of text blocks.

2. **Overlay Forgery (`overlay`)**:
   - *Description*: A genuine payment template has its transaction details edited by overlaying new text fields directly on top of the original text.
   - *Detection Signal*: Minor font size, typeface, weight, or rendering discrepancies compared to the template's native font engine; double-compression boundaries.

3. **Regenerated Forgery (`regenerated`)**:
   - *Description*: Entirely synthetic payment success screens built using HTML/CSS templates or canvas engines to mimic the app.
   - *Detection Signal*: Subtle shifts in brand color palettes, incorrect brand palette distances, and global pixel layouts.
   - *Hardest Variant*: Regenerated screenshots with near-perfect color matches, which pass color checks but are flagged by font variance and ELA hotspot densities.

4. **Filter Forgery (`filter`)**:
   - *Description*: Hue, contrast, saturation, or noise parameters are adjusted on a genuine payment screenshot to alter legibility or mask manual edits.
   - *Detection Signal*: Extreme global histogram deviations, altered brand color space values.

---

## Difficulty Classification
For stratified evaluation, each forged sample is labeled with an evaluation difficulty:
- **Easy**: Obvious brand color mismatch or invalid UTR format.
- **Medium**: Valid UTR format + slight brand color drift.
- **Hard**: Valid UTR format + near-accurate brand colors + subtle font inconsistencies or overlay edits detectable only by multi-modal forensics.

## Usage & License
The dataset is licensed under **Creative Commons Attribution 4.0 International (CC BY 4.0)**. 
Please cite this dataset and paper when using these benchmarks for research:
```bibtex
@dataset{upi_fraudbench_2026,
  author    = {Tanmay Alpha and SentinelX Research},
  title     = {UPI-FraudBench-2026: First Open Benchmark for UPI Payment Screenshot Forensics},
  year      = {2026},
  publisher = {HuggingFace Datasets},
  url       = {https://huggingface.co/datasets/tanmay-alpha/upi-fraudbench-2026}
}
```
