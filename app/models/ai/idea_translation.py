import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class IdeaTranslation(Base):
    __tablename__ = "idea_translations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    idea_id = Column(UUID(as_uuid=True), ForeignKey("ideas.id", ondelete="CASCADE"), nullable=False, index=True)
    language = Column(String(2), nullable=False)        # "ar" | "en"
    section_name = Column(String, nullable=False)       # e.g. "overview", "market_potential"
    content = Column(Text, nullable=False)
    translated_at = Column(DateTime, default=datetime.utcnow)
    model_used = Column(String, nullable=True)          # e.g. "claude-haiku-4-5"

    idea = relationship("Idea", back_populates="translations")
