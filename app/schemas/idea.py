from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional
from app.models.idea import IdeaStatus

class IdeaBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: Optional[IdeaStatus] = IdeaStatus.DRAFT
    ai_score: Optional[float] = None
    is_archived: Optional[bool] = False

class IdeaCreate(IdeaBase):
    owner_id: UUID

class IdeaUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[IdeaStatus] = None
    ai_score: Optional[float] = None
    is_archived: Optional[bool] = None
    business_id: Optional[UUID] = None

class IdeaRead(IdeaBase):
    id: UUID
    owner_id: UUID
    business_id: Optional[UUID] = None
    archived_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    converted_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)
