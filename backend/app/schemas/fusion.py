from pydantic import BaseModel
from typing import Optional, Dict, List, Any

class CorrelationFlagSchema(BaseModel):
    flag: str
    severity: str
    detail: str

class FusionRequest(BaseModel):
    document_result: Optional[Dict[str, Any]] = None
    phishing_result: Optional[Dict[str, Any]] = None
    upi_result: Optional[Dict[str, Any]] = None
    weights: Optional[Dict[str, float]] = None
    ground_truth: Optional[int] = None

class FusionResponse(BaseModel):
    unified_score: int
    risk_level: str
    dominant_signal: Optional[str] = None
    scores: Dict[str, Optional[float]]
    weights: Dict[str, float]
    correlation_flags: List[CorrelationFlagSchema]
    explanation: List[str]
