from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class ThreatFeedBase(BaseModel):
    indicator_type: str  # 'domain', 'ip', 'upi_handle', 'hash'
    value: str
    source: str
    severity: str  # low, medium, high, critical
    description: Optional[str] = None
    mitigation_strategy: Optional[str] = None

class ThreatFeedCreate(ThreatFeedBase):
    pass

class ThreatFeedResponse(ThreatFeedBase):
    id: int
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)
