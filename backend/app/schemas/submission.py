import uuid
from typing import Any, Optional
from pydantic import BaseModel


class SubmissionCreate(BaseModel):
    exam_id: uuid.UUID
    file_uri: str
    student_id: Optional[uuid.UUID] = None
    answers: Optional[list[dict]] = None


class SubmissionOut(BaseModel):
    id: uuid.UUID
    exam_id: uuid.UUID
    class_id: Optional[uuid.UUID] = None
    class_name: Optional[str] = None
    exam_title: Optional[str] = None
    student_id: Optional[uuid.UUID] = None
    student_email: Optional[str] = None
    file_uri: str
    status: str
    parsed_json: Optional[Any] = None

    class Config:
        from_attributes = True
