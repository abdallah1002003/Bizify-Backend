from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User
from app.schemas.user import UserCreate
from typing import Optional
from app.core.security import get_password_hash
import random
import string
from datetime import datetime, timedelta, timezone
from app.models.verification import AccountVerification , VerificationType
from app.core.mail import send_otp_email
from app.models.partner_profile import PartnerProfile
from app.models.user import UserRole
from uuid import UUID


def create_user(db: Session, user_in: UserCreate) -> User:
    hashed_password = get_password_hash(user_in.password)
    db_user = User(
        email=user_in.email,
        password_hash=hashed_password,
        role=user_in.role,
        is_active=user_in.is_active,
        is_verified=user_in.is_verified,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    if not db_user.is_verified:
        create_otp(db, db_user.id, db_user.email)
        
    return db_user

def create_otp(
    db: Session, 
    user_id: str, 
    email: str, 
    v_type: VerificationType = VerificationType.ACCOUNT_VERIFICATION
) -> str:
    last_otp = db.query(AccountVerification).filter(
        AccountVerification.user_id == user_id,
        AccountVerification.verification_type == v_type
    ).order_by(AccountVerification.created_at.desc()).first()
    if last_otp:
        time_elapsed = datetime.now(timezone.utc) - last_otp.created_at.replace(tzinfo=timezone.utc)
        if time_elapsed.total_seconds() < 60:
            remaining = 60 - int(time_elapsed.total_seconds())
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Please wait before sending another OTP {remaining} seconds")
    
    otp = ''.join(random.choices(string.digits, k=6))
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
    
    db_otp = AccountVerification(
        user_id=user_id,
        otp_code=otp,
        verification_type=v_type,
        expires_at=expires_at
    )
    db.add(db_otp)
    db.commit()
    
    send_otp_email(email, otp)
    
    return otp

def verify_otp_status(db: Session, email: str, otp_code: str) -> bool:
    user = get_user_by_email(db, email)
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

def reset_password_logic(db: Session, email: str, otp_code: str, new_password: str) -> bool:
    user = get_user_by_email(db, email)
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

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()

def get_all_users(db: Session):
    return db.query(User).all()
def delete_user_by_email(db: Session, email: str):
    user = get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.query(PartnerProfile).filter(PartnerProfile.user_id == user.id).delete()
    db.delete(user)
    db.commit()
    return True
def promote_user(db: Session, user_id: UUID, new_role: UserRole):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.role = new_role
    db.commit()
    db.refresh(user)
    return user


