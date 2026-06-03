from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from research.dataset_manifest import DatasetManifest, DatasetRecord

class ErrorCase(BaseModel):
    record_id: str
    true_label: str
    predicted_label: str
    predicted_score: float
    error_type: str  # "FALSE_POSITIVE" or "FALSE_NEGATIVE"
    taxonomy_category: str  # "CORRELATION_MISS", "OVER_SENSITIVE", "FORENSICS_FAILURE", "NO_ACTIVE_SIGNALS", "API_ERROR", "OTHER"
    details: str

def classify_error_case(
    record_id: str,
    true_label: str,
    pred_label: str,
    pred_score: float,
    raw_output: Dict[str, Any],
    error_msg: Optional[str] = None
) -> Optional[ErrorCase]:
    """
    Heuristically classifies a prediction error into one of the research taxonomy categories.
    """
    from research.metrics import to_bool
    
    true_b = to_bool(true_label)
    pred_b = to_bool(pred_label)
    
    if true_b == pred_b:
        return None
        
    error_type = "FALSE_NEGATIVE" if true_b else "FALSE_POSITIVE"
    
    category = "OTHER"
    details = ""
    
    if error_msg:
        category = "API_ERROR"
        details = f"Adapter run failed: {error_msg}"
    else:
        explanation = raw_output.get("explanation") or []
        explanation_str = " ".join(explanation).lower()
        corr_flags = raw_output.get("correlation_flags") or []
        
        if "no active signals" in explanation_str:
            category = "NO_ACTIVE_SIGNALS"
            details = "Zero active modalities identified or successfully processed."
        elif error_type == "FALSE_POSITIVE":
            if pred_score > 0 and pred_score < 50.0:
                category = "OVER_SENSITIVE"
                details = f"Borderline score ({pred_score:.1f}) incorrectly crossed verdict threshold."
            else:
                category = "FORENSICS_FAILURE"
                details = f"Anomaly detector generated high score ({pred_score:.1f}) on a clean sample."
        elif error_type == "FALSE_NEGATIVE":
            if corr_flags:
                category = "CORRELATION_MISS"
                details = f"Multi-modal correlation flags identified ({len(corr_flags)}), but final score was suppressed."
            else:
                category = "FORENSICS_FAILURE"
                details = f"Target forgery/phish signatures failed to trigger threshold. Final score: {pred_score:.1f}."
                
    return ErrorCase(
        record_id=record_id,
        true_label=true_label,
        predicted_label=pred_label,
        predicted_score=pred_score,
        error_type=error_type,
        taxonomy_category=category,
        details=details
    )

def analyze_errors(results: List[Any], manifest: DatasetManifest) -> List[ErrorCase]:
    """
    Correlates prediction results with dataset records to isolate and categorize error cases.
    """
    record_by_id = {r.id: r for r in manifest.records}
    error_cases = []
    
    for res in results:
        if isinstance(res, dict):
            rec_id = res.get("record_id")
            pred_label = res.get("predicted_label")
            pred_score = res.get("predicted_score", 0.0)
            err = res.get("error")
            raw_out = res.get("raw_result") or res.get("raw_output") or {}
        else:
            rec_id = getattr(res, "record_id", None)
            pred_label = getattr(res, "predicted_label", None)
            pred_score = getattr(res, "predicted_score", 0.0)
            err = getattr(res, "error", None)
            raw_out = getattr(res, "raw_result", None) or getattr(res, "raw_output", None) or {}
            
        if not rec_id:
            continue
            
        rec = record_by_id.get(rec_id)
        if not rec:
            continue
            
        ec = classify_error_case(
            record_id=rec_id,
            true_label=rec.label,
            pred_label=pred_label,
            pred_score=pred_score,
            raw_output=raw_out,
            error_msg=err
        )
        if ec:
            error_cases.append(ec)
            
    return error_cases

def summarize_top_errors(error_cases: List[ErrorCase]) -> Dict[str, Any]:
    """
    Aggregates metrics and statistics on error distribution.
    """
    summary = {
        "total_errors": len(error_cases),
        "error_types": {},
        "categories": {},
        "samples": []
    }
    
    for ec in error_cases:
        summary["error_types"][ec.error_type] = summary["error_types"].get(ec.error_type, 0) + 1
        summary["categories"][ec.taxonomy_category] = summary["categories"].get(ec.taxonomy_category, 0) + 1
        
    for ec in error_cases[:5]:
        summary["samples"].append({
            "record_id": ec.record_id,
            "type": ec.error_type,
            "category": ec.taxonomy_category,
            "details": ec.details
        })
        
    return summary
