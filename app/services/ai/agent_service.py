# type: ignore
from __future__ import annotations
import logging
from typing import Any, List, Optional
from uuid import UUID
from fastapi import Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models import Agent
from app.services.base_service import BaseService
from app.core.crud_utils import _to_update_dict, _apply_updates

logger = logging.getLogger(__name__)

class AgentService(BaseService):
    """Service for managing AI Agent templates."""

    def get_agent(self, id: UUID) -> Optional[Agent]:
        return self.db.query(Agent).filter(Agent.id == id).first()

    def get_agents(self, skip: int = 0, limit: int = 100) -> List[Agent]:
        return self.db.query(Agent).offset(skip).limit(limit).all()

    def create_agent(self, name: str, phase: str, config: Optional[dict] = None) -> Agent:
        _ = config
        db_obj = Agent(name=name, phase=phase)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update_agent(self, db_obj: Agent, obj_in: Any) -> Agent:
        _apply_updates(db_obj, _to_update_dict(obj_in))
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def delete_agent(self, id: UUID) -> Optional[Agent]:
        db_obj = self.get_agent(id=id)
        if not db_obj:
            return None
        self.db.delete(db_obj)
        self.db.commit()
        return db_obj

def get_agent_service(db: Session = Depends(get_db)) -> AgentService:
    return AgentService(db)
