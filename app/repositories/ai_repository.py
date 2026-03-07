"""
Repository for AI domain models:
  - Agent
  - AgentRun
  - ValidationLog
  - Embedding

# NOTE (Architecture - Afnan):
# Service → Repository → Database
# AI services should delegate all persistence to this repository.
"""
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai.agent import Agent, AgentRun, ValidationLog, Embedding
from app.repositories.base_repository import GenericRepository


class AgentRepository(GenericRepository[Agent]):
    """Repository for Agent model."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, Agent)

    async def get_by_name(self, name: str) -> Optional[Agent]:
        """Retrieve an agent by name."""
        stmt = select(Agent).where(Agent.name == name)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()


class AgentRunRepository(GenericRepository[AgentRun]):
    """Repository for AgentRun model."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, AgentRun)

    async def get_for_agent(
        self, agent_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[AgentRun]:
        """Retrieve all runs for a given agent."""
        stmt = (
            select(AgentRun)
            .where(AgentRun.agent_id == agent_id)
            .order_by(AgentRun.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_for_stage(
        self, stage_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[AgentRun]:
        """Retrieve all runs for a given roadmap stage."""
        stmt = (
            select(AgentRun)
            .where(AgentRun.stage_id == stage_id)
            .order_by(AgentRun.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_with_stage_and_business(self, id: UUID) -> Optional[AgentRun]:
        from sqlalchemy.orm import joinedload
        from app.models.business.business import RoadmapStage, BusinessRoadmap
        stmt = (
            select(AgentRun)
            .options(
                joinedload(AgentRun.stage)
                .joinedload(RoadmapStage.roadmap)
                .joinedload(BusinessRoadmap.business)
            )
            .where(AgentRun.id == id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
        
    async def get_with_stage_and_agent(self, id: UUID) -> Optional[AgentRun]:
        from sqlalchemy.orm import selectinload
        stmt = select(AgentRun).where(AgentRun.id == id).options(
            selectinload(AgentRun.stage),
            selectinload(AgentRun.agent)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_for_user(
        self, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[AgentRun]:
        from app.models.business.business import Business
        from app.models.business.business import RoadmapStage, BusinessRoadmap
        stmt = (
            select(AgentRun)
            .join(RoadmapStage, AgentRun.stage_id == RoadmapStage.id)
            .join(BusinessRoadmap, RoadmapStage.roadmap_id == BusinessRoadmap.id)
            .join(Business, BusinessRoadmap.business_id == Business.id)
            .where(Business.owner_id == user_id)
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())



class ValidationLogRepository(GenericRepository[ValidationLog]):
    """Repository for ValidationLog model."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, ValidationLog)

    async def get_for_run(
        self, agent_run_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[ValidationLog]:
        """Retrieve validation logs for a specific agent run."""
        stmt = (
            select(ValidationLog)
            .where(ValidationLog.agent_run_id == agent_run_id)
            .order_by(ValidationLog.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())


class EmbeddingRepository(GenericRepository[Embedding]):
    """Repository for Embedding model."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, Embedding)

    async def get_for_business(
        self, business_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Embedding]:
        """Retrieve embeddings for a specific business."""
        stmt = (
            select(Embedding)
            .where(Embedding.business_id == business_id)
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
