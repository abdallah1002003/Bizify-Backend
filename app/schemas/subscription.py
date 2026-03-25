import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator

from app.models.subscription import SubscriptionStatus


class SubscriptionBase(BaseModel):
    """
    Base Pydantic model for Subscription data.
    """
    
    user_id: uuid.UUID
    plan_id: uuid.UUID
    status: Optional[SubscriptionStatus] = SubscriptionStatus.ACTIVE

    @field_validator("status", mode="before")
    @classmethod
    def validate_status(cls, v):
        if isinstance(v, str):
            return v.upper()
        return v


class SubscriptionCreate(SubscriptionBase):
    """
    Pydantic model for creating a new Subscription.
    """
    
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class SubscriptionRead(SubscriptionBase):
    """
    Pydantic model for reading Subscription data.
    """
    
    id: uuid.UUID
    start_date: datetime
    end_date: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
