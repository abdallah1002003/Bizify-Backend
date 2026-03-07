"""
Payment Method CRUD operations.
"""
from __future__ import annotations

import logging
from typing import Any, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import PaymentMethod
from app.core.crud_utils import _to_update_dict
from app.core.exceptions import ValidationError
from app.repositories.billing_repository import PaymentMethodRepository
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)


def _normalize_provider(raw: str | None) -> str:
    provider = (raw or "").strip().lower()
    if not provider:
        raise ValidationError(
            message="Payment provider is required",
            field="provider",
        )
    return provider


class PaymentMethodService(BaseService):
    """Service for managing PaymentMethod records with default-enforcement logic."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)
        self.repo = PaymentMethodRepository(db)

    async def _unset_other_defaults(self, user_id: UUID, keep_method_id: UUID) -> None:
        methods = await self.repo.get_for_user(user_id)
        for method in methods:
            if method.id != keep_method_id and method.is_default:
                await self.repo.update(method, {"is_default": False})

    async def _get_first_user_payment_method(self, user_id: UUID) -> Optional[PaymentMethod]:
        methods = await self.repo.get_for_user(user_id)
        if not methods:
            return None
        methods.sort(key=lambda m: m.created_at)
        return methods[0]

    async def get_payment_method(self, id: UUID) -> Optional[PaymentMethod]:
        """Return a single payment method by id."""
        return await self.repo.get(id)

    async def get_payment_methods(
        self,
        skip: int = 0,
        limit: int = 100,
        user_id: Optional[UUID] = None,
    ) -> List[PaymentMethod]:
        """Return paginated payment methods, optionally filtered by user."""
        if user_id is not None:
            methods = await self.repo.get_for_user(user_id)
            methods.sort(key=lambda m: (not m.is_default, m.created_at), reverse=False)
            return methods[skip: skip + limit]
        return await self.repo.get_all(skip=skip, limit=limit)

    async def create_payment_method(self, obj_in: Any) -> PaymentMethod:
        """Create a payment method record and enforce single-default semantics."""
        data = _to_update_dict(obj_in)
        data["provider"] = _normalize_provider(data.get("provider"))
        if "user_id" not in data or data["user_id"] is None:
            raise ValidationError(message="user_id is required for payment method", field="user_id")

        first_method = await self._get_first_user_payment_method(data["user_id"])
        data["is_default"] = True if first_method is None else bool(data.get("is_default", False))

        db_obj = await self.repo.create(data)

        if db_obj.is_default:
            await self._unset_other_defaults(db_obj.user_id, db_obj.id)

        return db_obj

    async def update_payment_method(self, db_obj: PaymentMethod, obj_in: Any) -> PaymentMethod:
        """Update mutable fields and preserve default-payment-method invariants."""
        update_data = _to_update_dict(obj_in)
        if "provider" in update_data:
            update_data["provider"] = _normalize_provider(update_data.get("provider"))
        if "is_default" in update_data:
            update_data["is_default"] = bool(update_data["is_default"])

        updated = await self.repo.update(db_obj, update_data)

        if updated.is_default:
            await self._unset_other_defaults(updated.user_id, updated.id)
        else:
            first_method = await self._get_first_user_payment_method(updated.user_id)
            if first_method and first_method.id == updated.id:
                updated = await self.repo.update(updated, {"is_default": True})

        return updated

    async def delete_payment_method(self, id: UUID) -> Optional[PaymentMethod]:
        """Delete a payment method by id and preserve default fallback."""
        db_obj = await self.repo.get(id)
        if not db_obj:
            return None

        db_obj_copy = {c.name: getattr(db_obj, c.name) for c in db_obj.__table__.columns}
        deleted_was_default = bool(db_obj.is_default)
        owner_id = db_obj.user_id

        await self.repo.delete(db_obj)

        if deleted_was_default:
            replacement = await self._get_first_user_payment_method(owner_id)
            if replacement is not None:
                await self.repo.update(replacement, {"is_default": True})

        return PaymentMethod(**db_obj_copy)


