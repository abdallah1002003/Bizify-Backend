"""
Repository for Partners domain models:
  - PartnerProfile
  - PartnerRequest

# NOTE (Architecture - Afnan):
# Service → Repository → Database
# Partner services should delegate all persistence to this repository.
"""
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.partners.partner import PartnerProfile, PartnerRequest
from app.repositories.base_repository import GenericRepository


class PartnerProfileRepository(GenericRepository[PartnerProfile]):
    """Repository for PartnerProfile model."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, PartnerProfile)

    async def get_by_user(self, user_id: UUID) -> Optional[PartnerProfile]:
        """Retrieve the partner profile for a given user."""
        stmt = select(PartnerProfile).where(PartnerProfile.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_safe(self, obj_in: dict, auto_commit: bool = True) -> Optional[PartnerProfile]:
        """Create a partner profile safely, returning None on IntegrityError (duplicate)."""
        from sqlalchemy.exc import IntegrityError
        try:
            return await self.create(obj_in, auto_commit=auto_commit)
        except IntegrityError:
            await self.db.rollback()
            return None

    async def get_approved(self, skip: int = 0, limit: int = 100) -> List[PartnerProfile]:
        """Retrieve all approved partner profiles."""
        from app.models.enums import ApprovalStatus
        stmt = (
            select(PartnerProfile)
            .where(PartnerProfile.approval_status == ApprovalStatus.APPROVED)
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_approved_by_type(
        self, partner_type: Optional[str] = None, limit: int = 500
    ) -> List[PartnerProfile]:
        """Retrieve approved partner profiles, optionally filtered by type."""
        from app.models.enums import ApprovalStatus
        stmt = select(PartnerProfile).where(PartnerProfile.approval_status == ApprovalStatus.APPROVED)
        
        if partner_type is not None:
            stmt = stmt.where(PartnerProfile.partner_type == partner_type)
            
        stmt = stmt.limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())


class PartnerRequestRepository(GenericRepository[PartnerRequest]):
    """Repository for PartnerRequest model."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, PartnerRequest)

    async def get_for_business(self, business_id: UUID) -> List[PartnerRequest]:
        """Retrieve all partner requests for a given business."""
        stmt = select(PartnerRequest).where(PartnerRequest.business_id == business_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_for_partner(self, partner_id: UUID) -> List[PartnerRequest]:
        """Retrieve all requests targeting a given partner profile."""
        stmt = select(PartnerRequest).where(PartnerRequest.partner_id == partner_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_business_and_partner(
        self, business_id: UUID, partner_id: UUID
    ) -> Optional[PartnerRequest]:
        """Retrieve a specific request by business and partner IDs."""
        stmt = select(PartnerRequest).where(
            PartnerRequest.business_id == business_id,
            PartnerRequest.partner_id == partner_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_safe(self, obj_in: dict, auto_commit: bool = True) -> Optional[PartnerRequest]:
        """Create a partner request safely, returning None on IntegrityError (duplicate)."""
        from sqlalchemy.exc import IntegrityError
        try:
            return await self.create(obj_in, auto_commit=auto_commit)
        except IntegrityError:
            await self.db.rollback()
            return None

    async def upsert_request(self, obj_in: dict) -> PartnerRequest:
        """Create or update a partner request for a business/partner pair."""
        existing = await self.get_by_business_and_partner(
            obj_in["business_id"], obj_in["partner_id"]
        )
        if existing:
            return await self.update(existing, obj_in)
        return await self.create(obj_in)
