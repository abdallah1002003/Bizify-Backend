from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from uuid import UUID

class FileBase(BaseModel):
    owner_id: UUID
    file_path: str
    file_type: str
    size: int

class FileCreate(BaseModel):
    owner_id: UUID
    file_path: str = Field(..., max_length=255)
    file_type: str = Field(..., max_length=255)
    size: int

class FileUpdate(BaseModel):
    owner_id: Optional[UUID] = None
    file_path: Optional[str] = None
    file_type: Optional[str] = None
    size: Optional[int] = None
    uploaded_at: Optional[datetime] = None

class FileResponse(FileBase):
    id: UUID
    # Optional Timestamps usually found in db
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
