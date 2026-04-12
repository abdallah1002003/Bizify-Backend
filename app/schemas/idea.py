import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, field_validator

from app.models.idea import IdeaStatus


class IdeaBase(BaseModel):
    """
    Base Pydantic model for Business Idea data.
    """
    
    title: str
    description: Optional[str] = None
    status: IdeaStatus = IdeaStatus.DRAFT
    is_archived: Optional[bool] = False
    budget: Optional[float] = None
    skills: Optional[List[str]] = None
    feasibility: Optional[float] = None


    @field_validator("status", mode="before")
    @classmethod
    def validate_status(cls, v):
        if isinstance(v, str):
            return v.upper()
        return v


class IdeaCreate(IdeaBase):
    """
    Pydantic model for creating a new Business Idea.
    """
    pass


class IdeaUpdate(BaseModel):
    """
    Pydantic model for updating an existing Business Idea.
    """
    
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[IdeaStatus] = None
    is_archived: Optional[bool] = None
    budget: Optional[float] = None
    skills: Optional[List[str]] = None
    feasibility: Optional[float] = None


    @field_validator("status", mode="before")
    @classmethod
    def validate_status(cls, v):
        if isinstance(v, str):
            return v.upper()
        return v
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
