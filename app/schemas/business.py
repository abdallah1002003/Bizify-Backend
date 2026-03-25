import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, field_validator

from app.models.business import BusinessStage


class BusinessBase(BaseModel):
    """
    Base Pydantic model for Business data.
    """
    
    stage: BusinessStage = BusinessStage.EARLY
    is_archived: Optional[bool] = False

    @field_validator("stage", mode="before")
    @classmethod
    def validate_stage(cls, v):
        if isinstance(v, str):
            return v.upper()
        return v


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
    is_archived: Optional[bool] = None

    @field_validator("stage", mode="before")
    @classmethod
    def validate_stage(cls, v):
        if isinstance(v, str):
            return v.upper()
        return v


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
