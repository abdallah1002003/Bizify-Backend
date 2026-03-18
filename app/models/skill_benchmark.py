import uuid

from sqlalchemy import Column, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class SkillBenchmark(Base):
    """
    SQLAlchemy model representing the required skill benchmark for an industry.
    """

    __tablename__ = "skill_benchmarks"

    id = Column(UUID(as_uuid = True), primary_key = True, default = uuid.uuid4)
    skill_name = Column(String, nullable = False)
    industry_id = Column(UUID(as_uuid = True), ForeignKey("industries.id"), nullable = False)
    minimum_required_level = Column(Integer, nullable = False)
    weight = Column(Float, default = 1.0)

    industry = relationship("Industry", back_populates = "benchmarks")
