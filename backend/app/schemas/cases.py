from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime

# Severity whitelist to prevent arbitrary values.
VALID_SEVERITIES = frozenset({"low", "medium", "high", "critical"})

# Status whitelist.
VALID_STATUSES = frozenset({"open", "investigating", "escalated", "resolved", "closed"})


class CaseBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Case title")
    description: Optional[str] = Field(default=None, max_length=10000, description="Case description")
    status: Optional[str] = Field(default="open", max_length=20, description="Case status (whitelist)")
    severity: Optional[str] = Field(default="medium", max_length=20, description="Severity level (whitelist)")
    assigned_analyst: Optional[str] = Field(default=None, max_length=100, description="Assigned analyst ID")

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v):
        if v and v.lower() not in VALID_SEVERITIES:
            raise ValueError(f"Severity must be one of: {', '.join(sorted(VALID_SEVERITIES))}")
        return v.lower() if v else v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        if v and v.lower() not in VALID_STATUSES:
            raise ValueError(f"Status must be one of: {', '.join(sorted(VALID_STATUSES))}")
        return v.lower() if v else v


class CaseCreate(CaseBase):
    pass

class CaseUpdate(BaseModel):
    # Pydantic default is to silently drop unknown fields. We forbid them
    # explicitly so a malicious client sending
    # ``{"assigned_analyst": "X", "id": 0, "created_at": "1970-01-01"}``
    # gets a 422, not a no-op or a partial write.
    model_config = ConfigDict(extra="forbid")

    title: Optional[str] = Field(default=None, max_length=200, description="Case title")
    description: Optional[str] = Field(default=None, max_length=10000, description="Case description")
    status: Optional[str] = Field(default=None, max_length=20, description="Case status (whitelist)")
    severity: Optional[str] = Field(default=None, max_length=20, description="Severity level (whitelist)")
    assigned_analyst: Optional[str] = Field(default=None, max_length=100, description="Assigned analyst ID")
    analyst_notes: Optional[str] = Field(default=None, max_length=50000, description="Analyst notes")
    saved_evidence: Optional[List[Dict[str, Any]]] = Field(default=None, max_length=100, description="Evidence items (max 100)")

class CaseResponse(CaseBase):
    id: int
    created_at: datetime
    updated_at: datetime
    saved_evidence: List[Dict[str, Any]]
    analyst_notes: str
    ai_summary_brief: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
