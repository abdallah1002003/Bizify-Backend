import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict

from app.models.business import BusinessStage


class BusinessBase(BaseModel):
    """
    Base Pydantic model for Business data.
    """
    
    stage: Optional[BusinessStage] = BusinessStage.EARLY
    context_json: Optional[Any] = None
    is_archived: Optional[bool] = False


class BusinessCreate(BusinessBase):
    """
    Pydantic model for creating a new Business.
    """
    
    idea_id: Optional[uuid.UUID] = None
    owner_id: uuid.UUID


class BusinessUpdate(BaseModel):
    """
    Pydantic model for updating an existing Business.
    """
    
    stage: Optional[BusinessStage] = None
    context_json: Optional[Any] = None
    is_archived: Optional[bool] = None


class BusinessRead(BusinessBase):
    """
    Pydantic model for reading Business data.
    """
    
    id: uuid.UUID
    idea_id: Optional[uuid.UUID] = None
    owner_id: uuid.UUID
    archived_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
