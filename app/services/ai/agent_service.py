from __future__ import annotations
import logging
from typing import Any, List, Optional
from uuid import UUID
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_async_db
from app.models import Agent
from app.services.base_service import BaseService
from app.repositories.ai_repository import AgentRepository

logger = logging.getLogger(__name__)

class AgentService(BaseService):
    """Service for managing AI Agent templates."""
    
    def __init__(self, db: AsyncSession):
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
        return await self.repo.create({"name": name, "phase": phase, "config": config})

    async def update_agent(self, db_obj: Agent, obj_in: Any) -> Agent:
        """Update an existing agent template."""
        return await self.repo.update(db_obj, obj_in)

    async def delete_agent(self, id: UUID) -> Optional[Agent]:
        """Delete an agent template by ID."""
        return await self.repo.delete(id)

async def get_agent_service(db: AsyncSession = Depends(get_async_db)) -> AgentService:
    """Dependency provider for AgentService."""
    return AgentService(db)
