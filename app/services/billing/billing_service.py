"""Billing facade focused on domain usage operations.

This module intentionally delegates to `UsageService` so all quota rules
are centralized in one place.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.crud_utils import _utc_now
from app.models import Usage
from app.services.billing.usage_service import UsageService

logger = logging.getLogger(__name__)


async def check_usage_limit(db: AsyncSession, user_id: UUID, resource_type: str) -> bool:
    """Proxy to usage-domain quota checks."""
    return await UsageService(db).check_usage_limit(user_id, resource_type)


async def record_usage(db: AsyncSession, user_id: UUID, resource_type: str, quantity: int = 1) -> Usage:
    """Proxy to usage-domain consumption recording."""
    return await UsageService(db).record_usage(user_id, resource_type, quantity)


async def get_usage(db: AsyncSession, id: UUID) -> Optional[Usage]:
    return await UsageService(db).get_usage(id)


async def get_usages(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[UUID] = None,
) -> List[Usage]:
    return await UsageService(db).get_usages(skip=skip, limit=limit, user_id=user_id)


async def create_usage(db: AsyncSession, obj_in: Any) -> Usage:
    return await UsageService(db).create_usage(obj_in)


async def update_usage(db: AsyncSession, db_obj: Usage, obj_in: Any) -> Usage:
    return await UsageService(db).update_usage(db_obj, obj_in)


async def delete_usage(db: AsyncSession, id: UUID) -> Optional[Usage]:
    return await UsageService(db).delete_usage(id)


def get_detailed_status() -> Dict[str, Any]:
    return {
        "module": "billing_service",
        "status": "operational",
        "timestamp": _utc_now().isoformat(),
    }


def reset_internal_state() -> None:
    logger.info("billing_service reset_internal_state called")
