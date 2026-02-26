from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from uuid import UUID

class PaymentBase(BaseModel):
    user_id: UUID
    subscription_id: UUID
    payment_method_id: UUID
    amount: Decimal
    currency: str
    status: str

class PaymentCreate(BaseModel):
    user_id: UUID
    subscription_id: UUID
    payment_method_id: UUID
    amount: Decimal
    currency: str = Field(..., max_length=255)
    status: str = Field(..., max_length=255)

class PaymentUpdate(BaseModel):
    user_id: Optional[UUID] = None
    subscription_id: Optional[UUID] = None
    payment_method_id: Optional[UUID] = None
    amount: Optional[Decimal] = None
    currency: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[datetime] = None

class PaymentResponse(PaymentBase):
    id: UUID
    # Optional Timestamps usually found in db
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
