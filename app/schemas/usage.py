from pydantic import BaseModel, ConfigDict
from uuid import UUID
from typing import Optional

class UsageBase(BaseModel):
    user_id: UUID
    resource_type: str
    used: Optional[int] = 0
    limit_value: Optional[int] = None

class UsageRead(UsageBase):
    id: UUID
    model_config = ConfigDict(from_attributes=True)
