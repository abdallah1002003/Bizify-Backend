import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class SecurityLogBase(BaseModel):
    """
    Base Pydantic model for Security Log data.
    """
    
    event_type: str
    details: Optional[Any] = None
    ip_address: Optional[str] = None


class SecurityLogRead(SecurityLogBase):
    """
    Pydantic model for reading Security Log data.
    """
    
    id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
