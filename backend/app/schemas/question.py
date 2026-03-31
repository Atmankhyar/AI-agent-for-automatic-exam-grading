import uuid
from typing import Any, List, Optional
from pydantic import BaseModel


class Criterion(BaseModel):
    id: str
    weight: float
    desc: str | None = None


class QuestionBase(BaseModel):
    type: str  # qcm | open | code | qru
    prompt: str
    choices: Optional[Any] = None
    answer_key: Optional[Any] = None
    rubric_json: Optional[Any] = None
    max_points: float = 1.0
    order: int = 0


class QuestionCreate(QuestionBase):
    pass


class QuestionOut(QuestionBase):
    id: uuid.UUID

    class Config:
        from_attributes = True
