import uuid
from typing import Any, List, Optional
from pydantic import BaseModel


class ScoreItemOut(BaseModel):
    id: uuid.UUID
    question_id: uuid.UUID
    points: float
    feedback: Optional[Any] = None

    class Config:
        from_attributes = True


class ScoreOut(BaseModel):
    id: uuid.UUID
    submission_id: uuid.UUID
    total: float
    breakdown: Optional[Any] = None
    feedback: Optional[Any] = None
    items: List[ScoreItemOut] = []

    class Config:
        from_attributes = True
