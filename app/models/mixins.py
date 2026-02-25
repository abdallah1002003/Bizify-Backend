from datetime import datetime
from typing import Optional
from sqlalchemy import DateTime, Boolean, func, false
from sqlalchemy.orm import Mapped, mapped_column
from app.core.crud_utils import _utc_now as utc_now  # type: ignore

class TimestampMixin:
    """Timestamp mixin providing automated created_at and updated_at tracking."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=utc_now, 
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=utc_now, 
        server_default=func.now(),
        onupdate=utc_now, 
        nullable=False
    )

class SoftDeleteMixin:
    """Soft delete mixin providing is_deleted flags for safe archiving instead of hard SQL deletion."""

    is_deleted: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=false(), nullable=False, index=True
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        nullable=True
    )
