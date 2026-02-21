from app.models.enums import UserRole
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from pydantic import EmailStr
from typing import Optional
from uuid import UUID

class UserBase(BaseModel):
    name: str
    email: EmailStr
    role: UserRole
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None

class UserCreate(BaseModel):
    name: str = Field(..., max_length=255)
    email: EmailStr
    password_hash: str = Field(..., min_length=8)
    role: UserRole
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password_hash: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class UserResponse(UserBase):
    id: UUID
    # Optional Timestamps usually found in db
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
