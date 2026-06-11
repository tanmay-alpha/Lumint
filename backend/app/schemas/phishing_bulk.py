from pydantic import BaseModel, Field, field_validator
from typing import List
from app.schemas.phishing import PhishingCheckResponse

class BulkPhishingCheckRequest(BaseModel):
    urls: List[str] = Field(..., max_length=100, description="Maximum 100 URLs per batch")

    @field_validator("urls")
    @classmethod
    def validate_urls(cls, v: List[str]) -> List[str]:
        for url in v:
            if len(url) > 2048:
                raise ValueError(f"URL too long ({len(url)} chars, max 2048): {url[:50]}...")
        return v

class BulkPhishingCheckResponse(BaseModel):
    scanned_count: int
    results: List[PhishingCheckResponse]
