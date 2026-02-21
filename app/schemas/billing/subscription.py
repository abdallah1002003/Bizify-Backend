from app.models.enums import SubscriptionStatus
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Optional
from uuid import UUID

class SubscriptionBase(BaseModel):
    user_id: UUID
    plan_id: UUID
    status: SubscriptionStatus
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class SubscriptionCreate(BaseModel):
    user_id: UUID
    plan_id: UUID
    status: SubscriptionStatus = SubscriptionStatus.PENDING

class SubscriptionUpdate(BaseModel):
    user_id: Optional[UUID] = None
    plan_id: Optional[UUID] = None
    status: Optional[SubscriptionStatus] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class SubscriptionResponse(SubscriptionBase):
    id: UUID
    # Optional Timestamps usually found in db
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
