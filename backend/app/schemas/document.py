from pydantic import BaseModel
from typing import Optional, List


class IndicatorDetail(BaseModel):
    rule: str
    score: int
    detail: str


class DocumentMetadata(BaseModel):
    title: Optional[str]
    author: Optional[str]
    creator: Optional[str]
    producer: Optional[str]
    creation_date: Optional[str]
    modification_date: Optional[str]
    page_count: Optional[int]
    is_encrypted: bool
    file_size: int


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
    indicators: Optional[List[IndicatorDetail]] = None
    explanation: Optional[List[str]] = None
    message: Optional[str] = None