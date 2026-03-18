import uuid
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ComparisonItemBase(BaseModel):
    """
    Base Pydantic model for Comparison Item data.
    """
    
    comparison_id: uuid.UUID
    idea_id: uuid.UUID
    rank_index: Optional[int] = None


class ComparisonItemRead(ComparisonItemBase):
    """
    Pydantic model for reading Comparison Item data.
    """
    
    id: uuid.UUID
    
    model_config = ConfigDict(from_attributes=True)
