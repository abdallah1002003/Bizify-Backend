import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models.token_blacklist import TokenBlacklist
from app.models.verification import AccountVerification, VerificationType


class AuthRepository:
    """Data-access helpers for authentication state and OTP records."""

    def is_token_blacklisted(self, db: Session, token: str) -> bool:
        """Return whether a JWT has already been blacklisted."""
        result = db.query(TokenBlacklist).filter(TokenBlacklist.token == token).first()
        return result is not None

    def blacklist_token(
        self,
        db: Session,
        token: str,
        *,
        commit: bool = True,
    ) -> TokenBlacklist:
        """Persist a JWT blacklist entry."""
        blacklisted = TokenBlacklist(token=token)
        db.add(blacklisted)
        if commit:
            db.commit()
        else:
            db.flush()
        db.refresh(blacklisted)
        return blacklisted

    def create_otp(
        self,
        db: Session,
        *,
        user_id: uuid.UUID,
        otp_hash: str,
        verification_type: VerificationType,
        expires_at: datetime,
        commit: bool = True,
    ) -> AccountVerification:
        """Create an OTP verification record."""
        otp = AccountVerification(
            user_id=user_id,
            otp_hash=otp_hash,
            verification_type=verification_type,
            expires_at=expires_at,
        )
        db.add(otp)
        if commit:
            db.commit()
        else:
            db.flush()
        db.refresh(otp)
        return otp

    def get_latest_otp(
        self,
        db: Session,
        user_id: uuid.UUID,
        v_type: VerificationType,
    ) -> Optional[AccountVerification]:
        """Fetch the latest OTP for a user and verification type."""
        return (
            db.query(AccountVerification)
            .filter(
                AccountVerification.user_id == user_id,
                AccountVerification.verification_type == v_type,
            )
            .order_by(AccountVerification.created_at.desc())
            .first()
        )



    def delete_otp(
        self,
        db: Session,
        otp: AccountVerification,
        *,
        commit: bool = True,
    ) -> None:
        """Delete an OTP record."""
        db.delete(otp)
        if commit:
            db.commit()
        else:
            db.flush()


auth_repo = AuthRepository()
