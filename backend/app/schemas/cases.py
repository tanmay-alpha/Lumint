from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class CaseBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: Optional[str] = "open"
    severity: Optional[str] = "medium"
    assigned_analyst: Optional[str] = None

class CaseCreate(CaseBase):
    pass

class CaseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    severity: Optional[str] = None
    assigned_analyst: Optional[str] = None
    analyst_notes: Optional[str] = None
    saved_evidence: Optional[List[Dict[str, Any]]] = None

class CaseResponse(CaseBase):
    id: int
    created_at: datetime
    updated_at: datetime
    saved_evidence: List[Dict[str, Any]]
    analyst_notes: str
    ai_summary_brief: Optional[str] = None

    class Config:
        from_attributes = True
