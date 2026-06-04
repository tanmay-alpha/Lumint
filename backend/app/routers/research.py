import json
import os
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Dict, List, Any, Optional

router = APIRouter(prefix="/api/research", tags=["research"])

REPORTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "reports"))

# Pydantic Schemas
class MetricPoint(BaseModel):
    metric: str
    point_estimate: float
    ci_lower: float
    ci_upper: float
    confidence: float
    n_replicates: int
    method: str

class ModelPerformance(BaseModel):
    metrics: Dict[str, float]
    confidence_intervals: Dict[str, MetricPoint]
    auc_delong_ci: Dict[str, Any]

class ModuleStats(BaseModel):
    module: str
    models: Dict[str, ModelPerformance]
    significance_tests: Dict[str, Any]
    auc_comparisons: Dict[str, Any]
    best_model: str
    best_model_justification: str

class ResearchMetricsResponse(BaseModel):
    doc: ModuleStats
    phish: ModuleStats
    upi: ModuleStats

class AblationResponse(BaseModel):
    module_ablation: List[Dict[str, Any]]
    feature_ablation: List[Dict[str, Any]]
    smote_ablation: List[Dict[str, Any]]
    cross_dataset: Optional[Dict[str, Any]] = None

class ShapFeatureInfo(BaseModel):
    name: str
    mean_abs_shap: float
    direction: str
    interpretation: str
    rank: int

class ShapResponse(BaseModel):
    doc: List[ShapFeatureInfo]
    phish: List[ShapFeatureInfo]
    upi: List[ShapFeatureInfo]

class DatasetMetadata(BaseModel):
    name: str
    source: str
    n_samples: int
    class_ratio: str
    doi: str
    doi_link: str

class DatasetsResponse(BaseModel):
    phish: DatasetMetadata
    doc: DatasetMetadata
    upi: DatasetMetadata


def clean_header(h: str) -> str:
    h = h.replace("**", "").strip().lower()
    h = h.replace("&delta;", "delta").replace("&delta", "delta").replace("delta;", "delta").replace("δ", "delta").replace("Δ", "delta")
    h = h.replace("features / shields", "features")
    h = h.replace("f1 score", "f1")
    h = h.replace("auc-roc", "auc")
    h = h.replace("recall (fraud)", "recall")
    h = h.replace("strategy / configuration", "strategy")
    h = h.replace("module / shield", "module")
    h = h.replace("feature group", "feature_group")
    h = h.replace("feature count", "feature_count")
    h = h.replace(" ", "_")
    return h


def parse_md_table(lines: List[str]) -> List[Dict[str, Any]]:
    table_lines = [l.strip() for l in lines if l.strip().startswith('|')]
    if len(table_lines) < 3:
        return []
    
    headers = [h.strip() for h in table_lines[0].split('|')[1:-1]]
    clean_headers = [clean_header(h) for h in headers]
    
    rows = []
    for line in table_lines[2:]:
        if '---' in line:
            continue
        cols = [c.strip() for c in line.split('|')[1:-1]]
        if len(cols) == len(headers):
            clean_cols = [col.replace("**", "").strip() for col in cols]
            row_dict = {}
            for k, v in zip(clean_headers, clean_cols):
                if v == "--" or v == "":
                    row_dict[k] = None
                    continue
                try:
                    if "." in v:
                        row_dict[k] = float(v)
                    elif v.isdigit() or (v.startswith('-') and v[1:].isdigit()):
                        row_dict[k] = int(v)
                    else:
                        row_dict[k] = v
                except ValueError:
                    row_dict[k] = v
            rows.append(row_dict)
    return rows


@router.get("/metrics", response_model=ResearchMetricsResponse)
def get_metrics():
    doc_path = os.path.join(REPORTS_DIR, "r10_doc_statistical.json")
    phish_path = os.path.join(REPORTS_DIR, "r10_phish_statistical.json")
    upi_path = os.path.join(REPORTS_DIR, "r10_upi_statistical.json")
    
    if not (os.path.exists(doc_path) and os.path.exists(phish_path) and os.path.exists(upi_path)):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Research metrics reports are not generated yet."
        )
        
    try:
        with open(doc_path, "r", encoding="utf-8") as f:
            doc_data = json.load(f)
        with open(phish_path, "r", encoding="utf-8") as f:
            phish_data = json.load(f)
        with open(upi_path, "r", encoding="utf-8") as f:
            upi_data = json.load(f)
            
        return {
            "doc": doc_data,
            "phish": phish_data,
            "upi": upi_data
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error reading metrics reports: {str(e)}"
        )


@router.get("/ablation", response_model=AblationResponse)
def get_ablation():
    ablation_md_path = os.path.join(REPORTS_DIR, "r11_ablation_tables.md")
    cross_dataset_json_path = os.path.join(REPORTS_DIR, "r12_cross_dataset_results.json")
    
    if not os.path.exists(ablation_md_path):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ablation study report is not generated yet."
        )
        
    try:
        with open(ablation_md_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        sections = {}
        current_key = None
        section_lines = []
        
        for line in content.split("\n"):
            if line.startswith("## Table A:"):
                current_key = "module_ablation"
                section_lines = []
            elif line.startswith("## Table B:"):
                sections[current_key] = parse_md_table(section_lines)
                current_key = "feature_ablation"
                section_lines = []
            elif line.startswith("## Table C:"):
                sections[current_key] = parse_md_table(section_lines)
                current_key = "smote_ablation"
                section_lines = []
            elif line.startswith("## Table D:") or line.startswith("## Global Feature"):
                if current_key:
                    sections[current_key] = parse_md_table(section_lines)
                current_key = None
            elif current_key:
                section_lines.append(line)
                
        if current_key and current_key not in sections:
            sections[current_key] = parse_md_table(section_lines)
            
        # Parse cross-dataset metrics if available
        cross_dataset = None
        if os.path.exists(cross_dataset_json_path):
            with open(cross_dataset_json_path, "r", encoding="utf-8") as f:
                cross_dataset = json.load(f)
                
        return {
            "module_ablation": sections.get("module_ablation", []),
            "feature_ablation": sections.get("feature_ablation", []),
            "smote_ablation": sections.get("smote_ablation", []),
            "cross_dataset": cross_dataset
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error reading ablation reports: {str(e)}"
        )


@router.get("/shap", response_model=ShapResponse)
def get_shap():
    doc_path = os.path.join(REPORTS_DIR, "r11_doc_shap_global.json")
    phish_path = os.path.join(REPORTS_DIR, "r11_phish_shap_global.json")
    upi_path = os.path.join(REPORTS_DIR, "r11_upi_shap_global.json")
    
    if not (os.path.exists(doc_path) and os.path.exists(phish_path) and os.path.exists(upi_path)):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="SHAP analysis reports are not generated yet."
        )
        
    try:
        with open(doc_path, "r", encoding="utf-8") as f:
            doc_data = json.load(f)
        with open(phish_path, "r", encoding="utf-8") as f:
            phish_data = json.load(f)
        with open(upi_path, "r", encoding="utf-8") as f:
            upi_data = json.load(f)
            
        # Extract top 10 features
        return {
            "doc": doc_data.get("top_features", [])[:10],
            "phish": phish_data.get("top_features", [])[:10],
            "upi": upi_data.get("top_features", [])[:10]
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error reading SHAP reports: {str(e)}"
        )


@router.get("/datasets", response_model=DatasetsResponse)
def get_datasets():
    return {
        "phish": {
            "name": "UCI Phishing Websites Dataset",
            "source": "UCI Machine Learning Repository",
            "n_samples": 11055,
            "class_ratio": "55.7% Phishing / 44.3% Legitimate",
            "doi": "10.24432/C51W2X",
            "doi_link": "https://doi.org/10.24432/C51W2X"
        },
        "doc": {
            "name": "DocShield Synthetic Forensic Dataset",
            "source": "Lumint Synthetic Document Generator",
            "n_samples": 1500,
            "class_ratio": "50% Tampered / 50% Authentic",
            "doi": "None (Synthetic reference dataset)",
            "doi_link": "#"
        },
        "upi": {
            "name": "UPIShield Transaction Dataset",
            "source": "Lumint Synthetic UPI Receipt Generator",
            "n_samples": 1500,
            "class_ratio": "50% Tampered / 50% Authentic",
            "doi": "None (Synthetic reference dataset)",
            "doi_link": "#"
        }
    }
