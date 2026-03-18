import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class IdeaComparisonBase(BaseModel):
    """
    Base Pydantic model for Idea Comparison data.
    """
    
    user_id: uuid.UUID
    name: str


class IdeaComparisonCreate(IdeaComparisonBase):
    """
    Pydantic model for creating an Idea Comparison.
    """
    
    pass


class IdeaComparisonRead(IdeaComparisonBase):
    """
    Pydantic model for reading Idea Comparison data.
    """
    
    id: uuid.UUID
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
