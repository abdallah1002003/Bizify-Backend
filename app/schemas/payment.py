from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional
from decimal import Decimal

class PaymentBase(BaseModel):
    user_id: UUID
    subscription_id: Optional[UUID] = None
    payment_method_id: Optional[UUID] = None
    amount: Decimal
    currency: Optional[str] = "USD"
    status: str

class PaymentRead(PaymentBase):
    id: UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
