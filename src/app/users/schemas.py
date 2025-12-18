"""Pydantic schemas for user operations."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserRegisterRequest(BaseModel):
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=8, max_length=128, description="User's password")

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserActivateRequest(BaseModel):
    code: str = Field(
        ...,
        min_length=4,
        max_length=4,
        pattern=r"^\d{4}$",
        description="4-digit activation code",
    )


class UserResponse(BaseModel):
    id: UUID
    email: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserCreatedResponse(BaseModel):
    id: UUID
    email: str
    is_active: bool
    created_at: datetime
    message: str = "Registration successful. Please check your email for the activation code."


class UserActivatedResponse(BaseModel):
    id: UUID
    email: str
    is_active: bool
    message: str = "Account activated successfully."


class ResendCodeResponse(BaseModel):
    message: str = "A new activation code has been sent to your email."


class ErrorResponse(BaseModel):
    error_code: str
    message: str
    details: dict | None = None
