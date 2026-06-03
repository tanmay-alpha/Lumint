from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from research.dataset_manifest import DatasetManifest

class DatasetCard(BaseModel):
    dataset_name: str
    dataset_type: str
    record_count: int
    label_distribution: Dict[str, int] = Field(default_factory=dict)
    source_description: str
    privacy_notes: str
    known_limitations: str
    recommended_use: str
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

def generate_dataset_card(
    manifest: DatasetManifest, 
    validation_summary: Optional[Dict[str, Any]] = None
) -> DatasetCard:
    """
    Generates a DatasetCard object from a DatasetManifest.
    """
    # Count types and labels
    label_counts = {"CLEAN": 0, "SUSPICIOUS": 0, "HIGH": 0}
    types_found = set()
    for r in manifest.records:
        label_counts[r.label] = label_counts.get(r.label, 0) + 1
        types_found.add(r.dataset_type.value)
        
    ds_type = ", ".join(sorted(types_found)) if types_found else "Unknown"
    
    # Generate generic descriptions/notes
    desc = manifest.notes or f"Imported/Ingested dataset '{manifest.name}'."
    
    p_notes = "Standard privacy scanning performed. "
    if validation_summary:
        codes = validation_summary.get("codes", [])
        leaks = [c for c in codes if c.startswith("LEAK_")]
        if leaks:
            p_notes += f"Warning: Potential raw identifiers detected: {', '.join(leaks)}. Redaction or verification recommended."
        else:
            p_notes += "No major raw PII leaks detected during automated scan."
    else:
        p_notes += "Anonymization status unverified."
        
    limitations = "Contains synthetic or limited samples. "
    if label_counts.get("CLEAN", 0) == 0:
        limitations += "Negative-heavy dataset structure (missing CLEAN controls)."
    elif label_counts.get("HIGH", 0) == 0:
        limitations += "Positive-heavy dataset structure (missing positive fraud markers)."
        
    rec_use = "Benchmarking fraud classification models in unified pipeline testing."
    
    return DatasetCard(
        dataset_name=manifest.name,
        dataset_type=ds_type,
        record_count=len(manifest.records),
        label_distribution=label_counts,
        source_description=desc,
        privacy_notes=p_notes,
        known_limitations=limitations,
        recommended_use=rec_use
    )

def dataset_card_to_markdown(card: DatasetCard) -> str:
    """
    Converts a DatasetCard to its markdown documentation representation.
    """
    lbl_dist_str = "\n".join([f"- **{k}**: {v} ({v/card.record_count*100:.1f}%)" if card.record_count > 0 else f"- **{k}**: {v}" for k, v in card.label_distribution.items()])
    
    return f"""# Dataset Card: {card.dataset_name}

## Overview
- **Dataset Name**: {card.dataset_name}
- **Dataset Type**: {card.dataset_type}
- **Total Records**: {card.record_count}
- **Source/Description**: {card.source_description}
- **Generated At**: {card.generated_at}

## Label Distribution
{lbl_dist_str}

## Privacy and Anonymization
{card.privacy_notes}

## Limitations
{card.known_limitations}

## Recommended Evaluation Use
{card.recommended_use}

## Reproducibility Notes
This dataset card was dynamically generated using the Lumint Dataset Card Generator. The manifest can be validated and benchmarked locally inside the Lumint research pipeline.
"""

def write_dataset_card_markdown(card: DatasetCard, output_path: Path) -> None:
    """
    Writes the dataset card markdown string to the specified path.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(dataset_card_to_markdown(card))
