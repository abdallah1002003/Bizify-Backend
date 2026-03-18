import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class PaymentMethodBase(BaseModel):
    """
    Base Pydantic model for Payment Method data.
    """
    
    user_id: uuid.UUID
    provider: str
    token_ref: str
    last4: Optional[str] = None
    is_default: Optional[bool] = False


class PaymentMethodCreate(PaymentMethodBase):
    """
    Pydantic model for creating a new Payment Method.
    """
    
    pass


class PaymentMethodRead(PaymentMethodBase):
    """
    Pydantic model for reading Payment Method data.
    """
    
    id: uuid.UUID
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
