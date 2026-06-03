from pydantic import BaseModel
from typing import Optional, List, Any
from app.schemas.xai import FeatureContributionSchema


class IndicatorDetail(BaseModel):
    rule: str
    score: int
    detail: str


class DocumentMetadata(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    creator: Optional[str] = None
    producer: Optional[str] = None
    creation_date: Optional[str] = None
    modification_date: Optional[str] = None
    page_count: Optional[int] = None
    is_encrypted: bool = False
    file_size: int = 0


class DocumentAnalysisResponse(BaseModel):
    doc_id: str
    original_filename: str
    saved_filename: str
    file_path: str
    file_size: int
    content_type: str
    analysis_status: str
    risk_score: Optional[int] = None
    risk_level: Optional[str] = None
    metadata: Optional[DocumentMetadata] = None
    text_analysis: Optional[Any] = None
    layout_analysis: Optional[Any] = None
    ela_analysis: Optional[Any] = None
    indicators: Optional[List[IndicatorDetail]] = None
    feature_contributions: Optional[List[FeatureContributionSchema]] = None
    explanation: Optional[List[str]] = None
    analysis_warnings: Optional[List[str]] = None   # NEW: surface sub-module failures
    message: Optional[str] = None