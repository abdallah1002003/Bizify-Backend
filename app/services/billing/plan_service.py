"""
Billing Plan CRUD operations.
"""
from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any, List, Optional
from uuid import UUID

<<<<<<< HEAD
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Plan
from app.services.base_service import BaseService
from app.core.crud_utils import _to_update_dict
from app.core.exceptions import ValidationError
from app.repositories.billing_repository import PlanRepository
=======
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models import Plan
from app.db.database import get_async_db
from app.services.base_service import BaseService
from app.core.crud_utils import _to_update_dict, _apply_updates
from app.core.exceptions import ValidationError
>>>>>>> origin/main

logger = logging.getLogger(__name__)


class PlanService(BaseService):
    """Service for managing Billing Plans."""

<<<<<<< HEAD
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)
        self.repo = PlanRepository(db)

=======
>>>>>>> origin/main
    _DEFAULT_LIMITS_BY_PLAN = {
        "FREE": 10,
        "PRO": 100,
        "ENTERPRISE": 1000,
    }
    _VALID_BILLING_CYCLES = {"month", "year"}

    @classmethod
    def _normalize_billing_cycle(cls, raw_cycle: str | None) -> str:
        cycle = (raw_cycle or "month").strip().lower()
        aliases = {
            "monthly": "month",
            "month": "month",
            "yearly": "year",
            "annual": "year",
            "year": "year",
        }
        normalized = aliases.get(cycle, cycle)
        if normalized not in cls._VALID_BILLING_CYCLES:
            raise ValidationError(
                message=f"Unsupported billing_cycle '{raw_cycle}'",
                field="billing_cycle",
                details={"allowed": sorted(cls._VALID_BILLING_CYCLES)},
            )
        return normalized

    @classmethod
    def _derive_default_ai_runs(cls, plan_name: str) -> int:
        return cls._DEFAULT_LIMITS_BY_PLAN.get(plan_name.upper(), 10)

    @classmethod
    def _normalize_payload(
        cls,
        payload: dict[str, Any],
        *,
        is_update: bool = False,
    ) -> dict[str, Any]:
        data = dict(payload)

        if "name" in data and data["name"] is not None:
            normalized_name = str(data["name"]).strip()
            if not normalized_name:
                raise ValidationError(
                    message="Plan name cannot be empty",
                    field="name",
                )
            data["name"] = normalized_name

        if "price" in data and data["price"] is not None:
            try:
                price = Decimal(str(data["price"]))
            except Exception as e:
                raise ValidationError(
                    message="Invalid price format",
                    field="price",
                ) from e
            if price < 0:
                raise ValidationError(
                    message="Plan price must be non-negative",
                    field="price",
                )
            data["price"] = price

        if not is_update or "billing_cycle" in data:
            data["billing_cycle"] = cls._normalize_billing_cycle(
                str(data.get("billing_cycle", "month"))
            )

        if not is_update or "features_json" in data or "name" in data:
            features_raw = data.get("features_json")
            if features_raw is None:
                features: dict[str, Any] = {}
            elif isinstance(features_raw, dict):
                features = dict(features_raw)
            else:
                raise ValidationError(
                    message="features_json must be a dictionary",
                    field="features_json",
                )

            if "ai_runs" not in features:
                name_for_limit = str(data.get("name") or "FREE")
                features["ai_runs"] = cls._derive_default_ai_runs(name_for_limit)
            data["features_json"] = features

        return data

    async def get_plan(self, id: UUID) -> Optional[Plan]:
        """Return a single plan by id."""
<<<<<<< HEAD
        return await self.repo.get(id)

    async def get_plans(self, skip: int = 0, limit: int = 100) -> List[Plan]:
        """Return paginated plan records in business-friendly display order."""
        return await self.repo.get_ordered(skip=skip, limit=limit)

    async def count_plans(self) -> int:
        """Return total count of plans."""
        return await self.repo.count()
=======
        return await self.db.get(Plan, id)

    async def get_plans(self, skip: int = 0, limit: int = 100) -> List[Plan]:
        """Return paginated plan records in business-friendly display order."""
        stmt = (
            select(Plan)
            .order_by(Plan.is_active.desc(), Plan.price.asc(), Plan.name.asc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_plans(self) -> int:
        """Return total count of plans."""
        stmt = select(func.count()).select_from(Plan)
        result = await self.db.execute(stmt)
        return int(result.scalar() or 0)
>>>>>>> origin/main

    async def create_plan(self, obj_in: Any) -> Plan:
        """Create a new billing plan with normalized commercial rules."""
        data = self._normalize_payload(_to_update_dict(obj_in), is_update=False)

<<<<<<< HEAD
        # Use get_by_name_for_update to acquire a lock and prevent concurrent
        # creation of plans with the same name. If another transaction is creating
        # the same plan, it will block here; if someone created it already, we'll
        # detect it and raise ValidationError.
        existing = await self.repo.get_by_name_for_update(data["name"])
        if existing is not None:
=======
        existing_stmt = select(Plan).where(func.lower(Plan.name) == data["name"].lower())
        existing_result = await self.db.execute(existing_stmt)
        if existing_result.scalar_one_or_none() is not None:
>>>>>>> origin/main
            raise ValidationError(
                message=f"Plan with name '{data['name']}' already exists",
                field="name",
            )

<<<<<<< HEAD
        db_obj = await self.repo.create(data)
=======
        db_obj = Plan(**data)
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
>>>>>>> origin/main
        return db_obj

    async def update_plan(self, db_obj: Plan, obj_in: Any) -> Plan:
        """Update mutable fields on an existing plan with validation."""
        update_data = self._normalize_payload(_to_update_dict(obj_in), is_update=True)

        if "name" in update_data:
<<<<<<< HEAD
            if await self.repo.get_by_name_excluding(update_data["name"], db_obj.id) is not None:
=======
            existing_stmt = select(Plan).where(
                func.lower(Plan.name) == update_data["name"].lower(),
                Plan.id != db_obj.id,
            )
            existing_result = await self.db.execute(existing_stmt)
            if existing_result.scalar_one_or_none() is not None:
>>>>>>> origin/main
                raise ValidationError(
                    message=f"Plan with name '{update_data['name']}' already exists",
                    field="name",
                )

<<<<<<< HEAD
        db_obj = await self.repo.update(db_obj, update_data)
=======
        _apply_updates(db_obj, update_data)
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
>>>>>>> origin/main
        return db_obj

    async def delete_plan(self, id: UUID) -> Optional[Plan]:
        """Delete a plan by id and return the deleted record."""
        db_obj = await self.get_plan(id=id)
<<<<<<< HEAD
        if db_obj:
            return await self.repo.delete(db_obj)
        return None


async def get_plan_service(db: AsyncSession) -> PlanService:
=======
        if not db_obj:
            return None

        await self.db.delete(db_obj)
        await self.db.commit()
        return db_obj


async def get_plan_service(db: AsyncSession = Depends(get_async_db)) -> PlanService:
>>>>>>> origin/main
    """Dependency provider for PlanService."""
    return PlanService(db)


<<<<<<< HEAD
=======
# ----------------------------
# Legacy Aliases
# ----------------------------

async def get_plan(db: AsyncSession, id: UUID) -> Optional[Plan]:
    return await PlanService(db).get_plan(id)


async def get_plans(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Plan]:
    return await PlanService(db).get_plans(skip, limit)


async def create_plan(db: AsyncSession, obj_in: Any) -> Plan:
    return await PlanService(db).create_plan(obj_in)


async def update_plan(db: AsyncSession, db_obj: Plan, obj_in: Any) -> Plan:
    return await PlanService(db).update_plan(db_obj, obj_in)


async def delete_plan(db: AsyncSession, id: UUID) -> Optional[Plan]:
    return await PlanService(db).delete_plan(id)
>>>>>>> origin/main
