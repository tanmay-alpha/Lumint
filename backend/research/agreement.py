from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from research.consensus_adapters import ConsensusResult
from research.metrics import compute_binary_classification_metrics

class AgreementResult(BaseModel):
    total_records: int
    comparable_records: int
    agreement_count: int
    disagreement_count: int
    unknown_count: int
    agreement_rate: float
    high_risk_agreement_rate: float
    disagreements: List[Dict[str, Any]] = Field(default_factory=list)

def compare_predictions_to_consensus(predictions: list, consensus: Dict[str, ConsensusResult]) -> AgreementResult:
    total_records = 0
    comparable_records = 0
    agreement_count = 0
    disagreement_count = 0
    unknown_count = 0
    high_risk_comparable = 0
    high_risk_agreement = 0
    disagreements = []
    
    for pred in predictions:
        if hasattr(pred, "record_id"):
            record_id = pred.record_id
            predicted_label = pred.predicted_label
            predicted_score = getattr(pred, "predicted_score", 0.0)
        elif isinstance(pred, dict):
            record_id = pred.get("record_id")
            predicted_label = pred.get("predicted_label")
            predicted_score = pred.get("predicted_score", 0.0)
        else:
            continue
            
        total_records += 1
        
        if record_id not in consensus:
            unknown_count += 1
            continue
            
        consensus_res = consensus[record_id]
        c_label = consensus_res.consensus_label
        
        if c_label == "UNKNOWN":
            unknown_count += 1
            continue
            
        comparable_records += 1
        
        # Determine risk matching
        is_high_risk_consensus = c_label in ("HIGH", "SUSPICIOUS")
        is_high_risk_pred = predicted_label in ("HIGH", "SUSPICIOUS")
        
        if c_label == predicted_label:
            agreement_count += 1
            if is_high_risk_consensus:
                high_risk_comparable += 1
                high_risk_agreement += 1
        else:
            disagreement_count += 1
            if is_high_risk_consensus:
                high_risk_comparable += 1
                if is_high_risk_pred:
                    # Both agree it's high risk generally, but maybe differ (e.g. HIGH vs SUSPICIOUS)
                    # Let's count this as a high risk agreement if they both flag high risk generally,
                    # but since they disagree on the exact label, it's still a label disagreement.
                    # To be strict, if they disagree on the exact label, let's check exact match for high risk agreement.
                    pass
            
            disagreements.append({
                "record_id": record_id,
                "predicted_label": predicted_label,
                "consensus_label": c_label,
                "predicted_score": predicted_score,
                "provider": consensus_res.provider,
                "evidence": consensus_res.evidence
            })
            
    agreement_rate = float(agreement_count) / float(comparable_records) if comparable_records > 0 else 0.0
    high_risk_agreement_rate = float(high_risk_agreement) / float(high_risk_comparable) if high_risk_comparable > 0 else 0.0
    
    return AgreementResult(
        total_records=total_records,
        comparable_records=comparable_records,
        agreement_count=agreement_count,
        disagreement_count=disagreement_count,
        unknown_count=unknown_count,
        agreement_rate=agreement_rate,
        high_risk_agreement_rate=high_risk_agreement_rate,
        disagreements=disagreements
    )

def compute_consensus_confusion_matrix(predictions: list, consensus: Dict[str, ConsensusResult]) -> Dict[str, Any]:
    y_true = []
    y_pred = []
    
    for pred in predictions:
        if hasattr(pred, "record_id"):
            record_id = pred.record_id
            predicted_label = pred.predicted_label
        elif isinstance(pred, dict):
            record_id = pred.get("record_id")
            predicted_label = pred.get("predicted_label")
        else:
            continue
            
        if record_id in consensus:
            c_res = consensus[record_id]
            if c_res.consensus_label != "UNKNOWN":
                y_true.append(c_res.consensus_label)
                y_pred.append(predicted_label)
                
    if not y_true:
        return {
            "TP": 0, "FP": 0, "TN": 0, "FN": 0,
            "accuracy": 0.0, "precision": 0.0, "recall": 0.0, "f1": 0.0,
            "fpr": 0.0, "fnr": 0.0, "support": 0
        }
        
    return compute_binary_classification_metrics(y_true, y_pred)
