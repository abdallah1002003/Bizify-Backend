from pydantic import BaseModel, EmailStr, ConfigDict ,field_validator , ValidationInfo
from uuid import UUID
from datetime import datetime
from typing import Optional
from app.models.user import UserRole

class UserBase(BaseModel):
    email: EmailStr
    role: Optional[UserRole] = UserRole.USER
    is_active: Optional[bool] = True
    is_verified: Optional[bool] = False

class UserCreate(UserBase):
    password: str
    confirm_password: str
    # role is set to 'user' by default in the registration endpoint
    
    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
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
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("Passwords do not match")
        return v

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    password: Optional[str] = None

class UserRead(UserBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None


class OTPVerify(BaseModel):
    email: EmailStr
    otp_code: str
