from __future__ import annotations
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_async_db
from app.models import AgentRun, ValidationLog
from app.models.enums import AgentRunStatus
from app.services.base_service import BaseService
from app.services.interfaces import IBillingService
from app.services.billing.usage_service import get_usage_service
from app.services.ai import provider_runtime
from app.core.events import dispatcher
from app.repositories.ai_repository import AgentRunRepository, ValidationLogRepository

logger = logging.getLogger(__name__)

class AgentRunService(BaseService):
    """Service for managing AI Agent executions (Runs)."""
    
    def __init__(self, db: AsyncSession, billing_service: IBillingService):
        super().__init__(db)
        self.billing = billing_service
        self.repo = AgentRunRepository(db)
        self.validation_repo = ValidationLogRepository(db)

    async def get_agent_run(self, id: UUID) -> Optional[AgentRun]:
        """Retrieve a single agent run by ID."""
        return await self.repo.get_with_stage_and_agent(id)

    async def get_agent_runs(
        self,
        skip: int = 0,
        limit: int = 100,
        user_id: Optional[UUID] = None,
    ) -> List[AgentRun]:
        """Retrieve paginated agent runs with optional user filtering."""
        if user_id is not None:
            return await self.repo.get_all_for_user(user_id, skip=skip, limit=limit)
        return await self.repo.get_all(skip=skip, limit=limit)

    async def initiate_agent_run(
        self,
        agent_id: UUID,
        user_id: Optional[UUID] = None,
        stage_id: Optional[UUID] = None,
        input_data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> AgentRun:
        """Create and queue an agent run for execution with quota check via Billing interface."""
        if user_id is not None:
            if not await self.billing.check_usage_limit(user_id, "AI_REQUEST"):
                raise PermissionError("Insufficient AI quota")
            await self.billing.record_usage(user_id, "AI_REQUEST")

        return await self.repo.create({
            "stage_id": stage_id,
            "agent_id": agent_id,
            "status": AgentRunStatus.PENDING,
            "input_data": input_data,
        })

    async def execute_agent_run_async(self, run_id: UUID) -> Optional[AgentRun]:
        """Execute an agent run using the configured AI provider."""
        db_obj = await self.get_agent_run(id=run_id)
        if db_obj is None:
            return None

        db_obj = await self.repo.update(db_obj, {"status": AgentRunStatus.RUNNING})

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

            db_obj = await self.repo.update(
                db_obj,
                {
                    "output_data": output_data,
                    "confidence_score": score,
                    "status": AgentRunStatus.SUCCESS,
                },
            )

            await self.record_validation_log(
                agent_run_id=db_obj.id,
                result="SUCCESS",
                details=str(output_data.get("summary", "Execution completed")),
            )
            
            await dispatcher.emit("agent_run.completed", {"run_id": db_obj.id, "status": "SUCCESS"})
        except Exception as exc:
            logger.exception("Agent run execution failed for %s: %s", run_id, exc)
            db_obj = await self.repo.update(
                db_obj,
                {
                    "status": AgentRunStatus.FAILED,
                    "output_data": {"mode": "error", "error": str(exc)},
                    "confidence_score": 0.0,
                },
            )

            await self.record_validation_log(
                agent_run_id=db_obj.id,
                result="FAILED",
                details=str(exc),
            )
            await dispatcher.emit("agent_run.completed", {"run_id": db_obj.id, "status": "FAILED", "error": str(exc)})
            
        return db_obj

    async def get_validation_log(self, id: UUID) -> Optional[ValidationLog]:
        """Retrieve a validation log by ID."""
        return await self.validation_repo.get(id)

    async def record_validation_log(self, agent_run_id: UUID, result: str, details: str) -> ValidationLog:
        """Create and store a validation log for an agent run."""
        confidence = 0.9 if result.upper() == "SUCCESS" else 0.4
        threshold_passed = confidence >= 0.8

        return await self.validation_repo.create({
            "agent_run_id": agent_run_id,
            "confidence_score": confidence,
            "critique_json": {"message": details},
            "threshold_passed": threshold_passed,
        })

async def get_agent_run_service(
    db: AsyncSession = Depends(get_async_db),
    billing_service: IBillingService = Depends(get_usage_service)
) -> AgentRunService:
    """Dependency provider for AgentRunService."""
    return AgentRunService(db, billing_service)
