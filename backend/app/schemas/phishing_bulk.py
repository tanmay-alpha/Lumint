from pydantic import BaseModel
from typing import List
from app.schemas.phishing import PhishingCheckResponse

class BulkPhishingCheckRequest(BaseModel):
    urls: List[str]

class BulkPhishingCheckResponse(BaseModel):
    scanned_count: int
    results: List[PhishingCheckResponse]
