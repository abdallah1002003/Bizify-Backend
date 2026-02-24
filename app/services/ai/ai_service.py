from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import Agent, AgentRun, Business, BusinessRoadmap, Embedding, RoadmapStage, ValidationLog
from app.models.enums import AgentRunStatus
from app.services.ai import provider_runtime
from app.services.billing import billing_service
from app.services.billing.billing_service import _utc_now, _to_update_dict, _apply_updates

logger = logging.getLogger(__name__)


# ----------------------------
# Agent
# ----------------------------

def get_agent(db: Session, id: UUID) -> Optional[Agent]:
    return db.query(Agent).filter(Agent.id == id).first()


def get_agents(db: Session, skip: int = 0, limit: int = 100) -> List[Agent]:
    return db.query(Agent).offset(skip).limit(limit).all()


def create_agent(db: Session, name: str, phase: str, config: Optional[dict] = None) -> Agent:
    """Create a new AI agent template.
    
    Args:
        db: Database session
        name: Human-readable agent name
        phase: Execution phase (e.g., 'discovery', 'validation')
        config: Optional agent configuration dict (reserved for future use)
        
    Returns:
        Created Agent instance
        
    Raises:
        SQLAlchemyError: If database commit fails
    """
    _ = config
    db_obj = Agent(name=name, phase=phase)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_agent(db: Session, db_obj: Agent, obj_in: Any) -> Agent:
    _apply_updates(db_obj, _to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_agent(db: Session, id: UUID) -> Optional[Agent]:
    db_obj = get_agent(db, id=id)
    if not db_obj:
        return None

    db.delete(db_obj)
    db.commit()
    return db_obj


# ----------------------------
# AgentRun
# ----------------------------

def get_agent_run(db: Session, id: UUID) -> Optional[AgentRun]:
    return db.query(AgentRun).filter(AgentRun.id == id).first()


def get_agent_runs(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[UUID] = None,
) -> List[AgentRun]:
    """Retrieve agent runs with optional user filtering.
    
    Args:
        db: Database session
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        user_id: Optional user ID to filter runs by business ownership
        
    Returns:
        List of AgentRun instances, filtered by user if provided
    """
    query = db.query(AgentRun)
    if user_id is not None:
        query = (
            query.join(RoadmapStage, AgentRun.stage_id == RoadmapStage.id)
            .join(BusinessRoadmap, RoadmapStage.roadmap_id == BusinessRoadmap.id)
            .join(Business, BusinessRoadmap.business_id == Business.id)
            .filter(Business.owner_id == user_id)
        )
    return query.offset(skip).limit(limit).all()


def initiate_agent_run(
    db: Session,
    agent_id: UUID,
    user_id: Optional[UUID],
    target_id: Optional[UUID],
    target_type: Optional[str],
    stage_id: UUID,
    input_data: Optional[Dict[str, Any]] = None,
) -> AgentRun:
    """Create and queue an agent run for execution.
    
    Validates user quota and prepares the agent to process a specific business roadmap stage.
    
    Args:
        db: Database session
        agent_id: UUID of the Agent to execute
        user_id: UUID of the requesting user (for quota tracking)
        target_id: Optional target object ID
        target_type: Optional target object type
        stage_id: UUID of the RoadmapStage to process
    """
    billing = UsageService(db)
    return AgentRunService(db, billing).initiate_agent_run(
        agent_id=agent_id,
        user_id=user_id,
        stage_id=stage_id,
        input_data=input_data
    )


def update_agent_run(db: Session, db_obj: AgentRun, obj_in: Any) -> AgentRun:
    # Adding missing generic update if needed, but AgentRunService should probably have it
    from app.services.billing.billing_service import _to_update_dict, _apply_updates
    _apply_updates(db_obj, _to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_agent_run(db: Session, id: UUID) -> Optional[AgentRun]:
    db_obj = get_agent_run(db, id)
    if not db_obj:
        return None
    db.delete(db_obj)
    db.commit()
    return db_obj


async def execute_agent_run_async(db: Session, run_id: UUID) -> Optional[AgentRun]:
    billing = UsageService(db)
    return await AgentRunService(db, billing).execute_agent_run_async(run_id)


# Backward-compat alias (old name was misleading — function is async, not sync)
execute_agent_run_sync = execute_agent_run_async


def run_agent_in_background(db: Session, run_id: UUID) -> None:
    """Helper for background tasks."""
    import asyncio
    billing = UsageService(db)
    service = AgentRunService(db, billing)
    try:
        # Since this is likely called from a background task (synchronous context in FastAPI)
        # we might need to handle the loop correctly or it might already be in an async thread.
        # But FastAPI BackgroundTasks usually runs in a worker thread.
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        if loop.is_running():
            asyncio.ensure_future(service.execute_agent_run_async(run_id))
        else:
            loop.run_until_complete(service.execute_agent_run_async(run_id))
    finally:
        db.close()


# --- Validation Log Delegation ---

def get_validation_log(db: Session, id: UUID) -> Optional[ValidationLog]:
    billing = UsageService(db)
    return AgentRunService(db, billing).get_validation_log(id)


def record_validation_log(db: Session, agent_run_id: UUID, result: str, details: str) -> ValidationLog:
    billing = UsageService(db)
    return AgentRunService(db, billing).record_validation_log(agent_run_id, result, details)


# --- Embedding Delegation ---

def get_embedding(db: Session, id: UUID) -> Optional[Embedding]:
    return EmbeddingService(db).get_embedding(id)


def get_embeddings(db: Session, skip: int = 0, limit: int = 100) -> List[Embedding]:
    return EmbeddingService(db).get_embeddings(skip, limit)


def create_embedding(db: Session, obj_in: Any) -> Embedding:
    return EmbeddingService(db).create_embedding(obj_in)


def delete_embedding(db: Session, id: UUID) -> Optional[Embedding]:
    return EmbeddingService(db).delete_embedding(id)


async def trigger_vectorization(
    db: Session,
    target_id: UUID,
    target_type: str,
    content: str,
    agent_id: Optional[UUID] = None,
) -> Optional[Embedding]:
    return await EmbeddingService(db).trigger_vectorization(target_id, target_type, content, agent_id)


def get_detailed_status() -> Dict[str, Any]:
    from app.services.billing.billing_service import _utc_now
    return {
        "module": "ai_service",
        "status": "operational",
        "timestamp": _utc_now().isoformat(),
    }


def reset_internal_state() -> None:
    logger.info("ai_service reset_internal_state called")
