import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, ValidationInfo, field_validator

from app.models.user import UserRole


class GoogleCallbackRequest(BaseModel):
    """
    Pydantic model for Google OAuth2 callback.
    """
    code: str


class UserBase(BaseModel):
    """
    Base Pydantic model for User data.
    """
    
    email: EmailStr
    full_name: Optional[str] = None
    role: Optional[UserRole] = UserRole.USER
    is_active: Optional[bool] = True
    is_verified: Optional[bool] = False

    @field_validator("role", mode="before")
    @classmethod
    def validate_role(cls, v):
        if isinstance(v, str):
            return v.upper()
        return v


class UserCreate(UserBase):
    """
    Pydantic model for creating a new User.
    """
    
    password: str
    confirm_password: str
    
    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        """
        Validate password strength.
        """
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        return v

    @field_validator("confirm_password")
    @classmethod
    def confirm_password_match(cls, v: str, info: ValidationInfo) -> str:
        """
        Validate that passwords match.
        """
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("Passwords do not match")
        return v


    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    password: Optional[str] = None

    @field_validator("role", mode="before")
    @classmethod
    def validate_role(cls, v):
        if isinstance(v, str):
            return v.upper()
        return v


class UserRead(UserBase):
    """
    Pydantic model for reading User data.
    """
    
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    """
    Pydantic model for an authentication token.
    """
    
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """
    Pydantic model for token payload data.
    """
    
    email: Optional[str] = None


class OTPVerify(BaseModel):
    """
    Pydantic model for OTP verification.
    """
    
    email: EmailStr
    otp_code: str


class OTPResendRequest(BaseModel):
    """
    Pydantic model for requesting a new account verification OTP.
    """

    email: EmailStr
