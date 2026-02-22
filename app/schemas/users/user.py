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
    name: str = Field(..., min_length=2, max_length=100, pattern=r"^[A-Za-z0-9\s\-_@.]+$")
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None

class UserResponse(UserBase):
    id: UUID
    # Optional Timestamps usually found in db
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
