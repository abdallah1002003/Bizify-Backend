import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class VerificationType(str, enum.Enum):
    """
    Enumeration of account verification types.
    """

    ACCOUNT_VERIFICATION = "account_verification"
    PASSWORD_RESET = "password_reset"


class AccountVerification(Base):
    """
    SQLAlchemy model representing an account verification or password reset token.
    """

    __tablename__ = "account_verifications"

    id = Column(UUID(as_uuid = True), primary_key = True, default = uuid.uuid4)
    user_id = Column(UUID(as_uuid = True), ForeignKey("users.id"), nullable = False)
    otp_code = Column(String(6), nullable = False)
    verification_type = Column(
        Enum(VerificationType, values_callable = lambda x: [e.value for e in x]),
        default = VerificationType.ACCOUNT_VERIFICATION
    )
    expires_at = Column(DateTime, nullable = False)
    created_at = Column(DateTime, default = datetime.utcnow)

    user = relationship("User", back_populates = "verification_codes")

    @property
    def is_expired(self) -> bool:
        """
        Check if the verification token has expired.
        """
        now = datetime.now(timezone.utc)

        if self.expires_at.tzinfo is None:
            return now.replace(tzinfo = None) > self.expires_at

        return now > self.expires_at