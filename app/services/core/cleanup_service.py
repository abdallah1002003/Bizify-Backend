"""
Cleanup service for periodic removal of stale database records.

Functions can be called individually or via ``cleanup_all``.
All functions are safe to call repeatedly (idempotent).
"""

from datetime import datetime, timezone
import logging
from sqlalchemy.orm import Session

from app.models.users.user import RefreshToken, PasswordResetToken, EmailVerificationToken

logger = logging.getLogger(__name__)


def cleanup_expired_refresh_tokens(db: Session) -> int:
    """
    Remove expired refresh tokens.
    Returns the number of rows deleted.
    """
    try:
        now = datetime.now(timezone.utc)
        deleted = (
            db.query(RefreshToken)
            .filter(RefreshToken.expires_at < now)
            .delete(synchronize_session=False)
        )
        db.commit()
        if deleted:
            logger.info("Cleaned up %d expired refresh tokens", deleted)
        return deleted  # type: ignore[no-any-return]
    except Exception:
        db.rollback()
        logger.exception("Failed to clean up expired refresh tokens")
        return 0


# Keep legacy alias so existing callers in main.py don't break
cleanup_expired_tokens = cleanup_expired_refresh_tokens


def cleanup_expired_password_reset_tokens(db: Session) -> int:
    """
    Remove password reset tokens that are either expired or already used.
    Returns the number of rows deleted.
    """
    try:
        now = datetime.now(timezone.utc)
        deleted = (
            db.query(PasswordResetToken)
            .filter(
                (PasswordResetToken.expires_at < now) | (PasswordResetToken.used == True)  # noqa: E712
            )
            .delete(synchronize_session=False)
        )
        db.commit()
        if deleted:
            logger.info("Cleaned up %d expired/used password reset tokens", deleted)
        return deleted  # type: ignore[no-any-return]
    except Exception:
        db.rollback()
        logger.exception("Failed to clean up expired password reset tokens")
        return 0


def cleanup_expired_verification_tokens(db: Session) -> int:
    """
    Remove email verification tokens that are either expired or already used.
    Returns the number of rows deleted.
    """
    try:
        now = datetime.now(timezone.utc)
        deleted = (
            db.query(EmailVerificationToken)
            .filter(
                (EmailVerificationToken.expires_at < now) | (EmailVerificationToken.used == True)  # noqa: E712
            )
            .delete(synchronize_session=False)
        )
        db.commit()
        if deleted:
            logger.info("Cleaned up %d expired/used email verification tokens", deleted)
        return deleted  # type: ignore[no-any-return]
    except Exception:
        db.rollback()
        logger.exception("Failed to clean up expired email verification tokens")
        return 0


def cleanup_all(db: Session) -> dict:
    """
    Run all cleanup tasks in sequence and return a summary dict.

    Safe to call from a scheduler or manually.
    """
    return {
        "refresh_tokens": cleanup_expired_refresh_tokens(db),
        "password_reset_tokens": cleanup_expired_password_reset_tokens(db),
        "verification_tokens": cleanup_expired_verification_tokens(db),
    }
