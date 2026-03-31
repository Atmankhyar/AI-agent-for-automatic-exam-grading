from pydantic import BaseModel, EmailStr


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class MeOut(BaseModel):
    id: str
    email: EmailStr
    role: str
    full_name: str | None = None
