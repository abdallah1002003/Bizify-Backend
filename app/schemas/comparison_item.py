from pydantic import BaseModel, ConfigDict
from uuid import UUID
from typing import Optional

class ComparisonItemBase(BaseModel):
    comparison_id: UUID
    idea_id: UUID
    rank_index: Optional[int] = None

class ComparisonItemRead(ComparisonItemBase):
    id: UUID
    model_config = ConfigDict(from_attributes=True)
