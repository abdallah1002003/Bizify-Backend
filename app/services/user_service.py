import random
import string
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.mail import send_otp_email
from app.core.security import get_password_hash
from app.models.partner_profile import PartnerProfile
from app.models.user import User, UserRole
from app.models.verification import AccountVerification, VerificationType
from app.schemas.user import UserCreate


class UserService:
    """
    Service class for user-related operations, including registration and OTP management.
    """

    @staticmethod
    def create_user(db: Session, user_in: UserCreate) -> User:
        """
        Creates a new user and triggers OTP creation if not pre-verified.
        """
        hashed_password = get_password_hash(user_in.password)
        
        db_user = User(
            email = user_in.email,
            password_hash = hashed_password,
            full_name = user_in.full_name,
            role = user_in.role,
            is_active = user_in.is_active,
            is_verified = user_in.is_verified,
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        if not db_user.is_verified:
            UserService.create_otp(db, db_user.id, db_user.email)
            
        return db_user

    @staticmethod
    def create_otp(
        db: Session,
        user_id: uuid.UUID,
        email: str,
        v_type: VerificationType = VerificationType.ACCOUNT_VERIFICATION
    ) -> str:
        """
        Generates and sends an OTP for verification purposes.
        Enforces a 60-second wait between OTP requests.
        """
        last_otp = db.query(AccountVerification).filter(
            AccountVerification.user_id == user_id,
            AccountVerification.verification_type == v_type
        ).order_by(AccountVerification.created_at.desc()).first()
        
        if last_otp:
            time_elapsed = datetime.now(timezone.utc) - last_otp.created_at.replace(tzinfo = timezone.utc)
            
            if time_elapsed.total_seconds() < 60:
                remaining = 60 - int(time_elapsed.total_seconds())
                
                raise HTTPException(
                    status_code = status.HTTP_400_BAD_REQUEST,
                    detail = f"Please wait before sending another OTP {remaining} seconds"
                )
        
        otp = "".join(random.choices(string.digits, k = 6))
        expires_at = datetime.now(timezone.utc) + timedelta(minutes = 10)
        
        db_otp = AccountVerification(
            user_id = user_id,
            otp_code = otp,
            verification_type = v_type,
            expires_at = expires_at
        )
        
        db.add(db_otp)
        db.commit()
        
        send_otp_email(email, otp)
        
        return otp

    @staticmethod
    def verify_otp_status(db: Session, email: str, otp_code: str) -> bool:
        """
        Verifies an OTP and marks the user as verified if successful.
        """
        user = UserService.get_user_by_email(db, email)
        
        if not user:
            return False
            
        db_otp = db.query(AccountVerification).filter(
            AccountVerification.user_id == user.id,
            AccountVerification.otp_code == otp_code,
            AccountVerification.verification_type == VerificationType.ACCOUNT_VERIFICATION
        ).order_by(AccountVerification.created_at.desc()).first()
        
        if not db_otp or db_otp.is_expired:
            return False
            
        user.is_verified = True
        
        db.delete(db_otp)
        db.commit()
        
        return True

    @staticmethod
    def reset_password_logic(
        db: Session,
        email: str,
        otp_code: str,
        new_password: str
    ) -> bool:
        """
        Resets a user's password after successful OTP verification.
        """
        user = UserService.get_user_by_email(db, email)
        
        if not user:
            return False
            
        db_otp = db.query(AccountVerification).filter(
            AccountVerification.user_id == user.id,
            AccountVerification.otp_code == otp_code,
            AccountVerification.verification_type == VerificationType.PASSWORD_RESET
        ).order_by(AccountVerification.created_at.desc()).first()
        
        if not db_otp or db_otp.is_expired:
            return False
            
        user.password_hash = get_password_hash(new_password)
        
        db.delete(db_otp)
        db.commit()
        
        return True

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """
        Retrieves a user by their email address.
        """
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def get_all_users(db: Session) -> List[User]:
        """
        Retrieves all users from the database.
        """
        return db.query(User).all()

    @staticmethod
    def delete_user_by_email(db: Session, email: str) -> bool:
        """
        Deletes a user and their associated partner profile by email.
        """
        user = UserService.get_user_by_email(db, email)
        
        if not user:
            raise HTTPException(
                status_code = status.HTTP_404_NOT_FOUND,
                detail = "User not found"
            )
            
        db.query(PartnerProfile).filter(PartnerProfile.user_id == user.id).delete()
        
        db.delete(user)
        db.commit()
        
        return True

    @staticmethod
    def promote_user(db: Session, user_id: uuid.UUID, new_role: UserRole) -> User:
        """
        Updates a user's role.
        """
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(
                status_code = status.HTTP_404_NOT_FOUND,
                detail = "User not found"
            )
        
        user.role = new_role
        
        db.commit()
        db.refresh(user)
        
        return user
