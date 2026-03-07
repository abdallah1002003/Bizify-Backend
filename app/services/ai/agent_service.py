from __future__ import annotations
import logging
from typing import Any, List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Agent
from app.services.base_service import BaseService
from app.core.crud_utils import _to_update_dict
from app.repositories.ai_repository import AgentRepository

logger = logging.getLogger(__name__)

class AgentService(BaseService):
    """Service for managing AI Agent templates."""
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)
        self.repo = AgentRepository(db)

    async def get_agent(self, id: UUID) -> Optional[Agent]:
        """Retrieve a single agent by ID."""
        return await self.repo.get(id)

    async def get_agents(self, skip: int = 0, limit: int = 100) -> List[Agent]:
        """Retrieve paginated agents."""
        return await self.repo.get_all(skip=skip, limit=limit)

    async def create_agent(self, name: str, phase: str, config: Optional[dict] = None) -> Agent:
        """Create a new AI agent template."""
        _ = config
        return await self.repo.create({"name": name, "phase": phase})

    async def update_agent(self, db_obj: Agent, obj_in: Any) -> Agent:
        """Update an existing agent template."""
        return await self.repo.update(db_obj, _to_update_dict(obj_in))

    async def delete_agent(self, id: UUID) -> Optional[Agent]:
        """Delete an agent template by ID."""
        db_obj = await self.get_agent(id=id)
        if db_obj:
            return await self.repo.delete(db_obj)
        return None

async def get_agent_service(db: AsyncSession) -> AgentService:
    """Dependency provider for AgentService."""
    return AgentService(db)
