from typing import Literal

from pydantic import BaseModel, EmailStr, field_validator

from app.services.password_validator import PasswordValidator


class RegisterRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    role: Literal["student", "worker", "admin"] = "student"
    
    # Phase 5.7: Add field validators (Requirement 8.1)
    @field_validator('full_name')
    @classmethod
    def validate_full_name(cls, v):
        """Validate full name is not empty and reasonable length."""
        if not v or len(v.strip()) == 0:
            raise ValueError('Full name cannot be empty')
        if len(v) < 2:
            raise ValueError('Full name must be at least 2 characters')
        if len(v) > 200:
            raise ValueError('Full name must not exceed 200 characters')
        return v.strip()
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        """Validate password meets complexity requirements."""
        is_valid, error_msg = PasswordValidator.validate(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        """Validate email format."""
        if not v or len(v) == 0:
            raise ValueError('Email cannot be empty')
        if len(v) > 255:
            raise ValueError('Email must not exceed 255 characters')
        return v.lower()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str
