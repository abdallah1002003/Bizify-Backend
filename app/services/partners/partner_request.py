# ruff: noqa
"""
Partner Request CRUD operations and status transitions.
"""
from __future__ import annotations

import logging
from typing import Any, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import PartnerRequest
from app.models.enums import RequestStatus

from app.services.base_service import BaseService

logger = logging.getLogger(__name__)


class PartnerRequestService(BaseService):
    """Refactored class-based access to partner requests."""
    def __init__(self, db: AsyncSession):
        super().__init__(db)
        from app.repositories.partner_repository import PartnerRequestRepository
        self.repo = PartnerRequestRepository(db)

    async def get_partner_request(self, id: UUID) -> Optional[PartnerRequest]:
        return await self.repo.get(id)

    async def get_partner_requests(self, skip: int = 0, limit: int = 100) -> List[PartnerRequest]:
        return await self.repo.get_all(skip=skip, limit=limit)

    async def submit_partner_request(self, **kwargs) -> PartnerRequest:
        data = dict(kwargs)
        if not data.get("status"):
            data["status"] = RequestStatus.PENDING
        return await self.repo.create(data)

    async def create_partner_request(self, obj_in: Any) -> PartnerRequest:
        return await self.repo.create(_to_update_dict(obj_in))

    async def update_partner_request(self, db_obj: PartnerRequest, obj_in: Any) -> PartnerRequest:
        return await self.repo.update(db_obj, _to_update_dict(obj_in))

    async def delete_partner_request(self, id: UUID) -> Optional[PartnerRequest]:
        return await self.repo.delete(id)

    async def transition_request_status(self, request_id: UUID, new_status: RequestStatus, performer_id: Optional[UUID] = None) -> Optional[PartnerRequest]:
        request = await self.get_partner_request(request_id)
        if not request:
            return None
        return await self.repo.update(request, {"status": new_status})

    async def accept_partner_request(self, request_id: UUID) -> Optional[PartnerRequest]:
        return await self.transition_request_status(request_id, RequestStatus.ACCEPTED)


def get_partner_request_service(db: AsyncSession) -> PartnerRequestService:
    """Helper to return an instance of PartnerRequestService."""
    return PartnerRequestService(db)


from app.core.crud_utils import _to_update_dict, _apply_updates

# ----------------------------
# PartnerRequest CRUD
# ----------------------------

async def get_partner_request(db: AsyncSession, id: UUID) -> Optional[PartnerRequest]:
    return await db.get(PartnerRequest, id)



async def get_partner_requests(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[PartnerRequest]:
    stmt = select(PartnerRequest).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())



async def submit_partner_request(
    db: AsyncSession,
    business_id: UUID,
    partner_id: UUID,
    request_type: Optional[str] = None,
    context: Optional[str] = None,
    requested_by: Optional[UUID] = None,
) -> PartnerRequest:
    _ = request_type
    _ = context
    db_obj = PartnerRequest(
        business_id=business_id,
        partner_id=partner_id,
        requested_by=requested_by,
        status=RequestStatus.PENDING,
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def create_partner_request(db: AsyncSession, obj_in: Any) -> PartnerRequest:
    data = _to_update_dict(obj_in)
    db_obj = PartnerRequest(**data)
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def update_partner_request(db: AsyncSession, db_obj: PartnerRequest, obj_in: Any) -> PartnerRequest:
    _apply_updates(db_obj, _to_update_dict(obj_in))
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def delete_partner_request(db: AsyncSession, id: UUID) -> Optional[PartnerRequest]:
    db_obj = await get_partner_request(db, id=id)
    if not db_obj:
        return None

    await db.delete(db_obj)
    await db.commit()
    return db_obj


async def transition_request_status(
    db: AsyncSession,
    request_id: UUID,
    new_status: RequestStatus,
    performer_id: Optional[UUID] = None,
) -> Optional[PartnerRequest]:
    _ = performer_id
    request = await get_partner_request(db, request_id)
    if request is None:
        return None

    request.status = new_status
    await db.commit()
    await db.refresh(request)
    return request


async def accept_partner_request(db: AsyncSession, request_id: UUID) -> Optional[PartnerRequest]:
    return await transition_request_status(db, request_id, RequestStatus.ACCEPTED)
