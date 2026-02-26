from __future__ import annotations
import logging
from typing import Any, List, Optional
from uuid import UUID
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.database import get_async_db
from app.models import Agent
from app.services.base_service import BaseService
from app.core.crud_utils import _to_update_dict, _apply_updates

logger = logging.getLogger(__name__)

class AgentService(BaseService):
    """Service for managing AI Agent templates."""
    db: AsyncSession

    async def get_agent(self, id: UUID) -> Optional[Agent]:
        """Retrieve a single agent by ID."""
        stmt = select(Agent).where(Agent.id == id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_agents(self, skip: int = 0, limit: int = 100) -> List[Agent]:
        """Retrieve paginated agents."""
        stmt = select(Agent).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create_agent(self, name: str, phase: str, config: Optional[dict] = None) -> Agent:
        """Create a new AI agent template."""
        _ = config
        db_obj = Agent(name=name, phase=phase)
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def update_agent(self, db_obj: Agent, obj_in: Any) -> Agent:
        """Update an existing agent template."""
        _apply_updates(db_obj, _to_update_dict(obj_in))
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def delete_agent(self, id: UUID) -> Optional[Agent]:
        """Delete an agent template by ID."""
        db_obj = await self.get_agent(id=id)
        if not db_obj:
            return None
        await self.db.delete(db_obj)
        await self.db.commit()
        return db_obj

async def get_agent_service(db: AsyncSession = Depends(get_async_db)) -> AgentService:
    """Dependency provider for AgentService."""
    return AgentService(db)
