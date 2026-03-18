import uuid
from typing import Optional

from pydantic import BaseModel, ConfigDict


class UsageBase(BaseModel):
    """
    Base Pydantic model for Usage tracking data.
    """
    
    user_id: uuid.UUID
    resource_type: str
    used: Optional[int] = 0
    limit_value: Optional[int] = None


class UsageRead(UsageBase):
    """
    Pydantic model for reading Usage tracking data.
    """
    
    id: uuid.UUID
    
    model_config = ConfigDict(from_attributes=True)
