from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Agent, AgentRun, Embedding, ValidationLog
from app.services.ai import provider_runtime  # noqa: F401 — exposed for monkeypatching in tests
from app.services.ai.agent_run_service import AgentRunService
from app.services.ai.embedding_service import EmbeddingService
from app.services.billing.usage_service import UsageService
from app.core.crud_utils import _utc_now, _to_update_dict
from app.services.base_service import BaseService
from app.repositories.ai_repository import AgentRepository, ValidationLogRepository, EmbeddingRepository, AgentRunRepository

logger = logging.getLogger(__name__)


class AIService(BaseService):
    """AI service facade providing access to Agent, AgentRun, Embedding and ValidationLog operations."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)
        self.agent_repo = AgentRepository(db)
        self.validation_repo = ValidationLogRepository(db)
        self.embedding_repo = EmbeddingRepository(db)
        self.run_repo = AgentRunRepository(db)

    def _billing(self) -> UsageService:
        return UsageService(self.db)

    def _agent_run_svc(self) -> AgentRunService:
        return AgentRunService(self.db, self._billing())

    # ----------------------------
    # Agent
    # ----------------------------

    async def get_agent(self, id: UUID) -> Optional[Agent]:
        return await self.agent_repo.get(id)

    async def get_agents(self, skip: int = 0, limit: int = 100) -> List[Agent]:
        return await self.agent_repo.get_all(skip=skip, limit=limit)

    async def create_agent(self, name: str, phase: str, config: Optional[dict] = None) -> Agent:
        _ = config
        return await self.agent_repo.create({"name": name, "phase": phase})

    async def update_agent(self, db_obj: Agent, obj_in: Any) -> Agent:
        return await self.agent_repo.update(db_obj, _to_update_dict(obj_in))

    async def delete_agent(self, id: UUID) -> Optional[Agent]:
        db_obj = await self.get_agent(id)
        if db_obj:
            return await self.agent_repo.delete(db_obj)
        return None

    # ----------------------------
    # AgentRun
    # ----------------------------

    async def get_agent_run(self, id: UUID) -> Optional[AgentRun]:
        return await self.run_repo.get_with_stage_and_business(id)

    async def get_agent_runs(
        self,
        skip: int = 0,
        limit: int = 100,
        user_id: Optional[UUID] = None,
    ) -> List[AgentRun]:
        if user_id is not None:
            return await self.run_repo.get_all_for_user(user_id=user_id, skip=skip, limit=limit)
        return await self.run_repo.get_all(skip=skip, limit=limit)

    async def initiate_agent_run(
        self,
        agent_id: UUID,
        user_id: Optional[UUID],
        target_id: Optional[UUID],
        target_type: Optional[str],
        stage_id: UUID,
        input_data: Optional[Dict[str, Any]] = None,
    ) -> AgentRun:
        return await self._agent_run_svc().initiate_agent_run(
            agent_id=agent_id,
            user_id=user_id,
            stage_id=stage_id,
            input_data=input_data,
        )

    async def update_agent_run(self, db_obj: AgentRun, obj_in: Any) -> AgentRun:
        return await self.run_repo.update(db_obj, _to_update_dict(obj_in))

    async def delete_agent_run(self, id: UUID) -> Optional[AgentRun]:
        db_obj = await self.get_agent_run(id)
        if db_obj:
            return await self.run_repo.delete(db_obj)
        return None

    async def execute_agent_run_async(self, run_id: UUID) -> Optional[AgentRun]:
        return await self._agent_run_svc().execute_agent_run_async(run_id)

    # ----------------------------
    # ValidationLog
    # ----------------------------

    async def get_validation_log(self, id: UUID) -> Optional[ValidationLog]:
        return await self._agent_run_svc().get_validation_log(id)

    async def record_validation_log(self, agent_run_id: UUID, result: str, details: str) -> ValidationLog:
        return await self._agent_run_svc().record_validation_log(agent_run_id, result, details)

    async def get_validation_logs(self, skip: int = 0, limit: int = 100) -> List[ValidationLog]:
        return await self.validation_repo.get_all(skip=skip, limit=limit)

    async def update_validation_log(self, db_obj: ValidationLog, obj_in: Any) -> ValidationLog:
        return await self.validation_repo.update(db_obj, _to_update_dict(obj_in))

    async def delete_validation_log(self, id: UUID) -> Optional[ValidationLog]:
        db_obj = await self.get_validation_log(id)
        if db_obj:
            return await self.validation_repo.delete(db_obj)
        return None

    # ----------------------------
    # Embedding
    # ----------------------------

    async def get_embedding(self, id: UUID) -> Optional[Embedding]:
        return await EmbeddingService(self.db).get_embedding(id)

    async def get_embeddings(self, skip: int = 0, limit: int = 100) -> List[Embedding]:
        return await EmbeddingService(self.db).get_embeddings(skip, limit)

    async def create_embedding(self, obj_in: Any) -> Embedding:
        return await EmbeddingService(self.db).create_embedding(obj_in)

    async def update_embedding(self, db_obj: Embedding, obj_in: Any) -> Embedding:
        return await self.embedding_repo.update(db_obj, _to_update_dict(obj_in))

    async def delete_embedding(self, id: UUID) -> Optional[Embedding]:
        return await EmbeddingService(self.db).delete_embedding(id)

    async def trigger_vectorization(
        self,
        target_id: UUID,
        target_type: str,
        content: str,
        agent_id: Optional[UUID] = None,
    ) -> Optional[Embedding]:
        return await EmbeddingService(self.db).trigger_vectorization(target_id, target_type, content, agent_id)

    def reset_internal_state(self) -> None:
        logger.info("ai_service reset_internal_state called")

    def get_detailed_status(self) -> dict:
        return {"module": "ai_service", "status": "operational"}

    @staticmethod
    async def run_agent_in_background(db_factory: Any, run_id: UUID) -> None:
        """Internal background task handler for agent execution."""
        async with db_factory() as db:
            billing = UsageService(db)
            service = AgentRunService(db, billing)
            try:
                await service.execute_agent_run_async(run_id)
            except Exception:
                logger.exception("Failed to execute agent run in background")
