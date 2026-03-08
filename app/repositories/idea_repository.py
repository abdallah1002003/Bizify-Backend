"""
Repository for Ideation domain models:
  - Idea
  - IdeaVersion
  - IdeaMetric
  - Experiment
  - IdeaAccess

# NOTE (Architecture - Afnan):
# Service → Repository → Database
# Ideation services should delegate all persistence to this repository.
"""
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ideation.idea import Idea, IdeaVersion, IdeaMetric, Experiment, IdeaAccess
from app.models.ideation.comparison import IdeaComparison, ComparisonItem, ComparisonMetric
from app.repositories.base_repository import GenericRepository


class IdeaRepository(GenericRepository[Idea]):
    """Repository for Idea model."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, Idea)

    async def get_with_relations(self, id: UUID) -> Optional[Idea]:
        """Retrieve an idea with owner and business eager-loaded."""
        stmt = (
            select(Idea)
            .options(selectinload(Idea.owner), selectinload(Idea.business))
            .where(Idea.id == id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_filtered(
        self,
        user_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Idea]:
        """Retrieve ideas accessible to the user (owned or shared)."""
        stmt = select(Idea).options(
            selectinload(Idea.owner),
            selectinload(Idea.business),
        )
        if user_id is not None:
            stmt = stmt.outerjoin(IdeaAccess).where(
                or_(Idea.owner_id == user_id, IdeaAccess.user_id == user_id)
            )
        stmt = stmt.distinct().offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())


class IdeaVersionRepository(GenericRepository[IdeaVersion]):
    """Repository for IdeaVersion model."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, IdeaVersion)

    async def get_for_idea(self, idea_id: UUID) -> List[IdeaVersion]:
        """Retrieve all versions for a given idea, newest first."""
        stmt = (
            select(IdeaVersion)
            .where(IdeaVersion.idea_id == idea_id)
            .order_by(IdeaVersion.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())


class IdeaMetricRepository(GenericRepository[IdeaMetric]):
    """Repository for IdeaMetric model."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, IdeaMetric)

    async def get_for_idea(self, idea_id: UUID) -> List[IdeaMetric]:
        """Retrieve all metrics for a given idea."""
        stmt = select(IdeaMetric).where(IdeaMetric.idea_id == idea_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_idea_and_name(self, idea_id: UUID, name: str) -> Optional[IdeaMetric]:
        """Retrieve a specific metric by idea and name."""
        stmt = select(IdeaMetric).where(
            IdeaMetric.idea_id == idea_id,
            IdeaMetric.name == name,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert(self, idea_id: UUID, name: str, value: float) -> IdeaMetric:
        """Create or update a metric for an idea."""
        existing = await self.get_by_idea_and_name(idea_id, name)
        if existing:
            return await self.update(existing, {"value": value})
        return await self.create({
            "idea_id": idea_id,
            "name": name,
            "value": value,
        })


class ExperimentRepository(GenericRepository[Experiment]):
    """Repository for Experiment model."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, Experiment)

    async def get_for_idea(self, idea_id: UUID) -> List[Experiment]:
        """Retrieve all experiments for a given idea."""
        stmt = select(Experiment).where(Experiment.idea_id == idea_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())


class IdeaAccessRepository(GenericRepository[IdeaAccess]):
    """Repository for IdeaAccess model."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, IdeaAccess)

    async def get_by_idea_and_user(
        self, idea_id: UUID, user_id: UUID
    ) -> Optional[IdeaAccess]:
        """Retrieve a specific access record for an idea/user pair."""
        stmt = select(IdeaAccess).where(
            IdeaAccess.idea_id == idea_id,
            IdeaAccess.user_id == user_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_safe(self, obj_in: dict, auto_commit: bool = True) -> Optional[IdeaAccess]:
        """Create an access record safely, returning None on IntegrityError (duplicate)."""
        from sqlalchemy.exc import IntegrityError
        try:
            return await self.create(obj_in, auto_commit=auto_commit)
        except IntegrityError:
            await self.db.rollback()
            return None

    async def upsert(
        self, idea_id: UUID, user_id: UUID, permissions: dict, auto_commit: bool = True
    ) -> IdeaAccess:
        """Create or update access permissions for a user on an idea."""
        existing = await self.get_by_idea_and_user(idea_id, user_id)
        if existing:
            return await self.update(existing, permissions, auto_commit=auto_commit)
        
        data = {"idea_id": idea_id, "user_id": user_id}
        data.update(permissions)
        return await self.create(data, auto_commit=auto_commit)

    async def get_for_idea(self, idea_id: UUID) -> List[IdeaAccess]:
        """Retrieve all access records for a given idea."""
        stmt = select(IdeaAccess).where(IdeaAccess.idea_id == idea_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_for_owner(self, owner_id: UUID, skip: int = 0, limit: int = 100) -> List[IdeaAccess]:
        from app.models.ideation.idea import Idea
        stmt = (
            select(IdeaAccess)
            .join(Idea, IdeaAccess.idea_id == Idea.id)
            .where(Idea.owner_id == owner_id)
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())


class IdeaComparisonRepository(GenericRepository[IdeaComparison]):
    """Repository for IdeaComparison model."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, IdeaComparison)

    async def get_for_user(self, user_id: UUID, skip: int = 0, limit: int = 100) -> List[IdeaComparison]:
        """Retrieve all comparisons belonging to a user."""
        stmt = (
            select(IdeaComparison)
            .where(IdeaComparison.user_id == user_id)
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    async def get_multi(self, *, skip: int = 0, limit: int = 100) -> List[IdeaComparison]:
        """Retrieve a paginated list of all comparisons."""
        stmt = select(IdeaComparison).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())



class ComparisonItemRepository(GenericRepository[ComparisonItem]):
    """Repository for ComparisonItem model."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, ComparisonItem)

    async def get_by_comparison_and_item(self, comparison_id: UUID, item_id: UUID) -> Optional[ComparisonItem]:
        """Retrieve a specific comparison item by comparison and item record ID."""
        stmt = select(ComparisonItem).where(
            ComparisonItem.comparison_id == comparison_id,
            ComparisonItem.id == item_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_comparison_and_idea(
        self, comparison_id: UUID, idea_id: UUID
    ) -> Optional[ComparisonItem]:
        """Retrieve a comparison item by unique (comparison_id, idea_id) pair."""
        stmt = select(ComparisonItem).where(
            ComparisonItem.comparison_id == comparison_id,
            ComparisonItem.idea_id == idea_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_safe(self, obj_in: dict, auto_commit: bool = True) -> Optional[ComparisonItem]:
        from sqlalchemy.exc import IntegrityError
        try:
            return await self.create(obj_in, auto_commit=auto_commit)
        except IntegrityError:
            await self.db.rollback()
            return None

    async def get_for_comparison(self, comparison_id: UUID) -> List[ComparisonItem]:
        """Retrieve all items in a comparison, ordered by rank."""
        stmt = (
            select(ComparisonItem)
            .where(ComparisonItem.comparison_id == comparison_id)
            .order_by(ComparisonItem.rank_index)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_last_rank(self, comparison_id: UUID) -> Optional[ComparisonItem]:
        """Retrieve the item with the highest rank_index in a comparison."""
        stmt = (
            select(ComparisonItem)
            .where(ComparisonItem.comparison_id == comparison_id)
            .order_by(ComparisonItem.rank_index.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()


class ComparisonMetricRepository(GenericRepository[ComparisonMetric]):
    """Repository for ComparisonMetric model."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, ComparisonMetric)

    async def get_by_comparison_and_metric(self, comparison_id: UUID, metric_name: str) -> Optional[ComparisonMetric]:
        """Retrieve a metric by comparison and name."""
        stmt = select(ComparisonMetric).where(
            ComparisonMetric.comparison_id == comparison_id,
            ComparisonMetric.metric_name == metric_name
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_safe(self, obj_in: dict, auto_commit: bool = True) -> Optional[ComparisonMetric]:
        """Create a comparison metric safely, returning None on IntegrityError (duplicate)."""
        from sqlalchemy.exc import IntegrityError
        try:
            return await self.create(obj_in, auto_commit=auto_commit)
        except IntegrityError:
            await self.db.rollback()
            return None

    async def upsert(
        self,
        comparison_id: UUID,
        metric_name: str,
        value: float = 1.0,
        auto_commit: bool = True,
    ) -> ComparisonMetric:
        """Create or update a comparison metric."""
        existing = await self.get_by_comparison_and_metric(comparison_id, metric_name)
        if existing:
            return await self.update(existing, {"value": value}, auto_commit=auto_commit)
        return await self.create({
            "comparison_id": comparison_id,
            "metric_name": metric_name,
            "value": value
        }, auto_commit=auto_commit)

    async def get_for_comparison(self, comparison_id: UUID) -> List[ComparisonMetric]:
        """Retrieve all metrics in a comparison."""
        stmt = select(ComparisonMetric).where(ComparisonMetric.comparison_id == comparison_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
