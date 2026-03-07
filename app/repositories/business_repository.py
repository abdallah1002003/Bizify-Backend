"""
Repository for Business domain models:
  - Business
  - BusinessCollaborator
  - BusinessInvite
  - BusinessInviteIdea
  - BusinessRoadmap
  - RoadmapStage

# NOTE (Architecture - Afnan):
# Service → Repository → Database
# Business services should delegate all persistence to this repository.
"""
from typing import List, Optional, cast
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.business.business import (
    Business,
    BusinessCollaborator,
    BusinessInvite,
    BusinessInviteIdea,
    BusinessRoadmap,
    RoadmapStage,
)
from app.models.enums import CollaboratorRole
from app.repositories.base_repository import GenericRepository


class BusinessRepository(GenericRepository[Business]):
    """Repository for Business model."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, Business)

    async def get_with_relations(self, id: UUID) -> Optional[Business]:
        """Retrieve a business with owner, collaborators, and roadmap eager-loaded."""
        stmt = (
            select(Business)
            .options(
                selectinload(Business.owner),
                selectinload(Business.collaborators).selectinload(BusinessCollaborator.user),
                selectinload(Business.roadmap),
            )
            .where(Business.id == id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_safe(self, obj_in: dict, auto_commit: bool = True) -> Optional[Business]:
        """Create a business safely, returning None on IntegrityError (duplicate idea_id)."""
        from sqlalchemy.exc import IntegrityError
        try:
            return await self.create(obj_in, auto_commit=auto_commit)
        except IntegrityError:
            await self.db.rollback()
            return None


    async def get_all_filtered(
        self,
        owner_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Business]:
        """Retrieve businesses, optionally filtered by owner, with relations loaded."""
        stmt = select(Business).options(
            selectinload(Business.owner),
            selectinload(Business.collaborators).selectinload(BusinessCollaborator.user),
            selectinload(Business.roadmap),
        )
        if owner_id is not None:
            stmt = stmt.where(Business.owner_id == owner_id)
        stmt = stmt.offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())


class BusinessCollaboratorRepository(GenericRepository[BusinessCollaborator]):
    """Repository for BusinessCollaborator model."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, BusinessCollaborator)

    async def get(self, id: UUID) -> Optional[BusinessCollaborator]:
        """Retrieve a collaborator by ID."""
        stmt = select(BusinessCollaborator).where(BusinessCollaborator.id == id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_safe(self, obj_in: dict, auto_commit: bool = True) -> Optional[BusinessCollaborator]:
        """Create a collaborator safely, returning None on IntegrityError (duplicate)."""
        from sqlalchemy.exc import IntegrityError
        try:
            return await self.create(obj_in, auto_commit=auto_commit)
        except IntegrityError:
            await self.db.rollback()
            return None

    async def get_for_business(self, business_id: UUID) -> List[BusinessCollaborator]:
        """Retrieve all collaborators for a given business."""
        stmt = select(BusinessCollaborator).where(BusinessCollaborator.business_id == business_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_business_and_user(
        self, business_id: UUID, user_id: UUID
    ) -> Optional[BusinessCollaborator]:
        """Retrieve a specific collaborator by business and user IDs."""
        stmt = select(BusinessCollaborator).where(
            and_(
                BusinessCollaborator.business_id == business_id,
                BusinessCollaborator.user_id == user_id,
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert(
        self, business_id: UUID, user_id: UUID, role: CollaboratorRole, auto_commit: bool = True
    ) -> BusinessCollaborator:
        """Create or update a collaborator record (upsert by business+user)."""
        existing = await self.get_by_business_and_user(business_id, user_id)
        if existing is not None:
            return await self.update(existing, {"role": role}, auto_commit=auto_commit)

        return await self.create({
            "business_id": business_id,
            "user_id": user_id,
            "role": role
        }, auto_commit=auto_commit)

    async def delete_by_business_and_user(
        self, business_id: UUID, user_id: UUID
    ) -> Optional[BusinessCollaborator]:
        """Delete a collaborator by business and user IDs."""
        obj = await self.get_by_business_and_user(business_id, user_id)
        if obj:
            await self.db.delete(obj)
            await self.db.commit()
        return obj


class BusinessInviteRepository(GenericRepository[BusinessInvite]):
    """Repository for BusinessInvite model."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, BusinessInvite)

    async def get_by_token(self, token: str) -> Optional[BusinessInvite]:
        """Retrieve an invite by its token."""
        stmt = select(BusinessInvite).where(BusinessInvite.token == token)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_safe(self, obj_in: dict, auto_commit: bool = True) -> Optional[BusinessInvite]:
        """Create an invite safely, returning None on IntegrityError (duplicate token)."""
        from sqlalchemy.exc import IntegrityError
        try:
            return await self.create(obj_in, auto_commit=auto_commit)
        except IntegrityError:
            await self.db.rollback()
            return None


    async def get_for_business(self, business_id: UUID) -> List[BusinessInvite]:
        """Retrieve all invites for a business."""
        stmt = select(BusinessInvite).where(BusinessInvite.business_id == business_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())


class BusinessInviteIdeaRepository(GenericRepository[BusinessInviteIdea]):
    """Repository for BusinessInviteIdea junction model."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, BusinessInviteIdea)

    async def get_by_invite_and_idea(self, invite_id: UUID, idea_id: UUID) -> Optional[BusinessInviteIdea]:
        """Retrieve a specific junction record."""
        stmt = select(BusinessInviteIdea).where(
            BusinessInviteIdea.invite_id == invite_id,
            BusinessInviteIdea.idea_id == idea_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_safe(self, obj_in: dict, auto_commit: bool = True) -> Optional[BusinessInviteIdea]:
        """Create an invite-idea link safely, returning None on IntegrityError (duplicate)."""
        from sqlalchemy.exc import IntegrityError
        try:
            return await self.create(obj_in, auto_commit=auto_commit)
        except IntegrityError:
            await self.db.rollback()
            return None

    async def upsert(self, invite_id: UUID, idea_id: UUID, auto_commit: bool = True) -> BusinessInviteIdea:
        """Ensure an idea is linked to an invite without duplicates."""
        existing = await self.get_by_invite_and_idea(invite_id, idea_id)
        if existing:
            return existing
        return await self.create({
            "invite_id": invite_id,
            "idea_id": idea_id
        }, auto_commit=auto_commit)


class BusinessRoadmapRepository(GenericRepository[BusinessRoadmap]):
    """Repository for BusinessRoadmap model."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, BusinessRoadmap)

    async def get_by_business(self, business_id: UUID) -> Optional[BusinessRoadmap]:
        """Retrieve the roadmap for a given business."""
        stmt = select(BusinessRoadmap).where(BusinessRoadmap.business_id == business_id)
        result = await self.db.execute(stmt)
        return cast(Optional[BusinessRoadmap], result.scalar_one_or_none())

    async def create_safe(self, obj_in: dict, auto_commit: bool = True) -> Optional[BusinessRoadmap]:
        """Create a roadmap safely, returning None on IntegrityError (duplicate business_id)."""
        from sqlalchemy.exc import IntegrityError
        try:
            return await self.create(obj_in, auto_commit=auto_commit)
        except IntegrityError:
            await self.db.rollback()
            return None


class RoadmapStageRepository(GenericRepository[RoadmapStage]):
    """Repository for RoadmapStage model."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, RoadmapStage)

    async def get_with_relations(self, id: UUID) -> Optional[RoadmapStage]:
        """Retrieve a stage with its roadmap and parent business eager-loaded."""
        stmt = (
            select(RoadmapStage)
            .options(joinedload(RoadmapStage.roadmap).joinedload(BusinessRoadmap.business))
            .where(RoadmapStage.id == id)
        )
        result = await self.db.execute(stmt)
        return cast(Optional[RoadmapStage], result.scalar_one_or_none())

    async def get_for_roadmap(
        self,
        roadmap_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[RoadmapStage]:
        """Retrieve all stages for a roadmap, ordered by index."""
        stmt = (
            select(RoadmapStage)
            .where(RoadmapStage.roadmap_id == roadmap_id)
            .order_by(RoadmapStage.order_index.asc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_order_index(
        self, roadmap_id: UUID, order_index: int
    ) -> Optional[RoadmapStage]:
        """Retrieve a stage by its position in the roadmap."""
        stmt = select(RoadmapStage).where(
            and_(
                RoadmapStage.roadmap_id == roadmap_id,
                RoadmapStage.order_index == order_index,
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_for_roadmap_unordered(self, roadmap_id: UUID) -> List[RoadmapStage]:
        """Retrieve all stages for completion calculation."""
        stmt = select(RoadmapStage).where(RoadmapStage.roadmap_id == roadmap_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
