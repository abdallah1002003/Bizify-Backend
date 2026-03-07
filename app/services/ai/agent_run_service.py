from __future__ import annotations
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID
<<<<<<< HEAD
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import AgentRun, ValidationLog
from app.models.enums import AgentRunStatus
from app.services.base_service import BaseService
from app.services.interfaces import IBillingService
from app.services.billing.usage_service import UsageService
from app.services.ai import provider_runtime
from app.core.events import dispatcher
from app.repositories.ai_repository import AgentRunRepository, ValidationLogRepository
=======
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.database import get_async_db
from app.models import AgentRun, ValidationLog, Business, BusinessRoadmap, RoadmapStage
from app.models.enums import AgentRunStatus
from app.services.base_service import BaseService
from app.services.interfaces import IBillingService
from app.services.billing.usage_service import get_usage_service
from app.core.crud_utils import _apply_updates
from app.services.ai import provider_runtime
from app.core.events import dispatcher
>>>>>>> origin/main

logger = logging.getLogger(__name__)

class AgentRunService(BaseService):
    """Service for managing AI Agent executions (Runs)."""
<<<<<<< HEAD
    def __init__(self, db: AsyncSession, billing_service: IBillingService):
        super().__init__(db)
        self.billing = billing_service
        self.repo = AgentRunRepository(db)
        self.validation_repo = ValidationLogRepository(db)

    async def get_agent_run(self, id: UUID) -> Optional[AgentRun]:
        """Retrieve a single agent run by ID."""
        return await self.repo.get_with_stage_and_agent(id)
=======
    db: AsyncSession

    def __init__(self, db: AsyncSession, billing_service: IBillingService):
        super().__init__(db)
        self.billing = billing_service

    async def get_agent_run(self, id: UUID) -> Optional[AgentRun]:
        """Retrieve a single agent run by ID."""
        from sqlalchemy.orm import selectinload
        stmt = select(AgentRun).where(AgentRun.id == id).options(
            selectinload(AgentRun.stage),
            selectinload(AgentRun.agent)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
>>>>>>> origin/main

    async def get_agent_runs(
        self,
        skip: int = 0,
        limit: int = 100,
        user_id: Optional[UUID] = None,
    ) -> List[AgentRun]:
        """Retrieve paginated agent runs with optional user filtering."""
<<<<<<< HEAD
        if user_id is not None:
            return await self.repo.get_all_for_user(user_id=user_id, skip=skip, limit=limit)
        return await self.repo.get_all(skip=skip, limit=limit)
=======
        stmt = select(AgentRun)
        if user_id is not None:
            stmt = (
                stmt.join(RoadmapStage, AgentRun.stage_id == RoadmapStage.id)
                .join(BusinessRoadmap, RoadmapStage.roadmap_id == BusinessRoadmap.id)
                .join(Business, BusinessRoadmap.business_id == Business.id)
                .where(Business.owner_id == user_id)
            )
        stmt = stmt.offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
>>>>>>> origin/main

    async def initiate_agent_run(
        self,
        agent_id: UUID,
        user_id: Optional[UUID],
        stage_id: UUID,
        input_data: Optional[Dict[str, Any]] = None,
    ) -> AgentRun:
        """Create and queue an agent run for execution with quota check via Billing interface."""
        if user_id is not None:
            # check_usage_limit and record_usage are async
            if not await self.billing.check_usage_limit(user_id, "AI_REQUEST"):
                raise PermissionError("Insufficient AI quota")
            await self.billing.record_usage(user_id, "AI_REQUEST")

<<<<<<< HEAD
        db_obj = await self.repo.create({
            "stage_id": stage_id,
            "agent_id": agent_id,
            "status": AgentRunStatus.PENDING,
            "input_data": input_data,
        })
=======
        db_obj = AgentRun(
            stage_id=stage_id,
            agent_id=agent_id,
            status=AgentRunStatus.PENDING,
            input_data=input_data,
        )
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        
>>>>>>> origin/main
        return db_obj

    async def execute_agent_run_async(self, run_id: UUID) -> Optional[AgentRun]:
        """Execute an agent run using the configured AI provider."""
        # Use await get_agent_run
        db_obj = await self.get_agent_run(id=run_id)
        if db_obj is None:
            return None

        # Correctly await relationship if needed, but here we assume eager or already loaded if possible.
        # However, with AsyncSession, we often need to ensure it.
        # For simplicity, we assume the fields we need are simple or we reload them.
        
<<<<<<< HEAD
        db_obj = await self.repo.update(db_obj, {"status": AgentRunStatus.RUNNING})
=======
        _apply_updates(db_obj, {"status": AgentRunStatus.RUNNING})
        await self.db.commit()
>>>>>>> origin/main

        stage = db_obj.stage
        stage_type = None
        if stage is not None and getattr(stage, "stage_type", None) is not None:
            stage_type = (
                stage.stage_type.value
                if hasattr(stage.stage_type, "value")
                else str(stage.stage_type)
            )

        try:
<<<<<<< HEAD
            ai_provider = provider_runtime.AIProviderService(self.db)
            output_data = await ai_provider.run_agent_execution(
=======
            output_data = await provider_runtime.run_agent_execution(
>>>>>>> origin/main
                db_obj.input_data,
                agent_name=db_obj.agent.name if db_obj.agent else "agent",
                stage_type=stage_type,
            )
            score = float(output_data.get("score", 0.92))

<<<<<<< HEAD
            db_obj = await self.repo.update(
=======
            _apply_updates(
>>>>>>> origin/main
                db_obj,
                {
                    "output_data": output_data,
                    "confidence_score": score,
                    "status": AgentRunStatus.SUCCESS,
                },
            )
<<<<<<< HEAD
=======
            await self.db.commit()
            await self.db.refresh(db_obj)
>>>>>>> origin/main

            await self.record_validation_log(
                agent_run_id=db_obj.id,
                result="SUCCESS",
                details=str(output_data.get("summary", "Execution completed")),
            )
            
            await dispatcher.emit("agent_run.completed", {"run_id": db_obj.id, "status": "SUCCESS"})
        except Exception as exc:
            logger.exception("Agent run execution failed for %s: %s", run_id, exc)
<<<<<<< HEAD
            db_obj = await self.repo.update(
=======
            _apply_updates(
>>>>>>> origin/main
                db_obj,
                {
                    "status": AgentRunStatus.FAILED,
                    "output_data": {"mode": "error", "error": str(exc)},
                    "confidence_score": 0.0,
                },
            )
<<<<<<< HEAD
=======
            await self.db.commit()
            await self.db.refresh(db_obj)
>>>>>>> origin/main

            await self.record_validation_log(
                agent_run_id=db_obj.id,
                result="FAILED",
                details=str(exc),
            )
            await dispatcher.emit("agent_run.completed", {"run_id": db_obj.id, "status": "FAILED", "error": str(exc)})
            
        return db_obj

    async def get_validation_log(self, id: UUID) -> Optional[ValidationLog]:
        """Retrieve a validation log by ID."""
<<<<<<< HEAD
        return await self.validation_repo.get(id)
=======
        stmt = select(ValidationLog).where(ValidationLog.id == id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
>>>>>>> origin/main

    async def record_validation_log(self, agent_run_id: UUID, result: str, details: str) -> ValidationLog:
        """Create and store a validation log for an agent run."""
        confidence = 0.9 if result.upper() == "SUCCESS" else 0.4
        threshold_passed = confidence >= 0.8

<<<<<<< HEAD
        db_obj = await self.validation_repo.create({
            "agent_run_id": agent_run_id,
            "confidence_score": confidence,
            "critique_json": {"message": details},
            "threshold_passed": threshold_passed,
        })
        return db_obj

async def get_agent_run_service(
    db: AsyncSession,
    billing_service: Optional[IBillingService] = None,
) -> AgentRunService:
    """Dependency provider for AgentRunService."""
    billing_service = billing_service or UsageService(db)
=======
        db_obj = ValidationLog(
            agent_run_id=agent_run_id,
            confidence_score=confidence,
            critique_json={"message": details},
            threshold_passed=threshold_passed,
        )
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

async def get_agent_run_service(
    db: AsyncSession = Depends(get_async_db),
    billing_service: IBillingService = Depends(get_usage_service)
) -> AgentRunService:
    """Dependency provider for AgentRunService."""
>>>>>>> origin/main
    return AgentRunService(db, billing_service)
