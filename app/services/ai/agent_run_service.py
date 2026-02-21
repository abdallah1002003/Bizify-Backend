from __future__ import annotations

from typing import Any
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


def execute_agent_run(db: Session, run_id):
    return ai_service.execute_agent_run_sync(db, run_id)
