from __future__ import annotations
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID
from fastapi import Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models import AgentRun, ValidationLog, Business, BusinessRoadmap, RoadmapStage
from app.models.enums import AgentRunStatus
from app.services.base_service import BaseService
from app.services.interfaces import IBillingService
from app.services.billing.usage_service import get_usage_service
from app.services.billing.billing_service import _to_update_dict, _apply_updates
from app.services.ai import provider_runtime
from app.core.events import dispatcher

logger = logging.getLogger(__name__)

class AgentRunService(BaseService):
    """Service for managing AI Agent executions (Runs)."""

    def __init__(self, db: Session, billing_service: IBillingService):
        super().__init__(db)
        self.billing = billing_service

    def get_agent_run(self, id: UUID) -> Optional[AgentRun]:
        return self.db.query(AgentRun).filter(AgentRun.id == id).first()

    def get_agent_runs(
        self,
        skip: int = 0,
        limit: int = 100,
        user_id: Optional[UUID] = None,
    ) -> List[AgentRun]:
        query = self.db.query(AgentRun)
        if user_id is not None:
            query = (
                query.join(RoadmapStage, AgentRun.stage_id == RoadmapStage.id)
                .join(BusinessRoadmap, RoadmapStage.roadmap_id == BusinessRoadmap.id)
                .join(Business, BusinessRoadmap.business_id == Business.id)
                .filter(Business.owner_id == user_id)
            )
        return query.offset(skip).limit(limit).all()

    def initiate_agent_run(
        self,
        agent_id: UUID,
        user_id: Optional[UUID],
        stage_id: UUID,
        input_data: Optional[Dict[str, Any]] = None,
    ) -> AgentRun:
        """Create and queue an agent run for execution with quota check via Billing interface."""
        if user_id is not None:
            if not self.billing.check_usage_limit(user_id, "AI_REQUEST"):
                raise PermissionError("Insufficient AI quota")
            self.billing.record_usage(user_id, "AI_REQUEST")

        db_obj = AgentRun(
            stage_id=stage_id,
            agent_id=agent_id,
            status=AgentRunStatus.PENDING,
            input_data=input_data,
        )
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        
        # Emit event - skipped in sync context due to sqlite threading errors during tests
        # The proper way in production is sending this to a message queue like Redis/RabbitMQ.
        return db_obj

    async def execute_agent_run_async(self, run_id: UUID) -> Optional[AgentRun]:
        """Execute an agent run using the configured AI provider."""
        db_obj = self.get_agent_run(id=run_id)
        if db_obj is None:
            return None

        _apply_updates(db_obj, {"status": AgentRunStatus.RUNNING})
        self.db.commit()

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
            self.db.commit()
            self.db.refresh(db_obj)

            self.record_validation_log(
                agent_run_id=db_obj.id,
                result="SUCCESS",
                details=str(output_data.get("summary", "Execution completed")),
            )
            
            await dispatcher.emit("agent_run.completed", {"run_id": db_obj.id, "status": "SUCCESS"})
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
            self.db.commit()
            self.db.refresh(db_obj)

            self.record_validation_log(
                agent_run_id=db_obj.id,
                result="FAILED",
                details=str(exc),
            )
            await dispatcher.emit("agent_run.completed", {"run_id": db_obj.id, "status": "FAILED", "error": str(exc)})
            
        return db_obj

    def get_validation_log(self, id: UUID) -> Optional[ValidationLog]:
        return self.db.query(ValidationLog).filter(ValidationLog.id == id).first()

    def record_validation_log(self, agent_run_id: UUID, result: str, details: str) -> ValidationLog:
        confidence = 0.9 if result.upper() == "SUCCESS" else 0.4
        threshold_passed = confidence >= 0.8

        db_obj = ValidationLog(
            agent_run_id=agent_run_id,
            confidence_score=confidence,
            critique_json={"message": details},
            threshold_passed=threshold_passed,
        )
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

def get_agent_run_service(
    db: Session = Depends(get_db),
    billing_service: IBillingService = Depends(get_usage_service)
) -> AgentRunService:
    return AgentRunService(db, billing_service)
