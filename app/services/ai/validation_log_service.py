from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ValidationLog
from app.services.ai import ai_service


async def record_critique(db: AsyncSession, agent_run_id, score: float, critique: dict) -> ValidationLog:
    result = "SUCCESS" if score >= 0.8 else "WARNING"
    log = await ai_service.record_validation_log(
        db,
        agent_run_id=agent_run_id,
        result=result,
        details=str(critique),
    )
    log.confidence_score = score
    log.threshold_passed = score >= 0.8
    await db.commit()
    await db.refresh(log)
    return log
