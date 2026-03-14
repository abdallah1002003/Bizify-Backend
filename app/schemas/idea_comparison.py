from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime

class IdeaComparisonBase(BaseModel):
    user_id: UUID
    name: str

class IdeaComparisonCreate(IdeaComparisonBase):
    pass

class IdeaComparisonRead(IdeaComparisonBase):
    id: UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
