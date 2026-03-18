import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class PaymentBase(BaseModel):
    """
    Base Pydantic model for Payment data.
    """
    
    user_id: uuid.UUID
    subscription_id: Optional[uuid.UUID] = None
    payment_method_id: Optional[uuid.UUID] = None
    amount: Decimal
    currency: Optional[str] = "USD"
    status: str


class PaymentRead(PaymentBase):
    """
    Pydantic model for reading Payment data.
    """
    
    id: uuid.UUID
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
