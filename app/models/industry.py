import uuid

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Industry(Base):
    """
    SQLAlchemy model representing a hierarchical Industry/Sector.
    Level: 0 (General), 1 (Main Category), 2 (Specific Industry/Niche).
    """

    __tablename__ = "industries"

    id = Column(UUID(as_uuid = True), primary_key = True, default = uuid.uuid4)
    name = Column(String, nullable = False, unique = True)
    parent_id = Column(UUID(as_uuid = True), ForeignKey("industries.id"), nullable = True)
    # 0=General, 1=Category, 2=Sub-category
    level = Column(Integer, default = 1)

    # Self-referential relationship for hierarchy
    children = relationship("Industry", backref = "parent", remote_side = [id])

    benchmarks = relationship("SkillBenchmark", back_populates = "industry")
    businesses = relationship("Business", back_populates = "industry")
