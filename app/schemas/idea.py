import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.idea import IdeaStatus


class IdeaBase(BaseModel):
    """
    Base Pydantic model for Business Idea data.
    """
    
    title: str
    description: Optional[str] = None
    status: Optional[IdeaStatus] = IdeaStatus.DRAFT
    ai_score: Optional[float] = None
    is_archived: Optional[bool] = False


class IdeaCreate(IdeaBase):
    """
    Pydantic model for creating a new Business Idea.
    """
    
    owner_id: uuid.UUID


class IdeaUpdate(BaseModel):
    """
    Pydantic model for updating an existing Business Idea.
    """
    
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[IdeaStatus] = None
    ai_score: Optional[float] = None
    is_archived: Optional[bool] = None
    business_id: Optional[uuid.UUID] = None


class IdeaRead(IdeaBase):
    """
    Pydantic model for reading Business Idea data.
    """
    
    id: uuid.UUID
    owner_id: uuid.UUID
    business_id: Optional[uuid.UUID] = None
    archived_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    converted_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
