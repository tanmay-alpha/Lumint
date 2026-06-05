# UPI-FraudBench-2026 Dataset Card

## Dataset Summary
**UPI-FraudBench-2026** is a high-fidelity synthetic benchmark dataset consisting of **1,200 payment success screen screenshots** designed for fraud forensics. It provides the research community with a standardized, privacy-preserving set of transaction samples representing four major Indian UPI application layouts (PhonePe, Google Pay, Paytm, and BHIM) to evaluate pixel-level, font-level, and format-level fraud detection models.

## Dataset Structure

### Data Splits
- **Train Split**: 840 samples (420 genuine, 420 forged)
- **Validation Split**: 180 samples (90 genuine, 90 forged)
- **Test Split**: 180 samples (90 genuine, 90 forged)

### Data Fields
Each JSONL record represents a single payment success screenshot and contains:
- `id` (string): Unique sample identifier (e.g. `upi_0001`)
- `split` (string): The split assignment (`train`, `val`, or `test`)
- `label` (integer): Ground truth binary label (`0` for genuine, `1` for forged)
- `app` (string): The simulated payment application name (`phonepay`, `googlepay`, `paytm`, `bhim`)
- `forgery_type` (string/null): The specific class of forgery applied (`null`, `splice`, `overlay`, `regenerated`, `filter`)
- `utr` (string): Unique Transaction Reference identifier extracted or rendered
- `amount` (string): Transaction amount rendered (e.g. `₹450.00`)
- `features` (dictionary): Extracted forensic signal vectors:
  - `brand_palette_distance` (float): Euclidean distance in RGB color space from expected brand colors
  - `text_height_variance` (float): Standard deviation of vertical alignment heights of text elements
  - `ela_hotspot_density` (float): Error Level Analysis density indicating localized double-compression
  - `utr_valid` (boolean): Whether the UTR conforms to official length and characters
  - `ocr_confidence` (float): Overall text visibility and legibility score
  - `font_consistent` (boolean): Binary flag representing typeface rendering uniformity
- `image_path` (string): File path of the screenshot image
- `generation_method` (string): The pipeline release key (`synthetic_v1`)
- `difficulty` (string): Stratified evaluation tier (`easy`, `medium`, `hard`)

### Forgery Methods
- **Splice**: Details copied/pasted from unrelated screenshots, creating edge compression anomalies.
- **Overlay**: Fields altered with local background boxes and distinct font assets.
- **Regenerated**: Re-rendered templates with slight color shifts (representing malicious APK simulations).
- **Filter**: Global hue/contrast scaling to obscure editing marks.

## Dataset Creation

### Curation Rationale
Mobile payments are highly ubiquitous in India. Fraudulent users often present forged success screens to bypass POS billing. Since actual transactions contain bank account balances, private full names, phone numbers, and bank routes, distributing a dataset of real screens is not legally or ethically possible. UPI-FraudBench-2026 models these templates synthetically to support open-source research without compromising PII.

### Personal and Sensitive Information
None. All names, timestamps, and amounts are randomly generated or simulated via mock library frameworks.

## Considerations for Using the Data

### Limitations
- The screenshots are generated synthetically. Model performance evaluated here represents a relative capability on synthetic distributions and should be calibrated prior to production live testing.
- Official application styling changes frequently. Layout features might need tuning as brands release interface updates.

## License
Creative Commons Attribution 4.0 International (CC BY 4.0).
