import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.db.guid import GUID
from app.db.database import Base
from app.core.crud_utils import _utc_now as utc_now

class ProcessedEvent(Base):
    """Tracks processed webhook events to ensure idempotency.
    
    Used primarily for Stripe webhooks to prevent processing the same
    event multiple times in case of retries or concurrent deliveries.
    """
    __tablename__ = "processed_events"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    event_id: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    source: Mapped[str] = mapped_column(String, nullable=False, default="stripe")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
