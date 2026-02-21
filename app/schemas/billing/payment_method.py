from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from uuid import UUID

class PaymentMethodBase(BaseModel):
    user_id: UUID
    provider: str
    token_ref: str
    last4: str
    is_default: Optional[bool] = None

class PaymentMethodCreate(BaseModel):
    user_id: UUID
    provider: str = Field(..., max_length=255)
    token_ref: str = Field(..., max_length=255)
    last4: str = Field(..., max_length=255)
    is_default: Optional[bool] = None

class PaymentMethodUpdate(BaseModel):
    user_id: Optional[UUID] = None
    provider: Optional[str] = None
    token_ref: Optional[str] = None
    last4: Optional[str] = None
    is_default: Optional[bool] = None
    created_at: Optional[datetime] = None

class PaymentMethodResponse(PaymentMethodBase):
    id: UUID
    # Optional Timestamps usually found in db
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
