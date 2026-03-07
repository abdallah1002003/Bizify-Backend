from __future__ import annotations

import logging
from typing import Any, List, Optional
from uuid import UUID

<<<<<<< HEAD
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Usage
from app.services.base_service import BaseService
from app.core.crud_utils import _to_update_dict
from app.core.exceptions import ValidationError, InvalidStateError
from app.repositories.billing_repository import UsageRepository
=======
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import Usage
from app.db.database import get_async_db
from app.services.base_service import BaseService
from app.core.crud_utils import _to_update_dict, _apply_updates
from app.core.exceptions import ValidationError, InvalidStateError
>>>>>>> origin/main

logger = logging.getLogger(__name__)


class UsageService(BaseService):
    """Service for managing resource usage tracking and enforcement."""

<<<<<<< HEAD
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)
        self.repo = UsageRepository(db)

=======
>>>>>>> origin/main
    @staticmethod
    def _normalize_resource_type(resource_type: str) -> str:
        normalized = resource_type.strip().upper()
        if not normalized:
            raise ValidationError(
                message="resource_type cannot be empty",
                field="resource_type",
            )
        return normalized

    @staticmethod
    def _validate_quantity(quantity: int) -> int:
        if quantity < 0:
            raise ValidationError(
                message=f"quantity must be non-negative, got {quantity}",
                field="quantity",
            )
        return quantity

    async def _get_usage_by_resource(
        self,
        *,
        user_id: UUID,
        resource_type: str,
        for_update: bool = False,
    ) -> Optional[Usage]:
<<<<<<< HEAD
        return await self.repo.get_by_resource(user_id=user_id, resource_type=resource_type, for_update=for_update)
=======
        stmt = select(Usage).where(
            Usage.user_id == user_id,
            Usage.resource_type == resource_type,
        )
        if for_update:
            stmt = stmt.with_for_update()
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
>>>>>>> origin/main

    async def check_usage_limit(self, user_id: UUID, resource_type: str) -> bool:
        """Return whether the user's usage remains below the configured limit."""
        normalized_resource = self._normalize_resource_type(resource_type)
        usage = await self._get_usage_by_resource(
            user_id=user_id,
            resource_type=normalized_resource,
            for_update=False,
        )
        
        if usage is None or usage.limit_value is None:
            return True
        return usage.used < usage.limit_value

    async def record_usage(self, user_id: UUID, resource_type: str, quantity: int = 1) -> Usage:
        """Atomically increment usage for a resource, creating the row when needed."""
        normalized_resource = self._normalize_resource_type(resource_type)
        delta = self._validate_quantity(quantity)
        usage = await self._get_usage_by_resource(
            user_id=user_id,
            resource_type=normalized_resource,
            for_update=True,
        )
        
        if usage is None:
<<<<<<< HEAD
            usage = await self.repo.create({
                "user_id": user_id, 
                "resource_type": normalized_resource, 
                "used": 0
            })
=======
            usage = Usage(user_id=user_id, resource_type=normalized_resource, used=0)
            self.db.add(usage)
>>>>>>> origin/main

        if usage.limit_value is not None and usage.used + delta > usage.limit_value:
            raise InvalidStateError(
                message="Usage quota exceeded",
                current_state=f"used={usage.used}",
                required_state=f"<= limit_value={usage.limit_value}",
                details={
                    "user_id": str(user_id),
                    "resource_type": normalized_resource,
                    "quantity": delta,
                },
            )

<<<<<<< HEAD
        usage = await self.repo.update(usage, {"used": usage.used + delta})
=======
        usage.used += delta
        await self.db.commit()
        await self.db.refresh(usage)
>>>>>>> origin/main
        return usage

    async def get_usage(self, id: UUID) -> Optional[Usage]:
        """Return a single usage row by id."""
<<<<<<< HEAD
        return await self.repo.get(id)
=======
        return await self.db.get(Usage, id)
>>>>>>> origin/main

    async def get_usages(
        self,
        skip: int = 0,
        limit: int = 100,
        user_id: Optional[UUID] = None,
    ) -> List[Usage]:
        """Return paginated usage rows, optionally filtered by user."""
<<<<<<< HEAD
        if user_id is not None:
            rows = await self.repo.get_for_user(user_id)
            return rows[skip: skip + limit]
        return await self.repo.get_all(skip=skip, limit=limit)
=======
        stmt = select(Usage)
        if user_id is not None:
            stmt = stmt.where(Usage.user_id == user_id)
        stmt = (
            stmt.order_by(Usage.updated_at.desc(), Usage.used.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
>>>>>>> origin/main

    async def create_usage(self, obj_in: Any) -> Usage:
        """Create or update a usage row for a given (user_id, resource_type) pair."""
        data = _to_update_dict(obj_in)
        user_id = data.get("user_id")
        resource_type = data.get("resource_type")

        if user_id is None or resource_type is None:
            raise ValidationError(
                message="user_id and resource_type are required",
                details={"required_fields": ["user_id", "resource_type"]},
            )

        data["resource_type"] = self._normalize_resource_type(str(resource_type))
        if "used" in data and data["used"] is not None:
            data["used"] = self._validate_quantity(int(data["used"]))
        if "limit_value" in data and data["limit_value"] is not None and int(data["limit_value"]) < 0:
            raise ValidationError(
                message="limit_value must be non-negative",
                field="limit_value",
            )

<<<<<<< HEAD
        # Use the repository's upsert logic to handle the unique constraint
        return await self.repo.upsert_usage(data)
=======
        existing = await self._get_usage_by_resource(
            user_id=user_id,
            resource_type=data["resource_type"],
            for_update=True,
        )
        if existing is not None:
            # Merge supplied fields onto the existing row instead of inserting a duplicate
            _apply_updates(existing, data)
            await self.db.commit()
            await self.db.refresh(existing)
            return existing

        db_obj = Usage(**data)
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj
>>>>>>> origin/main

    async def update_usage(self, db_obj: Usage, obj_in: Any) -> Usage:
        """Update mutable fields on a usage row."""
        update_data = _to_update_dict(obj_in)
        if "resource_type" in update_data and update_data["resource_type"] is not None:
            update_data["resource_type"] = self._normalize_resource_type(str(update_data["resource_type"]))
        if "used" in update_data and update_data["used"] is not None:
            update_data["used"] = self._validate_quantity(int(update_data["used"]))
        if "limit_value" in update_data and update_data["limit_value"] is not None and int(update_data["limit_value"]) < 0:
            raise ValidationError(
                message="limit_value must be non-negative",
                field="limit_value",
            )

<<<<<<< HEAD
        return await self.repo.update(db_obj, update_data)

    async def delete_usage(self, id: UUID) -> Optional[Usage]:
        """Delete a usage row by id."""
        return await self.repo.delete(id)


async def get_usage_service(db: AsyncSession) -> UsageService:
=======
        _apply_updates(db_obj, update_data)
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def delete_usage(self, id: UUID) -> Optional[Usage]:
        """Delete a usage row by id."""
        db_obj = await self.get_usage(id=id)
        if not db_obj:
            return None

        await self.db.delete(db_obj)
        await self.db.commit()
        return db_obj


async def get_usage_service(db: AsyncSession = Depends(get_async_db)) -> UsageService:
>>>>>>> origin/main
    """Dependency provider for UsageService."""
    return UsageService(db)


<<<<<<< HEAD
=======
# ----------------------------
# Legacy Aliases
# ----------------------------

async def check_usage_limit(db: AsyncSession, user_id: UUID, resource_type: str) -> bool:
    return await UsageService(db).check_usage_limit(user_id, resource_type)


async def record_usage(db: AsyncSession, user_id: UUID, resource_type: str, quantity: int = 1) -> Usage:
    return await UsageService(db).record_usage(user_id, resource_type, quantity)


async def get_usage(db: AsyncSession, id: UUID) -> Optional[Usage]:
    return await UsageService(db).get_usage(id)


async def get_usages(db: AsyncSession, skip: int = 0, limit: int = 100, user_id: Optional[UUID] = None) -> List[Usage]:
    return await UsageService(db).get_usages(skip, limit, user_id)


async def create_usage(db: AsyncSession, obj_in: Any) -> Usage:
    return await UsageService(db).create_usage(obj_in)


async def update_usage(db: AsyncSession, db_obj: Usage, obj_in: Any) -> Usage:
    return await UsageService(db).update_usage(db_obj, obj_in)


async def delete_usage(db: AsyncSession, id: UUID) -> Optional[Usage]:
    return await UsageService(db).delete_usage(id)
>>>>>>> origin/main
