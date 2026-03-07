"""
Payment Method CRUD operations.
"""
from __future__ import annotations

import logging
from typing import Any, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import PaymentMethod
from app.services.base_service import BaseService
from app.core.crud_utils import _to_update_dict, _apply_updates
from app.core.exceptions import ValidationError

logger = logging.getLogger(__name__)

class PaymentMethodService(BaseService):
    """Refactored class-based access to payment methods."""
    async def get_payment_method(self, id: UUID) -> Optional[PaymentMethod]:
        return await get_payment_method(self.db, id)

    async def get_payment_methods(self, skip: int = 0, limit: int = 100, user_id: Optional[UUID] = None) -> List[PaymentMethod]:
        return await get_payment_methods(self.db, skip, limit, user_id)

    async def create_payment_method(self, obj_in: Any) -> PaymentMethod:
        return await create_payment_method(self.db, obj_in)

    async def update_payment_method(self, db_obj: PaymentMethod, obj_in: Any) -> PaymentMethod:
        return await update_payment_method(self.db, db_obj, obj_in)

    async def delete_payment_method(self, id: UUID) -> Optional[PaymentMethod]:
        return await delete_payment_method(self.db, id)



def _normalize_provider(raw: str | None) -> str:
    provider = (raw or "").strip().lower()
    if not provider:
        raise ValidationError(
            message="Payment provider is required",
            field="provider",
        )
    return provider


async def _unset_other_defaults(db: AsyncSession, user_id: UUID, keep_method_id: UUID) -> None:
    stmt = select(PaymentMethod).where(
        PaymentMethod.user_id == user_id,
        PaymentMethod.id != keep_method_id,
        PaymentMethod.is_default.is_(True),
    )
    result = await db.execute(stmt)
    for method in result.scalars().all():
        method.is_default = False
        db.add(method)


async def _get_first_user_payment_method(db: AsyncSession, user_id: UUID) -> Optional[PaymentMethod]:
    stmt = (
        select(PaymentMethod)
        .where(PaymentMethod.user_id == user_id)
        .order_by(PaymentMethod.created_at.asc())
        .limit(1)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


# ----------------------------
# PaymentMethod
# ----------------------------

async def get_payment_method(db: AsyncSession, id: UUID) -> Optional[PaymentMethod]:
    """Return a single payment method by id."""
    return await db.get(PaymentMethod, id)


async def get_payment_methods(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[UUID] = None,
) -> List[PaymentMethod]:
    """Return paginated payment methods, optionally filtered by user."""
    stmt = select(PaymentMethod)
    if user_id is not None:
        stmt = stmt.where(PaymentMethod.user_id == user_id)
    stmt = (
        stmt.order_by(PaymentMethod.is_default.desc(), PaymentMethod.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_payment_method(db: AsyncSession, obj_in: Any) -> PaymentMethod:
    """Create a payment method record and enforce single-default semantics."""
    data = _to_update_dict(obj_in)
    data["provider"] = _normalize_provider(data.get("provider"))
    if "user_id" not in data or data["user_id"] is None:
        raise ValidationError(
            message="user_id is required for payment method",
            field="user_id",
        )

    first_method = await _get_first_user_payment_method(db, data["user_id"])
    if first_method is None:
        data["is_default"] = True
    else:
        data["is_default"] = bool(data.get("is_default", False))

    db_obj = PaymentMethod(**data)
    db.add(db_obj)
    await db.flush()

    if db_obj.is_default:
        await _unset_other_defaults(db, db_obj.user_id, db_obj.id)

    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def update_payment_method(db: AsyncSession, db_obj: PaymentMethod, obj_in: Any) -> PaymentMethod:
    """Update mutable fields and preserve default-payment-method invariants."""
    update_data = _to_update_dict(obj_in)
    if "provider" in update_data:
        update_data["provider"] = _normalize_provider(update_data.get("provider"))

    if "is_default" in update_data:
        update_data["is_default"] = bool(update_data["is_default"])

    _apply_updates(db_obj, update_data)
    db.add(db_obj)
    await db.flush()

    if db_obj.is_default:
        await _unset_other_defaults(db, db_obj.user_id, db_obj.id)
    else:
        first_method = await _get_first_user_payment_method(db, db_obj.user_id)
        if first_method and first_method.id == db_obj.id:
            # Keep at least one default payment method for billing UX.
            db_obj.is_default = True
            db.add(db_obj)

    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def delete_payment_method(db: AsyncSession, id: UUID) -> Optional[PaymentMethod]:
    """Delete a payment method by id and preserve default fallback."""
    db_obj = await get_payment_method(db, id=id)
    if not db_obj:
        return None

    # Keep a copy of the ID before deletion
    db_obj_copy = {c.name: getattr(db_obj, c.name) for c in db_obj.__table__.columns}
    deleted_was_default = bool(db_obj.is_default)
    owner_id = db_obj.user_id
    
    # Mark for deletion and commit
    await db.delete(db_obj)
    await db.flush()

    if deleted_was_default:
        replacement = await _get_first_user_payment_method(db, owner_id)
        if replacement is not None:
            replacement.is_default = True
            db.add(replacement)

    await db.commit()
    
    # Create a new detached PaymentMethod instance to avoid lazy loading issues
    deleted_method = PaymentMethod(**db_obj_copy)
    return deleted_method
