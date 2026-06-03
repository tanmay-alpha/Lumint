# Ingestion Layer, Anonymization, and Paper Registry (Milestone R7)

This document provides an overview and reference guide for the Real Dataset Ingestion Layer, Regex-based Anonymization Utilities, and Paper Registry tools implemented in Lumint Milestone R7.

---

## 1. Real Dataset Ingestion Layer (`backend/research/dataset_ingestion.py`)

The dataset ingestion layer provides unified utility functions to import external CSV, JSON, and Directory datasets into the validated `DatasetManifest` format without dependencies on heavy data libraries (such as `pandas`).

### Supported Source Types
1. **CSV**: Reads tabular records mapping specific value and label columns to `DatasetRecord`.
2. **JSON**: Reads lists of JSON objects containing transaction or risk details.
3. **DIRECTORY**: Recursively scans directories to ingest files (e.g. UPI screenshots or PDF files) and auto-infers their labels based on the parent folder name (e.g., `clean/` -> `CLEAN`, `fraud/` -> `HIGH`).

### Usage Example
```python
from research.dataset_ingestion import IngestionConfig, IngestionSourceType, ingest_csv_to_manifest
from research.dataset_manifest import DatasetType, DatasetSplit

config = IngestionConfig(
    source_path="data/raw/urls.csv",
    source_type=IngestionSourceType.CSV,
    dataset_type=DatasetType.URL,
    label_column="fraudulent",
    value_column="url_string",
    split=DatasetSplit.BENCHMARK,
    anonymize=True,
    output_manifest_path="research/fixtures/url_real_manifest.json"
)

manifest, summary = ingest_csv_to_manifest(config)
print(f"Ingested {summary.records_written} records with warnings: {summary.warnings}")
```

---

## 2. Text and Metadata Anonymization (`backend/research/anonymization.py`)

To ensure privacy when running experiments on real-world datasets, Lumint enforces a deterministic, regex-based anonymization layer that sanitizes sensitive identifiers.

### Redaction Patterns
- **Emails**: Redacted to `<EMAIL_HASH:xxxxxxxxxxxxxxxx>` using salted SHA-256 (first 16 characters).
- **Phone Numbers**: Redacted to `<PHONE_HASH:xxxxxxxxxxxxxxxx>`.
- **UPI IDs**: Redacted to `<UPI_ID_HASH:xxxxxxxxxxxxxxxx>`.
- **UTR Numbers (12-digit)**: Redacted to `<UTR_HASH:xxxxxxxxxxxxxxxx>`.
- **Amounts (INR/USD/Symbol)**: Replaced with `<AMOUNT>`.
- **URLs**: Path, queries, and fragments are redacted to `<PATH_HASH:xxxxxxxxxxxxxxxx>`, keeping the scheme and domain for benign/phishing classification.

---

## 3. Paper Experiment Registry (`backend/research/paper_registry.py`)

The Paper Registry serves as the source of truth mapping both synthetic and real-world experiments to their target paper tables.

### Registry Schema (`paper_experiments.json`)
The registry is defined via Pydantic model `PaperExperimentRegistry` containing:
- `version`: Version string of the registry schema.
- `experiments`: A list of experiment definitions with fields:
  - `experiment_id`: Unique identifier.
  - `title`: Descriptive title of the experiment.
  - `module`: Target Lumint module (e.g., `PhishShield`, `UPIShield`, `Fusion`).
  - `manifest_path`: Path to input manifest.
  - `output_dir`: Output directory for generated artifacts/results.
  - `table_target`: Output filename under `paper/tables/` where the latex/csv table is collected.
  - `status`: `planned` | `synthetic_done` | `real_data_pending` | `complete`.
  - `notes`: Research annotations.

---

## 4. Paper Table Collector (`backend/scripts/collect_paper_tables.py`)

A script to search research outputs, copy matching metric files to `paper/tables/`, and generate a status matrix inside `paper/tables/index.md`.

```bash
# Run dry-run to preview collection
python -m scripts.collect_paper_tables --dry-run

# Run actual collection
python -m scripts.collect_paper_tables
```
