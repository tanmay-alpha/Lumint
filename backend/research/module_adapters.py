import time
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import BaseModel
from PIL import Image

from research.dataset_manifest import DatasetRecord, DatasetType
from app.services.phishshield.url_analyzer import analyze_url
from app.services.phishshield.risk_scorer import score_url
from app.services.upi.analyzer import analyze_upi_screenshot
from app.services.docshield.analyzer import analyze_pdf_document, analyze_image_document
from app.core.fusion import compute_lumint_score

class PredictionResult(BaseModel):
    record_id: str
    module: str
    predicted_label: str
    predicted_score: float
    latency_ms: float
    raw_output: Dict[str, Any]
    error: Optional[str] = None

def normalize_label_from_score(score: float) -> str:
    if score < 30.0:
        return "CLEAN"
    elif score < 60.0:
        return "SUSPICIOUS"
    else:
        return "HIGH"

def run_url_record(record: DatasetRecord) -> PredictionResult:
    start_time = time.perf_counter()
    try:
        url = record.path_or_value
        analysis = analyze_url(url)
        scoring = score_url(analysis.get("triggered_rules", []))
        score = float(scoring.get("risk_score", 0.0))
        label = scoring.get("risk_level", normalize_label_from_score(score))
        
        # Keep label clean/suspicious/high mapping consistent
        if label not in ["CLEAN", "SUSPICIOUS", "HIGH"]:
            label = normalize_label_from_score(score)
            
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        return PredictionResult(
            record_id=record.id,
            module="url",
            predicted_label=label,
            predicted_score=score,
            latency_ms=elapsed_ms,
            raw_output={**analysis, **scoring}
        )
    except Exception as e:
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        return PredictionResult(
            record_id=record.id,
            module="url",
            predicted_label="CLEAN",
            predicted_score=0.0,
            latency_ms=elapsed_ms,
            raw_output={},
            error=str(e)
        )

def run_upi_record(record: DatasetRecord) -> PredictionResult:
    start_time = time.perf_counter()
    temp_img_path = None
    try:
        # Check metadata for overrides
        custom_text = record.metadata.get("synthetic_text") or record.metadata.get("ocr_text")
        image_path_str = record.path_or_value
        image_path = Path(image_path_str)
        if not image_path.exists():
            repo_root = Path(__file__).resolve().parents[2]
            alt_path = repo_root / image_path_str
            if alt_path.exists():
                image_path = alt_path
        
        # If file missing but synthetic_text is provided, create a dummy image to pass verification
        if not image_path.exists() or not image_path.is_file():
            if custom_text:
                # Create a small temporary image
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                    img = Image.new("RGB", (100, 100), color=(95, 37, 159)) # PhonePe purple default
                    img.save(tmp.name)
                    temp_img_path = Path(tmp.name)
                    image_path = temp_img_path
            else:
                raise FileNotFoundError(f"UPI receipt screenshot not found at path: {image_path_str}")
        
        analysis = analyze_upi_screenshot(image_path, custom_ocr_text=custom_text)
        score = float(analysis.get("forgery_score", 0.0))
        label = analysis.get("verdict", normalize_label_from_score(score))
        
        # Map LIKELY_FORGED to HIGH or SUSPICIOUS
        if label == "LIKELY_FORGED":
            label = "HIGH"
        elif label == "GENUINE":
            label = "CLEAN"
            
        if label not in ["CLEAN", "SUSPICIOUS", "HIGH"]:
            label = normalize_label_from_score(score)
            
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        return PredictionResult(
            record_id=record.id,
            module="upi",
            predicted_label=label,
            predicted_score=score,
            latency_ms=elapsed_ms,
            raw_output=analysis
        )
    except Exception as e:
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        return PredictionResult(
            record_id=record.id,
            module="upi",
            predicted_label="CLEAN",
            predicted_score=0.0,
            latency_ms=elapsed_ms,
            raw_output={},
            error=str(e)
        )
    finally:
        # Clean up temp image
        if temp_img_path and temp_img_path.exists():
            try:
                temp_img_path.unlink()
            except Exception:
                pass

def run_document_record(record: DatasetRecord) -> PredictionResult:
    start_time = time.perf_counter()
    try:
        file_path_str = record.path_or_value
        file_path = Path(file_path_str)
        if not file_path.exists():
            repo_root = Path(__file__).resolve().parents[2]
            alt_path = repo_root / file_path_str
            if alt_path.exists():
                file_path = alt_path
        if not file_path.exists() or not file_path.is_file():
            raise FileNotFoundError(f"Document file not found at: {file_path_str}")
            
        suffix = file_path.suffix.lower()
        file_size = file_path.stat().st_size
        
        if suffix == ".pdf":
            analysis = analyze_pdf_document(file_path, file_size)
        else:
            analysis = analyze_image_document(file_path, file_size)
            
        score = float(analysis.get("risk_score", 0.0))
        label = analysis.get("risk_level", normalize_label_from_score(score))
        
        if label == "CRITICAL":
            label = "HIGH"
        elif label == "LOW":
            label = "CLEAN"
            
        if label not in ["CLEAN", "SUSPICIOUS", "HIGH"]:
            label = normalize_label_from_score(score)
            
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        return PredictionResult(
            record_id=record.id,
            module="document",
            predicted_label=label,
            predicted_score=score,
            latency_ms=elapsed_ms,
            raw_output=analysis
        )
    except Exception as e:
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        return PredictionResult(
            record_id=record.id,
            module="document",
            predicted_label="CLEAN",
            predicted_score=0.0,
            latency_ms=elapsed_ms,
            raw_output={},
            error=str(e)
        )

def run_fusion_record(record: DatasetRecord) -> PredictionResult:
    start_time = time.perf_counter()
    try:
        doc_res = record.metadata.get("document_result")
        phish_res = record.metadata.get("phishing_result")
        upi_res = record.metadata.get("upi_result")
        
        analysis = compute_lumint_score(
            doc_result=doc_res,
            phish_result=phish_res,
            upi_result=upi_res
        )
        score = float(analysis.get("unified_score", 0.0))
        label = analysis.get("risk_level", normalize_label_from_score(score))
        
        if label in ["CRITICAL", "HIGH"]:
            label = "HIGH"
        elif label in ["LOW", "CLEAN"]:
            label = "CLEAN"
            
        if label not in ["CLEAN", "SUSPICIOUS", "HIGH"]:
            label = normalize_label_from_score(score)
            
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        return PredictionResult(
            record_id=record.id,
            module="fusion",
            predicted_label=label,
            predicted_score=score,
            latency_ms=elapsed_ms,
            raw_output=analysis
        )
    except Exception as e:
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        return PredictionResult(
            record_id=record.id,
            module="fusion",
            predicted_label="CLEAN",
            predicted_score=0.0,
            latency_ms=elapsed_ms,
            raw_output={},
            error=str(e)
        )

def run_record(record: DatasetRecord) -> PredictionResult:
    dtype = record.dataset_type
    if dtype == DatasetType.URL:
        return run_url_record(record)
    elif dtype == DatasetType.UPI_SCREENSHOT:
        return run_upi_record(record)
    elif dtype == DatasetType.DOCUMENT:
        return run_document_record(record)
    elif dtype == DatasetType.FRAUD_DNA:
        # Controlled skip/not implemented
        return PredictionResult(
            record_id=record.id,
            module="fraud_dna",
            predicted_label="CLEAN",
            predicted_score=0.0,
            latency_ms=0.0,
            raw_output={},
            error="FRAUD_DNA module is not evaluated directly via static records."
        )
    else:
        return PredictionResult(
            record_id=record.id,
            module="unknown",
            predicted_label="CLEAN",
            predicted_score=0.0,
            latency_ms=0.0,
            raw_output={},
            error=f"Unsupported dataset type: {dtype}"
        )
