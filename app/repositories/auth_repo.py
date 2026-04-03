import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models.token_blacklist import TokenBlacklist
from app.models.verification import AccountVerification, VerificationType


class AuthRepository:
    """
    Repository for authentication-related database operations.
    Covers: TokenBlacklist, AccountVerification.
    """

    def is_token_blacklisted(self, db: Session, token: str) -> bool:
        """
        Check whether a JWT token has been invalidated (blacklisted after logout).
        Returns True if the token is in the blacklist, False if it is still valid.
        """
        result = (
            db.query(TokenBlacklist)
            .filter(TokenBlacklist.token == token)
            .first()
        )
        return result is not None

    def blacklist_token(self, db: Session, token: str) -> TokenBlacklist:
        """
        Add a JWT token to the blacklist to invalidate it immediately.
        Called during logout to prevent re-use of a valid token after sign-out.
        """
        blacklisted = TokenBlacklist(token=token)
        db.add(blacklisted)
        db.commit()
        db.refresh(blacklisted)
        return blacklisted

    def create_otp(
        self,
        db: Session,
        *,
        user_id: uuid.UUID,
        otp_code: str,
        verification_type: VerificationType,
        expires_at: datetime,
        commit: bool = True,
    ) -> AccountVerification:
        otp = AccountVerification(
            user_id=user_id,
            otp_code=otp_code,
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
        """
        Fetch the most recently issued OTP for a user and verification type.
        Used to enforce the 60-second cooldown between OTP requests.
        """
        return (
            db.query(AccountVerification)
            .filter(
                AccountVerification.user_id == user_id,
                AccountVerification.verification_type == v_type,
            )
            .order_by(AccountVerification.created_at.desc())
            .first()
        )

    def get_valid_otp(
        self,
        db: Session,
        user_id: uuid.UUID,
        otp_code: str,
        v_type: VerificationType,
    ) -> Optional[AccountVerification]:
        """
        Fetch a non-expired OTP matching the given code and type.
        Returns None if the OTP does not exist, is wrong, or has expired.
        """
        return (
            db.query(AccountVerification)
            .filter(
                AccountVerification.user_id == user_id,
                AccountVerification.otp_code == otp_code,
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
        db.delete(otp)
        if commit:
            db.commit()
        else:
            db.flush()


auth_repo = AuthRepository()
