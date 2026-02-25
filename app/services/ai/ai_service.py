from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import Agent, AgentRun, Business, BusinessRoadmap, Embedding, RoadmapStage, ValidationLog
from app.services.ai.agent_run_service import AgentRunService
from app.services.ai.embedding_service import EmbeddingService
from app.services.billing.usage_service import UsageService
from app.core.crud_utils import _utc_now, _to_update_dict, _apply_updates

logger = logging.getLogger(__name__)


# ----------------------------
# Agent
# ----------------------------

def get_agent(db: Session, id: UUID) -> Optional[Agent]:
    return db.query(Agent).filter(Agent.id == id).first()  # type: ignore[no-any-return]


def get_agents(db: Session, skip: int = 0, limit: int = 100) -> List[Agent]:
    return db.query(Agent).offset(skip).limit(limit).all()  # type: ignore[no-any-return]


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
    return db.query(AgentRun).filter(AgentRun.id == id).first()  # type: ignore[no-any-return]


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
    return query.offset(skip).limit(limit).all()  # type: ignore[no-any-return]


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
    """Apply partial updates to an existing AgentRun."""
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





def run_agent_in_background(db: Session, run_id: UUID) -> None:
    """Helper for background tasks."""
    import asyncio
    billing = UsageService(db)
    service = AgentRunService(db, billing)
    try:
        # Background tasks in FastAPI run in a separate thread.
        # Using asyncio.run is safer here since it's a one-off task.
        asyncio.run(service.execute_agent_run_async(run_id))
    except Exception:
        logger.exception("Failed to execute agent run in background")
    finally:
        db.close()


# --- Validation Log Delegation ---

def get_validation_log(db: Session, id: UUID) -> Optional[ValidationLog]:
    billing = UsageService(db)
    return AgentRunService(db, billing).get_validation_log(id)


def record_validation_log(db: Session, agent_run_id: UUID, result: str, details: str) -> ValidationLog:
    billing = UsageService(db)
    return AgentRunService(db, billing).record_validation_log(agent_run_id, result, details)


def get_validation_logs(db: Session, skip: int = 0, limit: int = 100) -> List[ValidationLog]:
    return db.query(ValidationLog).offset(skip).limit(limit).all()  # type: ignore[no-any-return]


def update_validation_log(db: Session, db_obj: ValidationLog, obj_in: Any) -> ValidationLog:
    """Apply partial updates to an existing ValidationLog."""
    _apply_updates(db_obj, _to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_validation_log(db: Session, id: UUID) -> Optional[ValidationLog]:
    db_obj = get_validation_log(db, id)
    if not db_obj:
        return None
    db.delete(db_obj)
    db.commit()
    return db_obj


# --- Embedding Delegation ---

def get_embedding(db: Session, id: UUID) -> Optional[Embedding]:
    return EmbeddingService(db).get_embedding(id)


def get_embeddings(db: Session, skip: int = 0, limit: int = 100) -> List[Embedding]:
    return EmbeddingService(db).get_embeddings(skip, limit)


def create_embedding(db: Session, obj_in: Any) -> Embedding:
    return EmbeddingService(db).create_embedding(obj_in)


def update_embedding(db: Session, db_obj: Embedding, obj_in: Any) -> Embedding:
    """Apply partial updates to an existing Embedding."""
    _apply_updates(db_obj, _to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


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
    """Get detailed status information for the AI service."""
    return {
        "module": "ai_service",
        "status": "operational",
        "timestamp": _utc_now().isoformat(),
    }


def reset_internal_state() -> None:
    logger.info("ai_service reset_internal_state called")
