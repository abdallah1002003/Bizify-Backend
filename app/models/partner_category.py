import uuid

from sqlalchemy import Column, Enum, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.partner_profile import PartnerType


class PartnerCategory(Base):
    __tablename__ = "partner_categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    partner_type = Column(
        Enum(PartnerType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )

    partners = relationship("PartnerProfile", back_populates="category_ref")
