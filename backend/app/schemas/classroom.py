import uuid

from pydantic import BaseModel, EmailStr


class ClassroomBase(BaseModel):
    name: str
    description: str | None = None


class ClassroomCreate(ClassroomBase):
    pass


class ClassroomOut(ClassroomBase):
    id: uuid.UUID
    owner_id: uuid.UUID

    class Config:
        from_attributes = True


class StudentEnrollRequest(BaseModel):
    email: EmailStr
    full_name: str | None = None
    password: str | None = None


class StudentOut(BaseModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str | None = None

    class Config:
        from_attributes = True


class ClassScoreItem(BaseModel):
    submission_id: uuid.UUID
    exam_id: uuid.UUID
    exam_title: str
    class_id: uuid.UUID | None = None
    class_name: str | None = None
    student_id: uuid.UUID | None = None
    student_email: str | None = None
    total: float
