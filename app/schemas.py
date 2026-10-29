from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class PackageSignals(BaseModel):
    name: str
    exists: bool
    age_days: Optional[int] = None
    release_count: Optional[int] = None
    has_repo: Optional[bool] = None
    downloads: Optional[int] = None


class Finding(BaseModel):
    package: str
    verdict: Literal["ok", "suspicious", "hallucinated"]
    risk_score: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasons: List[str] = Field(default_factory=list)
    suggested_fix: Optional[str] = None
