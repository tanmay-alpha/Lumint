from pydantic import BaseModel
from typing import Optional, Union

class FeatureContributionSchema(BaseModel):
    name: str
    value: Optional[Union[str, int, float, bool]] = None
    contribution_pct: float
    raw_score: float
    direction: str
    evidence: str
