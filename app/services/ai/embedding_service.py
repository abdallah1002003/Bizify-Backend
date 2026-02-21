from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import Embedding
from app.services.ai import ai_service


def generate_embedding(db: Session, content: str, agent_id=None) -> Embedding:
    return ai_service.create_embedding(
        db,
        {
            "business_id": None,
            "agent_id": agent_id,
            "content": content,
            "vector": ",".join(["0.123"] * 16),
        },
    )
