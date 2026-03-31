from pydantic import BaseModel, EmailStr
import uuid


class UserBase(BaseModel):
    email: EmailStr
    role: str = "teacher"
    full_name: str | None = None


class UserCreate(UserBase):
    password: str


class UserOut(UserBase):
    id: uuid.UUID

    class Config:
        from_attributes = True
