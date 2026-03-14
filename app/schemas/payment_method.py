from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional

class PaymentMethodBase(BaseModel):
    user_id: UUID
    provider: str
    token_ref: str
    last4: Optional[str] = None
    is_default: Optional[bool] = False

class PaymentMethodCreate(PaymentMethodBase):
    pass

class PaymentMethodRead(PaymentMethodBase):
    id: UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
