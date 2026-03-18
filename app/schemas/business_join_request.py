import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.business_join_request import JoinRequestStatus


class BusinessJoinRequestBase(BaseModel):
    """
    Base Pydantic model for Business Join Request data.
    """
    
    business_id: uuid.UUID
    user_id: uuid.UUID
    status: Optional[JoinRequestStatus] = JoinRequestStatus.PENDING


class BusinessJoinRequestCreate(BusinessJoinRequestBase):
    """
    Pydantic model for creating a Business Join Request.
    """
    
    pass


class BusinessJoinRequestRead(BusinessJoinRequestBase):
    """
    Pydantic model for reading Business Join Request data.
    """
    
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
