import logging
import random
import string
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.mail import EmailDeliveryError, send_otp_email
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.models.verification import VerificationType
from app.repositories.auth_repo import auth_repo
from app.repositories.partner_repo import partner_repo
from app.repositories.user_repo import user_repo
from app.schemas.user import UserCreate


logger = logging.getLogger(__name__)


class UserService:
    """User workflows for registration, lookup, and OTP handling."""

    @staticmethod
    def create_user(db: Session, user_in: UserCreate) -> User:
        """Create a new user and send a verification OTP when needed."""
        hashed_password = get_password_hash(user_in.password)
        db_user = user_repo.create(
            db,
            obj_in={
                "email": user_in.email,
                "password_hash": hashed_password,
                "full_name": user_in.full_name,
                "role": UserRole.USER,
                "is_active": True,
                "is_verified": False,
            },
            commit=False,
            refresh=False,
        )

        try:
            UserService.create_otp(
                db,
                db_user.id,
                db_user.email,
                commit=False,
            )
            db.commit()
        except Exception:
            db.rollback()
            raise

        db.refresh(db_user)

        return db_user

    @staticmethod
    def create_otp(
        db: Session,
        user_id: uuid.UUID,
        email: str,
        v_type: VerificationType = VerificationType.ACCOUNT_VERIFICATION,
        commit: bool = True,
    ) -> str:
        """Generate and send an OTP with a cooldown between requests."""
        last_otp = auth_repo.get_latest_otp(db, user_id, v_type)
        if last_otp:
            created_at = last_otp.created_at.replace(tzinfo=timezone.utc)
            time_elapsed = datetime.now(timezone.utc) - created_at
            if time_elapsed.total_seconds() < 60:
                remaining = 60 - int(time_elapsed.total_seconds())
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Please wait before sending another OTP {remaining} seconds",
                )

        otp = "".join(random.choices(string.digits, k=6))
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
        auth_repo.create_otp(
            db,
            user_id=user_id,
            otp_code=otp,
            verification_type=v_type,
            expires_at=expires_at,
            commit=False,
        )

        try:
            send_otp_email(email, otp)
            if commit:
                db.commit()
        except EmailDeliveryError as exc:
            db.rollback()
            logger.exception("OTP delivery failed for %s", email)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Unable to send verification code right now. Please try again later.",
            ) from exc
        except Exception:
            db.rollback()
            raise

        return otp

    @staticmethod
    def verify_otp_status(db: Session, email: str, otp_code: str) -> bool:
        """Validate an account-verification OTP and mark the user as verified."""
        user = UserService.get_user_by_email(db, email=email)
        if not user:
            return False

        db_otp = auth_repo.get_valid_otp(
            db,
            user.id,
            otp_code,
            VerificationType.ACCOUNT_VERIFICATION,
        )
        if not db_otp or db_otp.is_expired:
            return False

        user.is_verified = True
        user_repo.save(db, db_obj=user, commit=False, refresh=False)
        auth_repo.delete_otp(db, db_otp, commit=False)
        db.commit()
        db.refresh(user)
        return True

    @staticmethod
    def reset_password_logic(
        db: Session,
        email: str,
        otp_code: str,
        new_password: str,
    ) -> bool:
        """Reset a user's password after OTP verification."""
        user = UserService.get_user_by_email(db, email=email)
        if not user:
            return False

        db_otp = auth_repo.get_valid_otp(
            db,
            user.id,
            otp_code,
            VerificationType.PASSWORD_RESET,
        )
        if not db_otp or db_otp.is_expired:
            return False

        user.password_hash = get_password_hash(new_password)
        user_repo.save(db, db_obj=user, commit=False, refresh=False)
        auth_repo.delete_otp(db, db_otp, commit=False)
        db.commit()
        db.refresh(user)
        return True

    @staticmethod
    def get_user_by_id(db: Session, user_id: uuid.UUID) -> Optional[User]:
        """Fetch a user by identifier."""
        return user_repo.get(db, user_id)

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Fetch a user by email address."""
        return user_repo.get_by_email(db, email)

    @staticmethod
    def get_all_users(db: Session) -> List[User]:
        """Fetch all users with a generous admin-facing limit."""
        return user_repo.get_multi(db, skip=0, limit=1000)

    @staticmethod
    def delete_user_by_email(db: Session, email: str) -> bool:
        """Delete a user and any linked partner profile."""
        user = UserService.get_user_by_email(db, email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        partner_profile = partner_repo.get_by_user_id(db, user.id)
        if partner_profile:
            partner_repo.remove(db, id=partner_profile.id, commit=False)

        user_repo.remove(db, id=user.id, commit=False)
        db.commit()
        return True

    @staticmethod
    def promote_user(db: Session, user_id: uuid.UUID, new_role: UserRole) -> User:
        """Update a user's role."""
        user = user_repo.get(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        return user_repo.update(db, db_obj=user, obj_in={"role": new_role})
