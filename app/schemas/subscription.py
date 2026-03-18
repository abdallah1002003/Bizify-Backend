import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.subscription import SubscriptionStatus


class SubscriptionBase(BaseModel):
    """
    Base Pydantic model for Subscription data.
    """
    
    user_id: uuid.UUID
    plan_id: uuid.UUID
    status: Optional[SubscriptionStatus] = SubscriptionStatus.ACTIVE


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
