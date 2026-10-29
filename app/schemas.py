from typing import Optional
from pydantic import BaseModel


class PackageSignals(BaseModel):
    name: str
    exists: bool
    age_days: Optional[int] = None
    release_count: Optional[int] = None
    has_repo: Optional[bool] = None
    downloads: Optional[int] = None
