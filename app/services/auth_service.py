from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.core import security
from app.core.config import settings
from app.models.user import User
from app.models.token_blacklist import TokenBlacklist
from app.services import user_service
from app.models.verification import VerificationType
from app.schemas.user import OTPVerify


class AuthService:
    @staticmethod
    def authenticate(db: Session, email: str, password: str) -> User:
        user = user_service.get_user_by_email(db, email=email)
        if not user:
            raise HTTPException(status_code=401, detail="Incorrect email or password")

        if user.is_locked:
            raise HTTPException(status_code=401, detail=f"Account locked until {user.locked_until}")

        if not security.verify_password(password, user.password_hash):
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 5:
                user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=15)
            db.commit()
            raise HTTPException(status_code=401, detail="Incorrect email or password")

        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_activity = datetime.utcnow() 
        db.refresh(user)
        
        if not user.is_active: raise HTTPException(status_code=400, detail="Inactive user")
        if not user.is_verified: raise HTTPException(status_code=400, detail="User not verified")
        return user

    @staticmethod
    def create_token_response(user: User):
        expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        token = security.create_access_token(
            data={"sub": str(user.id), "email": user.email, "role": user.role},
            expires_delta=expires
        )
        return {"access_token": token, "token_type": "bearer"}

    @staticmethod
    def logout(db: Session, token: str):
        exists = db.query(TokenBlacklist).filter(TokenBlacklist.token == token).first()
        if not exists:
            db.add(TokenBlacklist(token=token))
            db.commit()
        return {"message": "Successfully logged out"}
    
    @staticmethod
    def verify_otp(db: Session, data: OTPVerify):
        success = user_service.verify_otp_status(db, email=data.email, otp_code=data.otp_code)
        if not success:
            raise HTTPException(status_code=400, detail="Invalid or expired OTP")
        return {"message": "Account verified successfully"}

    @staticmethod
    def forgot_password(db: Session, email: str):
        user = user_service.get_user_by_email(db, email=email)
        if not user:
            return {"message": "If this email exists, a reset code has been sent"}
        user_service.create_otp(db, user.id, user.email, v_type=VerificationType.PASSWORD_RESET)
        return {"message": "Verification code sent to your email"}

    @staticmethod
    def reset_password(db: Session, email: str, otp_code: str, new_password: str):
        success = user_service.reset_password_logic(db, email, otp_code, new_password)
        if not success:
            raise HTTPException(status_code=400, detail="Invalid or expired OTP")
        return {"message": "Password reset successfully"}

