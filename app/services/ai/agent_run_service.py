from __future__ import annotations

from typing import Any
from uuid import UUID
from sqlalchemy.orm import Session

from app.models import AgentRun
from app.services.ai import ai_service


def create_agent_run(db: Session, obj_in: Any) -> AgentRun:
    return ai_service.initiate_agent_run(
        db,
        agent_id=obj_in.agent_id,
        user_id=None,
        target_id=None,
        target_type=None,
        stage_id=obj_in.stage_id,
    )


async def execute_agent_run(db: Session, run_id: UUID) -> AgentRun:
    """Kept for backward compatibility. Delegates to ai_service."""
    return await ai_service.execute_agent_run_async(db, run_id)
