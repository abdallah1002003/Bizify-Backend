from __future__ import annotations

import logging
from typing import Any, List, Optional
from uuid import UUID

<<<<<<< HEAD
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Subscription
from app.models.enums import SubscriptionStatus
from app.services.base_service import BaseService
from app.repositories.billing_repository import SubscriptionRepository, UsageRepository
from app.services.billing import plan_service
from app.core.metrics import subscriptions_active
from app.core.crud_utils import _utc_now, _to_update_dict
=======
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import Subscription, Usage
from app.models.enums import SubscriptionStatus
from app.db.database import get_async_db
from app.services.base_service import BaseService
from app.services.billing import plan_service
from app.core.metrics import subscriptions_active
from app.core.crud_utils import _utc_now, _to_update_dict, _apply_updates
>>>>>>> origin/main
from app.core.exceptions import (
    ResourceNotFoundError,
    DatabaseError,
    ValidationError,
    InvalidStateError,
)

logger = logging.getLogger(__name__)


class SubscriptionService(BaseService):
    """Service for managing user subscriptions and plan limit synchronization."""

<<<<<<< HEAD
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)
        self.sub_repo = SubscriptionRepository(db)
        self.usage_repo = UsageRepository(db)

=======
>>>>>>> origin/main
    _ALLOWED_TRANSITIONS: dict[SubscriptionStatus, set[SubscriptionStatus]] = {
        SubscriptionStatus.PENDING: {
            SubscriptionStatus.ACTIVE,
            SubscriptionStatus.CANCELED,
            SubscriptionStatus.EXPIRED,
        },
        SubscriptionStatus.ACTIVE: {
            SubscriptionStatus.CANCELED,
            SubscriptionStatus.EXPIRED,
        },
        SubscriptionStatus.CANCELED: set(),
        SubscriptionStatus.EXPIRED: set(),
    }

    async def _deactivate_other_active_subscriptions(
        self,
        *,
        user_id: UUID,
        keep_subscription_id: Optional[UUID] = None,
    ) -> None:
<<<<<<< HEAD
        active_rows = await self.sub_repo.get_for_user(user_id)
        active_rows = [r for r in active_rows if r.status == SubscriptionStatus.ACTIVE]
=======
        stmt = select(Subscription).where(
            Subscription.user_id == user_id,
            Subscription.status == SubscriptionStatus.ACTIVE,
        )
        result = await self.db.execute(stmt)
        active_rows = list(result.scalars().all())
>>>>>>> origin/main

        for row in active_rows:
            if keep_subscription_id and row.id == keep_subscription_id:
                continue
<<<<<<< HEAD
            await self.sub_repo.update(row, {
                "status": SubscriptionStatus.CANCELED,
                "end_date": _utc_now()
            })
=======
            row.status = SubscriptionStatus.CANCELED
            row.end_date = _utc_now()
            self.db.add(row)
>>>>>>> origin/main
            subscriptions_active.dec() # Metrics: Dec actively subscriptions count

    @classmethod
    def _coerce_status(cls, raw: Any) -> SubscriptionStatus:
        if isinstance(raw, SubscriptionStatus):
            return raw
        try:
            return SubscriptionStatus(str(raw).lower())
        except ValueError as exc:
            raise ValidationError(
                message=f"Invalid subscription status '{raw}'",
                field="status",
                details={"allowed": [s.value for s in SubscriptionStatus]},
            ) from exc

    @classmethod
    def _validate_status_transition(
        cls,
        current_status: SubscriptionStatus,
        new_status: SubscriptionStatus,
    ) -> None:
        if new_status == current_status:
            return
        allowed = cls._ALLOWED_TRANSITIONS.get(current_status, set())
        if new_status not in allowed:
            raise InvalidStateError(
                message=f"Invalid subscription status transition {current_status.value} -> {new_status.value}",
                current_state=current_status.value,
                required_state=" | ".join(sorted(s.value for s in allowed)) or "no transitions allowed",
            )

    @classmethod
    def _normalize_payload(
        cls,
        payload: dict[str, Any],
        *,
        is_update: bool = False,
    ) -> dict[str, Any]:
        data = dict(payload)
        if "status" in data and data["status"] is not None:
            data["status"] = cls._coerce_status(data["status"])
        elif not is_update:
            data["status"] = SubscriptionStatus.PENDING

        if not is_update and "start_date" not in data:
            data["start_date"] = _utc_now()

        return data

    async def _sync_plan_limits(self, subscription: Subscription, auto_commit: bool = True) -> None:
        """Synchronize usage limits from subscription plan to user's usage record."""
        try:
<<<<<<< HEAD
            plan = await plan_service.PlanService(self.db).get_plan(id=subscription.plan_id)
=======
            plan = await plan_service.get_plan(self.db, id=subscription.plan_id)
>>>>>>> origin/main
            if plan is None:
                logger.warning(f"Plan {subscription.plan_id} not found for subscription {subscription.id}")
                raise ResourceNotFoundError(
                    resource_type="Plan",
                    resource_id=str(subscription.plan_id),
                    details={"subscription_id": str(subscription.id)}
                )

            level = (plan.name or "").upper()
            limit_by_plan = {
                "FREE": 10,
                "PRO": 100,
                "ENTERPRISE": 1000,
            }
            limit = limit_by_plan.get(level, 10)

<<<<<<< HEAD
            usage = await self.usage_repo.get_by_user_and_resource(subscription.user_id, "AI_REQUEST")
            
            if usage is None:
                usage = await self.usage_repo.create({
                    "user_id": subscription.user_id,
                    "resource_type": "AI_REQUEST",
                    "used": 0,
                    "limit_value": limit,
                })
=======
            stmt = select(Usage).where(Usage.user_id == subscription.user_id, Usage.resource_type == "AI_REQUEST")
            result = await self.db.execute(stmt)
            usage = result.scalar_one_or_none()
            
            if usage is None:
                usage = Usage(
                    user_id=subscription.user_id,
                    resource_type="AI_REQUEST",
                    used=0,
                    limit_value=limit,
                )
                self.db.add(usage)
>>>>>>> origin/main
                logger.info(f"Created usage record for user {subscription.user_id} with limit {limit}")
            else:
                usage.limit_value = limit
                logger.info(f"Updated usage limit for user {subscription.user_id} to {limit}")

            if auto_commit:
<<<<<<< HEAD
                await self.sub_repo.commit()
            else:
                await self.sub_repo.flush()
        except ResourceNotFoundError:
            if auto_commit:
                await self.sub_repo.rollback()
=======
                await self.db.commit()
            else:
                await self.db.flush()
        except ResourceNotFoundError:
            if auto_commit:
                await self.db.rollback()
>>>>>>> origin/main
            raise
        except Exception as e:
            logger.error(f"Error syncing plan limits for subscription {subscription.id}: {e}")
            if auto_commit:
<<<<<<< HEAD
                await self.sub_repo.rollback()
=======
                await self.db.rollback()
>>>>>>> origin/main
            raise DatabaseError(
                operation="sync_plan_limits",
                entity_type="Subscription",
                original_error=str(e),
                details={"subscription_id": str(subscription.id)}
            ) from e

    async def get_subscription(self, id: UUID) -> Optional[Subscription]:
        """Retrieve a single subscription by its unique ID."""
<<<<<<< HEAD
        return await self.sub_repo.get(id)
=======
        return await self.db.get(Subscription, id)
>>>>>>> origin/main

    async def get_subscriptions(
        self,
        skip: int = 0,
        limit: int = 100,
        user_id: Optional[UUID] = None,
    ) -> List[Subscription]:
        """Retrieve subscriptions with pagination and optional user filtering."""
<<<<<<< HEAD
        all_subs = await self.sub_repo.get_all()
        if user_id is not None:
            filtered = [s for s in all_subs if s.user_id == user_id]
        else:
            filtered = all_subs
        filtered.sort(key=lambda s: s.created_at, reverse=True)
        return filtered[skip:skip+limit]

    async def get_active_subscription(self, user_id: UUID) -> Optional[Subscription]:
        """Retrieve the currently active subscription for a user."""
        return await self.sub_repo.get_active_for_user(user_id)
=======
        stmt = select(Subscription)
        if user_id is not None:
            stmt = stmt.where(Subscription.user_id == user_id)
        stmt = (
            stmt.order_by(Subscription.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_active_subscription(self, user_id: UUID) -> Optional[Subscription]:
        """Retrieve the currently active subscription for a user."""
        stmt = select(Subscription).where(Subscription.user_id == user_id, Subscription.status == SubscriptionStatus.ACTIVE)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
>>>>>>> origin/main

    async def create_subscription(self, obj_in: Any) -> Subscription:
        """Create a new subscription and synchronize plan usage limits."""
        try:
            data = self._normalize_payload(_to_update_dict(obj_in), is_update=False)
            
            # Validate required fields before database operation
            required_fields = {"user_id", "plan_id"}
            missing_fields = required_fields - set(data.keys())
            if missing_fields:
                missing_str = ", ".join(sorted(missing_fields))
                raise ValidationError(
                    message=f"Missing required fields: {missing_str}",
                    details={"missing_fields": list(missing_fields)}
                )
            
            # Verify plan exists before creating subscription
<<<<<<< HEAD
            plan = await plan_service.PlanService(self.db).get_plan(id=data["plan_id"])
=======
            plan = await plan_service.get_plan(self.db, id=data["plan_id"])
>>>>>>> origin/main
            if plan is None:
                raise ResourceNotFoundError(
                    resource_type="Plan",
                    resource_id=str(data["plan_id"]),
                    details={"operation": "create_subscription"}
                )

<<<<<<< HEAD
            if data.get("status") == SubscriptionStatus.ACTIVE:
                await self._deactivate_other_active_subscriptions(
                    user_id=data["user_id"],
                )
            db_obj = await self.sub_repo.create(data)

            await self._sync_plan_limits(db_obj, auto_commit=False)
            await self.sub_repo.commit()
=======
            db_obj = Subscription(**data)
            if db_obj.status == SubscriptionStatus.ACTIVE:
                await self._deactivate_other_active_subscriptions(
                    user_id=db_obj.user_id,
                    keep_subscription_id=db_obj.id,
                )
            self.db.add(db_obj)
            await self.db.flush()

            await self._sync_plan_limits(db_obj, auto_commit=False)
            await self.db.commit()
            await self.db.refresh(db_obj)
>>>>>>> origin/main
            
            if db_obj.status == SubscriptionStatus.ACTIVE:
                subscriptions_active.inc() # Metrics: Inc actively subscriptions count
                
            logger.info(f"Created subscription {db_obj.id} for user {db_obj.user_id} with plan {db_obj.plan_id}")
            return db_obj
        except (ValidationError, ResourceNotFoundError) as e:
<<<<<<< HEAD
            await self.sub_repo.rollback()
=======
            await self.db.rollback()
>>>>>>> origin/main
            code = getattr(e, "code", "UNKNOWN")
            logger.warning(f"Error {code} in create_subscription: {e}")
            raise
        except Exception as e:
<<<<<<< HEAD
            await self.sub_repo.rollback()
=======
            await self.db.rollback()
>>>>>>> origin/main
            logger.error(f"Transaction failed during create_subscription: {e}")
            raise DatabaseError(
                operation="create",
                entity_type="Subscription",
                original_error=str(e),
                details={"input_data": str(data) if 'data' in locals() else None}
            ) from e

    async def update_subscription(self, db_obj: Subscription, obj_in: Any) -> Subscription:
        """Update a subscription record and re-sync plan usage limits."""
        try:
            update_data = self._normalize_payload(_to_update_dict(obj_in), is_update=True)

            if "status" in update_data and update_data["status"] is not None:
                new_status = self._coerce_status(update_data["status"])
                self._validate_status_transition(db_obj.status, new_status)
                if new_status in {SubscriptionStatus.CANCELED, SubscriptionStatus.EXPIRED}:
                    update_data.setdefault("end_date", _utc_now())
                if new_status == SubscriptionStatus.ACTIVE:
                    await self._deactivate_other_active_subscriptions(
                        user_id=db_obj.user_id,
                        keep_subscription_id=db_obj.id,
                    )
                    subscriptions_active.inc()
                elif db_obj.status == SubscriptionStatus.ACTIVE and new_status != SubscriptionStatus.ACTIVE:
                    subscriptions_active.dec() # Status leaving ACTIVE state

<<<<<<< HEAD
            db_obj = await self.sub_repo.update(db_obj, update_data)
            await self.sub_repo.commit()
=======
            _apply_updates(db_obj, update_data)
            self.db.add(db_obj)
            await self.db.commit()
            await self.db.refresh(db_obj)
>>>>>>> origin/main

            await self._sync_plan_limits(db_obj)
            logger.info(f"Updated subscription {db_obj.id}")
            return db_obj
        except Exception as e:
<<<<<<< HEAD
            await self.sub_repo.rollback()
=======
            await self.db.rollback()
>>>>>>> origin/main
            logger.error(f"Error updating subscription {db_obj.id}: {e}")
            raise

    async def delete_subscription(self, id: UUID) -> Optional[Subscription]:
        """Delete a subscription by ID."""
        try:
            db_obj = await self.get_subscription(id=id)
            if not db_obj:
                logger.warning(f"Subscription {id} not found")
                return None

<<<<<<< HEAD
            deleted = await self.sub_repo.delete(db_obj)
            logger.info(f"Deleted subscription {id}")
            return deleted
        except Exception as e:
            await self.sub_repo.rollback()
=======
            await self.db.delete(db_obj)
            await self.db.commit()
            logger.info(f"Deleted subscription {id}")
            return db_obj
        except Exception as e:
            await self.db.rollback()
>>>>>>> origin/main
            logger.error(f"Error deleting subscription {id}: {e}")
            raise


<<<<<<< HEAD
async def get_subscription_service(db: AsyncSession) -> SubscriptionService:
=======
async def get_subscription_service(db: AsyncSession = Depends(get_async_db)) -> SubscriptionService:
>>>>>>> origin/main
    """Dependency provider for SubscriptionService."""
    return SubscriptionService(db)


<<<<<<< HEAD
=======
# ----------------------------
# Legacy Aliases
# ----------------------------

async def get_subscription(db: AsyncSession, id: UUID) -> Optional[Subscription]:
    return await SubscriptionService(db).get_subscription(id)


async def get_subscriptions(db: AsyncSession, skip: int = 0, limit: int = 100, user_id: Optional[UUID] = None) -> List[Subscription]:
    return await SubscriptionService(db).get_subscriptions(skip, limit, user_id)


async def get_active_subscription(db: AsyncSession, user_id: UUID) -> Optional[Subscription]:
    return await SubscriptionService(db).get_active_subscription(user_id)


async def create_subscription(db: AsyncSession, obj_in: Any) -> Subscription:
    return await SubscriptionService(db).create_subscription(obj_in)


async def update_subscription(db: AsyncSession, db_obj: Subscription, obj_in: Any) -> Subscription:
    return await SubscriptionService(db).update_subscription(db_obj, obj_in)


async def delete_subscription(db: AsyncSession, id: UUID) -> Optional[Subscription]:
    return await SubscriptionService(db).delete_subscription(id)
>>>>>>> origin/main
