from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import Agent, AgentRun, Business, BusinessRoadmap, Embedding, RoadmapStage, ValidationLog
from app.services.ai import provider_runtime  # noqa: F401 — exposed for monkeypatching in tests
from app.services.ai.agent_run_service import AgentRunService
from app.services.ai.embedding_service import EmbeddingService
from app.services.billing.usage_service import UsageService
from app.core.crud_utils import _utc_now, _to_update_dict, _apply_updates

logger = logging.getLogger(__name__)


# ----------------------------
# Agent
# ----------------------------

async def get_agent(db: AsyncSession, id: UUID) -> Optional[Agent]:
    """Retrieve a single agent by ID."""
    stmt = select(Agent).where(Agent.id == id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_agents(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Agent]:
    """Retrieve paginated agents."""
    stmt = select(Agent).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_agent(db: AsyncSession, name: str, phase: str, config: Optional[dict] = None) -> Agent:
    """Create a new AI agent template."""
    _ = config
    db_obj = Agent(name=name, phase=phase)
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def update_agent(db: AsyncSession, db_obj: Agent, obj_in: Any) -> Agent:
    """Update an existing agent template."""
    _apply_updates(db_obj, _to_update_dict(obj_in))
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def delete_agent(db: AsyncSession, id: UUID) -> Optional[Agent]:
    """Delete an agent template by ID."""
    db_obj = await get_agent(db, id=id)
    if not db_obj:
        return None

    await db.delete(db_obj)
    await db.commit()
    return db_obj


# ----------------------------
# AgentRun
# ----------------------------

async def get_agent_run(db: AsyncSession, id: UUID) -> Optional[AgentRun]:
    """Retrieve a single agent run by ID."""
    from sqlalchemy.orm import joinedload
    stmt = (
        select(AgentRun)
        .options(
            joinedload(AgentRun.stage)
            .joinedload(RoadmapStage.roadmap)
            .joinedload(BusinessRoadmap.business)
        )
        .where(AgentRun.id == id)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_agent_runs(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[UUID] = None,
) -> List[AgentRun]:
    """Retrieve agent runs with optional user filtering."""
    stmt = select(AgentRun)
    if user_id is not None:
        stmt = (
            stmt.join(RoadmapStage, AgentRun.stage_id == RoadmapStage.id)
            .join(BusinessRoadmap, RoadmapStage.roadmap_id == BusinessRoadmap.id)
            .join(Business, BusinessRoadmap.business_id == Business.id)
            .where(Business.owner_id == user_id)
        )
    stmt = stmt.offset(skip).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def initiate_agent_run(
    db: AsyncSession,
    agent_id: UUID,
    user_id: Optional[UUID],
    target_id: Optional[UUID],
    target_type: Optional[str],
    stage_id: UUID,
    input_data: Optional[Dict[str, Any]] = None,
) -> AgentRun:
    """Create and queue an agent run for execution."""
    billing = UsageService(db)
    return await AgentRunService(db, billing).initiate_agent_run(
        agent_id=agent_id,
        user_id=user_id,
        stage_id=stage_id,
        input_data=input_data
    )


async def update_agent_run(db: AsyncSession, db_obj: AgentRun, obj_in: Any) -> AgentRun:
    """Apply partial updates to an existing AgentRun."""
    _apply_updates(db_obj, _to_update_dict(obj_in))
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def delete_agent_run(db: AsyncSession, id: UUID) -> Optional[AgentRun]:
    """Delete an agent run by ID."""
    db_obj = await get_agent_run(db, id)
    if not db_obj:
        return None
    await db.delete(db_obj)
    await db.commit()
    return db_obj


async def execute_agent_run_async(db: AsyncSession, run_id: UUID) -> Optional[AgentRun]:
    """Execute an agent run asynchronously."""
    billing = UsageService(db)
    return await AgentRunService(db, billing).execute_agent_run_async(run_id)


async def run_agent_in_background(db_factory: Any, run_id: UUID) -> None:
    """
    Helper for background tasks.
    
    Args:
        db_factory: A callable that returns an AsyncSession (e.g., async_session_maker)
        run_id: UUID of the agent run to execute
    """
    async with db_factory() as db:
        billing = UsageService(db)
        service = AgentRunService(db, billing)
        try:
            await service.execute_agent_run_async(run_id)
        except Exception:
            logger.exception("Failed to execute agent run in background")


# --- Validation Log Delegation ---

async def get_validation_log(db: AsyncSession, id: UUID) -> Optional[ValidationLog]:
    """Retrieve a validation log by ID."""
    billing = UsageService(db)
    return await AgentRunService(db, billing).get_validation_log(id)


async def record_validation_log(db: AsyncSession, agent_run_id: UUID, result: str, details: str) -> ValidationLog:
    """Create and store a validation log."""
    billing = UsageService(db)
    return await AgentRunService(db, billing).record_validation_log(agent_run_id, result, details)


async def get_validation_logs(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[ValidationLog]:
    """Retrieve paginated validation logs."""
    stmt = select(ValidationLog).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def update_validation_log(db: AsyncSession, db_obj: ValidationLog, obj_in: Any) -> ValidationLog:
    """Apply partial updates to an existing ValidationLog."""
    _apply_updates(db_obj, _to_update_dict(obj_in))
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def delete_validation_log(db: AsyncSession, id: UUID) -> Optional[ValidationLog]:
    """Delete a validation log by ID."""
    db_obj = await get_validation_log(db, id)
    if not db_obj:
        return None
    await db.delete(db_obj)
    await db.commit()
    return db_obj


# --- Embedding Delegation ---

async def get_embedding(db: AsyncSession, id: UUID) -> Optional[Embedding]:
    """Retrieve a single embedding by ID."""
    return await EmbeddingService(db).get_embedding(id)


async def get_embeddings(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Embedding]:
    """Retrieve paginated embeddings."""
    return await EmbeddingService(db).get_embeddings(skip, limit)


async def create_embedding(db: AsyncSession, obj_in: Any) -> Embedding:
    """Create a new embedding record."""
    return await EmbeddingService(db).create_embedding(obj_in)


async def update_embedding(db: AsyncSession, db_obj: Embedding, obj_in: Any) -> Embedding:
    """Apply partial updates to an existing Embedding."""
    _apply_updates(db_obj, _to_update_dict(obj_in))
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def delete_embedding(db: AsyncSession, id: UUID) -> Optional[Embedding]:
    """Delete an embedding by ID."""
    return await EmbeddingService(db).delete_embedding(id)


async def trigger_vectorization(
    db: AsyncSession,
    target_id: UUID,
    target_type: str,
    content: str,
    agent_id: Optional[UUID] = None,
) -> Optional[Embedding]:
    """Trigger vectorization for content."""
    return await EmbeddingService(db).trigger_vectorization(target_id, target_type, content, agent_id)


async def get_detailed_status() -> Dict[str, Any]:
    """Get detailed status information for the AI service."""
    return {
        "module": "ai_service",
        "status": "operational",
        "timestamp": _utc_now().isoformat(),
    }


async def reset_internal_state() -> None:
    """Reset internal state of the AI service."""
    logger.info("ai_service reset_internal_state called")
