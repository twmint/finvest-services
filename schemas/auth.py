from typing import Optional

from pydantic import BaseModel, EmailStr

from schemas.base import TimestampSchema


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    fullname: str


class UserResponse(TimestampSchema):
    email: str
    fullname: Optional[str]
    is_active: bool
    is_verified: bool