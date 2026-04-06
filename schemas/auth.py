from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field
from pydantic.alias_generators import to_camel

from schemas.base import TimestampSchema

class AuthRequest(BaseModel):
    email: EmailStr
    password: str

class RegisterRequest(AuthRequest):
    fullname: str

class UserResponse(TimestampSchema):
    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, populate_by_name=True)

    email: str
    fullname: Optional[str] = Field(None, serialization_alias="fullName")
    is_active: bool
    is_verified: bool