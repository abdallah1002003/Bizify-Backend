import logging
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.mail import EmailDeliveryError, send_otp_email
from app.core.security import get_password_hash, verify_password
from app.models.user import User, UserRole
from app.models.verification import VerificationType
from app.repositories.auth_repo import auth_repo
from app.repositories.billing_repo import plan_repo, subscription_repo
from app.repositories.user_repo import user_repo
from app.schemas.partner_profile import PartnerProfileCreate, PartnerProfileRegistration
from app.schemas.user import UserCreate
from app.services.partner_service import PartnerService

logger = logging.getLogger(__name__)

# Max wrong guesses allowed against a single OTP before it is invalidated.
MAX_OTP_ATTEMPTS = 5

PARTNER_REGISTRATION_ROLES = {
    UserRole.MENTOR,
    UserRole.SUPPLIER,
    UserRole.MANUFACTURER,
}


class UserService:
    """User workflows for registration, lookup, and OTP handling."""

    @staticmethod
    def create_user(
        db: Session,
        user_in: UserCreate,
        partner_profile_in: Optional[PartnerProfileRegistration] = None,
        partner_files: Optional[list[UploadFile]] = None,
    ) -> User:
        """Create a new user and send a verification OTP when needed."""
        requires_partner_application = user_in.role in PARTNER_REGISTRATION_ROLES
        partner_files = partner_files or []

        if requires_partner_application and not partner_profile_in:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mentor, supplier, and manufacturer registration requires partner details.",
            )

        if not requires_partner_application and partner_profile_in:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Partner documents can only be submitted for partner roles.",
            )

        persisted_role = (
            UserRole.ENTREPRENEUR if requires_partner_application else user_in.role
        )
        hashed_password = get_password_hash(user_in.password)
        db_user = user_repo.create(
            db,
            obj_in={
                "email": user_in.email,
                "password_hash": hashed_password,
                "full_name": user_in.full_name,
                "role": persisted_role,
                "is_active": True,
                "is_verified": False,
            },
            commit=False,
            refresh=False,
        )

        partner_profile = None
        try:
            if partner_profile_in:
                partner_profile = PartnerService.apply_partner(
                    db,
                    db_user,
                    PartnerProfileCreate(
                        user_id=db_user.id,
                        **partner_profile_in.model_dump(),
                    ),
                    partner_files,
                    commit=False,
                    refresh=False,
                )
            # Provision a default Free subscription so every account has an
            # explicit plan record from signup. The usage/billing endpoints and
            # the AI plan gates read this; without it the user is only implicitly
            # "Free" and the subscriptions table stays empty. Best-effort: a
            # missing Free plan must not block registration.
            UserService._ensure_free_subscription(db, db_user.id)
            db.commit()
        except Exception:
            db.rollback()
            if partner_profile:
                PartnerService.cleanup_documents(partner_profile.documents_json)
            raise

        db.refresh(db_user)

        UserService.create_otp(
            db,
            db_user.id,
            db_user.email,
        )

        return db_user

    @staticmethod
    def _ensure_free_subscription(db: Session, user_id: uuid.UUID) -> None:
        """Attach the default Free plan to a user if they have no active subscription.

        Runs within the caller's transaction (commit=False). Failure to find or
        attach the Free plan is logged but never raised, so account creation is
        never blocked by billing configuration.
        """
        try:
            if subscription_repo.get_active_by_user(db, user_id):
                return
            free_plan = plan_repo.get_free_plan(db)
            if not free_plan:
                logger.warning(
                    "No active Free plan found; user %s created without a subscription", user_id
                )
                return
            subscription_repo.create_or_update(
                db, user_id=user_id, plan_id=free_plan.id, commit=False
            )
        except Exception:
            logger.exception("Failed to provision Free subscription for user %s", user_id)

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

        # Cryptographically-secure 6-digit code (secrets, not random).
        otp = "".join(secrets.choice("0123456789") for _ in range(6))
        hashed_otp = get_password_hash(otp)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
        auth_repo.create_otp(
            db,
            user_id=user_id,
            otp_hash=hashed_otp,
            verification_type=v_type,
            expires_at=expires_at,
            commit=True,
        )

        try:
            send_otp_email(email, otp)
        except EmailDeliveryError as exc:
            logger.error(
                "Email delivery failed for %s (OTP saved in DB): %s", email, exc,
            )
            # Surface the real reason so the user (and frontend toast) can act on it.
            # The OTP itself is never included in the response — only in server logs.
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Could not send verification email: {exc}",
            ) from exc
        except Exception:
            raise

        return otp

    @staticmethod
    def _verify_otp_or_count(db: Session, db_otp, otp_code: str) -> bool:
        """
        Verify a candidate OTP against the stored hash, counting failed attempts
        and invalidating the code once the lockout threshold is reached. This
        stops brute-force guessing of the short numeric code.
        """
        if db_otp.attempts >= MAX_OTP_ATTEMPTS:
            auth_repo.delete_otp(db, db_otp, commit=True)
            return False

        if not verify_password(otp_code, db_otp.otp_hash):
            db_otp.attempts += 1
            if db_otp.attempts >= MAX_OTP_ATTEMPTS:
                auth_repo.delete_otp(db, db_otp, commit=True)
            else:
                db.add(db_otp)
                db.commit()
            return False

        return True

    @staticmethod
    def verify_otp_status(db: Session, email: str, otp_code: str) -> bool:
        """Validate an account-verification OTP and mark the user as verified."""
        user = UserService.get_user_by_email(db, email=email)
        if not user:
            return False

        db_otp = auth_repo.get_latest_otp(
            db,
            user.id,
            VerificationType.ACCOUNT_VERIFICATION,
        )
        if not db_otp or db_otp.is_expired:
            return False

        if not UserService._verify_otp_or_count(db, db_otp, otp_code):
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

        db_otp = auth_repo.get_latest_otp(
            db,
            user.id,
            VerificationType.PASSWORD_RESET,
        )
        if not db_otp or db_otp.is_expired:
            return False

        if not UserService._verify_otp_or_count(db, db_otp, otp_code):
            return False

        user.password_hash = get_password_hash(new_password)
        user_repo.save(db, db_obj=user, commit=False, refresh=False)
        auth_repo.delete_otp(db, db_otp, commit=False)
        db.commit()
        db.refresh(user)
        return True

    @staticmethod
    def verify_reset_code_only(db: Session, email: str, otp_code: str) -> bool:
        """Verify if a password reset OTP is valid without resetting."""
        user = UserService.get_user_by_email(db, email=email)
        if not user:
            return False

        db_otp = auth_repo.get_latest_otp(
            db,
            user.id,
            VerificationType.PASSWORD_RESET,
        )
        if not db_otp or db_otp.is_expired:
            return False

        if not UserService._verify_otp_or_count(db, db_otp, otp_code):
            return False

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
    def get_all_users(db: Session) -> list[User]:
        """Fetch all users with a generous admin-facing limit."""
        return user_repo.get_multi(db, skip=0, limit=1000)

    @staticmethod
    def delete_user_by_email(db: Session, email: str) -> bool:
        """Delete a user and all their linked data using cascade delete."""
        user = UserService.get_user_by_email(db, email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # The model relationships are configured with cascade="all, delete-orphan"
        # so removing the user will automatically clean up profiles, verification codes, ideas, etc.
        user_repo.remove(db, id=user.id)
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
