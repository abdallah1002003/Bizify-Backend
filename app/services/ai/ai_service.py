from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import Agent, AgentRun, Embedding, ValidationLog
from app.models.enums import AgentRunStatus
from app.services.billing import billing_service

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _to_update_dict(obj_in: Any) -> Dict[str, Any]:
    if obj_in is None:
        return {}
    if hasattr(obj_in, "model_dump"):
        return obj_in.model_dump(exclude_unset=True)
    return dict(obj_in)


def _apply_updates(db_obj: Any, update_data: Dict[str, Any]) -> Any:
    for field, value in update_data.items():
        if hasattr(db_obj, field):
            setattr(db_obj, field, value)
    return db_obj


# ----------------------------
# Agent
# ----------------------------

def get_agent(db: Session, id: UUID) -> Optional[Agent]:
    return db.query(Agent).filter(Agent.id == id).first()


def get_agents(db: Session, skip: int = 0, limit: int = 100) -> List[Agent]:
    return db.query(Agent).offset(skip).limit(limit).all()


def create_agent(db: Session, name: str, phase: str, config: Optional[dict] = None) -> Agent:
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


def get_agent_runs(db: Session, skip: int = 0, limit: int = 100) -> List[AgentRun]:
    return db.query(AgentRun).offset(skip).limit(limit).all()


def initiate_agent_run(
    db: Session,
    agent_id: UUID,
    user_id: Optional[UUID],
    target_id: Optional[UUID],
    target_type: Optional[str],
    stage_id: UUID,
    input_data: Optional[Dict[str, Any]] = None,
) -> AgentRun:
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


def execute_agent_run_sync(db: Session, run_id: UUID) -> Optional[AgentRun]:
    """
    WARNING FOR AI EXPERT:
    This is currently MOCK LOGIC used for testing the flow.
    You must replace this with actual AI execution logic.
    
    Here are two ways to do this correctly:
    
    Example 1: Using FastAPI BackgroundTasks (Recommended for simple setups)
    -------------------------------------------------------------------------
    from fastapi import BackgroundTasks
    
    def trigger_agent(db: Session, run_id: UUID, background_tasks: BackgroundTasks):
        run = initiate_agent_run(...)
        background_tasks.add_task(execute_agent_run_actual, db, run.id)
        return run

    def execute_agent_run_actual(db: Session, run_id: UUID):
        # 1. Mark as RUNNING
        # 2. Call your actual AI pipeline (LangChain, OpenAI API, etc)
        # 3. Save output & mark SUCCESS or FAILED
    
    Example 2: Using Async Celery/Redis Queue (Recommended for Production)
    -------------------------------------------------------------------------
    @celery_app.task
    def execute_agent_task(run_id_str: str):
        with SessionLocal() as db:
            run = db.query(AgentRun).get(UUID(run_id_str))
            run.status = AgentRunStatus.RUNNING
            db.commit()
            
            try:
                # Call true AI logic
                output = ai_pipeline.run(run.input_data)
                run.output_data = output
                run.status = AgentRunStatus.SUCCESS
            except Exception as e:
                run.status = AgentRunStatus.FAILED
                
            db.commit()
    """
    db_obj = get_agent_run(db, id=run_id)
    if db_obj is None:
        return None

    db_obj.status = AgentRunStatus.RUNNING
    db.commit()

    db_obj.output_data = {"summary": "Execution completed", "score": 0.92}
    db_obj.confidence_score = 0.92
    db_obj.status = AgentRunStatus.SUCCESS
    db.commit()
    db.refresh(db_obj)

    record_validation_log(
        db,
        agent_run_id=db_obj.id,
        result="SUCCESS",
        details="Execution completed",
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


def trigger_vectorization(
    db: Session,
    target_id: UUID,
    target_type: str,
    content: str,
    agent_id: Optional[UUID] = None,
) -> Optional[Embedding]:
    if len(content) < 10:
        return None

    business_id = target_id if target_type.upper() == "BUSINESS" else None
    vector = [0.123] * 1536
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
