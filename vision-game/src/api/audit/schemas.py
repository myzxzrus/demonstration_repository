from typing import List
from pydantic import BaseModel
import datetime


class AuditScheme(BaseModel):
    id: str = None
    created_utc: datetime.datetime = None
    updated_utc: datetime.datetime = None
    user: str = None
    action: str = None
    date: datetime.datetime = None

    class Config:
        orm_mode = True


class AuditResponseScheme(BaseModel):
    count: int
    audit: List[AuditScheme]
    page: int = None
    size: int = None

