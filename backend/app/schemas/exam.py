import uuid
from typing import Any, List, Optional

from pydantic import BaseModel

from app.schemas.question import QuestionCreate, QuestionOut


class ExamBase(BaseModel):
    title: str
    description: Optional[str] = None
    class_id: Optional[uuid.UUID] = None
    manual_statement: Optional[str] = None
    statement_file_uri: Optional[str] = None
    statement_text: Optional[str] = None
    correction_file_uri: Optional[str] = None
    correction_text: Optional[str] = None
    config_json: Optional[Any] = None


class ExamCreate(ExamBase):
    # For manual creation API, statement_file_uri is required.
    statement_file_uri: str
    questions: List[QuestionCreate] = []


class ExamOut(ExamBase):
    id: uuid.UUID
    owner_id: uuid.UUID
    class_name: Optional[str] = None
    questions: List[QuestionOut] = []

    class Config:
        from_attributes = True
