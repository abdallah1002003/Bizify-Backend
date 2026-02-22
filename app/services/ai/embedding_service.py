from __future__ import annotations

from sqlalchemy.orm import Session
from uuid import UUID

from app.models import Embedding
from app.services.ai import ai_service
from app.services.ai import provider_runtime


def generate_embedding(db: Session, content: str, agent_id: UUID | None = None) -> Embedding:
    vector = provider_runtime.generate_embedding_vector(content)
    return ai_service.create_embedding(
        db,
        {
            "business_id": None,
            "agent_id": agent_id,
            "content": content,
            "vector": vector,
        },
    )
