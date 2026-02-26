from app.models.enums import IdeaStatus
from datetime import datetime
from pydantic import ConfigDict, Field
from typing import Optional
from uuid import UUID

from app.schemas.core_base import SafeBaseModel


class IdeaBase(SafeBaseModel):
    owner_id: UUID
    business_id: Optional[UUID] = None
    title: str
    description: str
    status: IdeaStatus
    ai_score: float
    is_archived: Optional[bool] = None

class IdeaCreate(SafeBaseModel):
    owner_id: UUID
    business_id: Optional[UUID] = None
    title: str = Field(..., max_length=255)
    description: str
    status: IdeaStatus
    ai_score: float
    is_archived: Optional[bool] = None

class IdeaUpdate(SafeBaseModel):
    business_id: Optional[UUID] = None
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[IdeaStatus] = None
    ai_score: Optional[float] = None
    is_archived: Optional[bool] = None
    archived_at: Optional[datetime] = None

class IdeaResponse(IdeaBase):
    id: UUID
    # Optional Timestamps usually found in db
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
