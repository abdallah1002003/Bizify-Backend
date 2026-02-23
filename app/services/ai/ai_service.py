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
        input_data: Optional context data for the agent
        
    Returns:
        Created AgentRun with PENDING status
        
    Raises:
        PermissionError: If user has exhausted AI request quota
        SQLAlchemyError: If database operations fail
    """
    # Keep quota checks used by existing flow.
    if user_id is not None:
        if not billing_service.check_usage_limit(db, user_id, "AI_REQUEST"):
            raise PermissionError("Insufficient AI quota")
        billing_service.record_usage(db, user_id, "AI_REQUEST")

    _ = target_id
    _ = target_type

    db_obj = AgentRun(
        stage_id=stage_id,
        agent_id=agent_id,
        status=AgentRunStatus.PENDING,
        input_data=input_data,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_agent_run(db: Session, db_obj: AgentRun, obj_in: Any) -> AgentRun:
    _apply_updates(db_obj, _to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_agent_run(db: Session, id: UUID) -> Optional[AgentRun]:
    db_obj = get_agent_run(db, id=id)
    if not db_obj:
        return None

    db.delete(db_obj)
    db.commit()
    return db_obj


async def execute_agent_run_sync(db: Session, run_id: UUID) -> Optional[AgentRun]:
    """Execute an agent run synchronously using the configured AI provider.
    
    Transitions AgentRun through lifecycle (PENDING -> RUNNING -> SUCCESS/FAILED).
    Supports fallback to mock AI when the configured provider is unavailable.
    
    Args:
        db: Database session
        run_id: UUID of the AgentRun to execute
        
    Returns:
        Updated AgentRun with output_data, confidence_score, and final status
        None if AgentRun not found
        
    Raises:
        Exception: Caught and logged; run marked as FAILED with error details
    """
    db_obj = get_agent_run(db, id=run_id)
    if db_obj is None:
        return None

    _apply_updates(db_obj, {"status": AgentRunStatus.RUNNING})
    db.commit()

    stage = db_obj.stage
    stage_type = None
    if stage is not None and getattr(stage, "stage_type", None) is not None:
        stage_type = (
            stage.stage_type.value
            if hasattr(stage.stage_type, "value")
            else str(stage.stage_type)
        )

    try:
        output_data = await provider_runtime.run_agent_execution(
            db_obj.input_data,
            agent_name=db_obj.agent.name if db_obj.agent else "agent",
            stage_type=stage_type,
        )
        score = float(output_data.get("score", 0.92))

        _apply_updates(
            db_obj,
            {
                "output_data": output_data,
                "confidence_score": score,
                "status": AgentRunStatus.SUCCESS,
            },
        )
        db.commit()
        db.refresh(db_obj)

        record_validation_log(
            db,
            agent_run_id=db_obj.id,
            result="SUCCESS",
            details=str(output_data.get("summary", "Execution completed")),
        )
    except Exception as exc:
        logger.exception("Agent run execution failed for %s: %s", run_id, exc)
        _apply_updates(
            db_obj,
            {
                "status": AgentRunStatus.FAILED,
                "output_data": {"mode": "error", "error": str(exc)},
                "confidence_score": 0.0,
            },
        )
        db.commit()
        db.refresh(db_obj)

        record_validation_log(
            db,
            agent_run_id=db_obj.id,
            result="FAILED",
            details=str(exc),
        )
    return db_obj


# ----------------------------
# ValidationLog
# ----------------------------

def get_validation_log(db: Session, id: UUID) -> Optional[ValidationLog]:
    return db.query(ValidationLog).filter(ValidationLog.id == id).first()


def get_validation_logs(db: Session, skip: int = 0, limit: int = 100) -> List[ValidationLog]:
    return db.query(ValidationLog).offset(skip).limit(limit).all()


def record_validation_log(db: Session, agent_run_id: UUID, result: str, details: str) -> ValidationLog:
    confidence = 0.9 if result.upper() == "SUCCESS" else 0.4
    threshold_passed = confidence >= 0.8

    db_obj = ValidationLog(
        agent_run_id=agent_run_id,
        confidence_score=confidence,
        critique_json={"message": details},
        threshold_passed=threshold_passed,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_validation_log(db: Session, db_obj: ValidationLog, obj_in: Any) -> ValidationLog:
    _apply_updates(db_obj, _to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_validation_log(db: Session, id: UUID) -> Optional[ValidationLog]:
    db_obj = get_validation_log(db, id=id)
    if not db_obj:
        return None

    db.delete(db_obj)
    db.commit()
    return db_obj


# ----------------------------
# Embedding
# ----------------------------

def get_embedding(db: Session, id: UUID) -> Optional[Embedding]:
    return db.query(Embedding).filter(Embedding.id == id).first()


def get_embeddings(db: Session, skip: int = 0, limit: int = 100) -> List[Embedding]:
    return db.query(Embedding).offset(skip).limit(limit).all()


def create_embedding(db: Session, obj_in: Any) -> Embedding:
    db_obj = Embedding(**_to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_embedding(db: Session, db_obj: Embedding, obj_in: Any) -> Embedding:
    _apply_updates(db_obj, _to_update_dict(obj_in))
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_embedding(db: Session, id: UUID) -> Optional[Embedding]:
    db_obj = get_embedding(db, id=id)
    if not db_obj:
        return None

    db.delete(db_obj)
    db.commit()
    return db_obj


async def trigger_vectorization(
    db: Session,
    target_id: UUID,
    target_type: str,
    content: str,
    agent_id: Optional[UUID] = None,
) -> Optional[Embedding]:
    if len(content) < 10:
        return None

    business_id = target_id if target_type.upper() == "BUSINESS" else None
    vector = await provider_runtime.generate_embedding_vector(content)
    if vector is None:
        return None

    return create_embedding(
        db,
        {
            "business_id": business_id,
            "agent_id": agent_id,
            "content": content,
            "vector": vector,
        },
    )


def get_detailed_status() -> Dict[str, Any]:
    return {
        "module": "ai_service",
        "status": "operational",
        "timestamp": _utc_now().isoformat(),
    }


def reset_internal_state() -> None:
    logger.info("ai_service reset_internal_state called")
