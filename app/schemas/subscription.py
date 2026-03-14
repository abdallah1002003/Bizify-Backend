from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional
from app.models.subscription import SubscriptionStatus

class SubscriptionBase(BaseModel):
    user_id: UUID
    plan_id: UUID
    status: Optional[SubscriptionStatus] = SubscriptionStatus.ACTIVE

class SubscriptionCreate(SubscriptionBase):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class SubscriptionRead(SubscriptionBase):
    id: UUID
    start_date: datetime
    end_date: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)
