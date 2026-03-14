from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.api.dependencies import get_db, get_current_user, oauth2_scheme
from app.schemas.user import Token
from app.services.auth_service import AuthService
from app.models.user import User
from app.schemas.user import Token, OTPVerify
from app.core.config import settings    

router = APIRouter()

@router.post("/login", response_model=Token)
def login_access_token(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    user = AuthService.authenticate(db, email=form_data.username, password=form_data.password)
    return AuthService.create_token_response(user)

@router.post("/logout")
def logout(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    return AuthService.logout(db, token)

@router.post("/verify-otp")
def verify_otp(data: OTPVerify, db: Session = Depends(get_db)):
    return AuthService.verify_otp(db, data)
    
@router.post("/forgot-password")
def forgot_password(email: str, db: Session = Depends(get_db)):
    return AuthService.forgot_password(db, email)
    
@router.post("/reset-password")
def reset_password(email: str, otp_code: str, new_password: str, db: Session = Depends(get_db)):
    return AuthService.reset_password(db, email, otp_code, new_password)


@router.get("/session-status")
def get_session_status(current_user: User = Depends(get_current_user)):
    from datetime import datetime, timedelta
    now = datetime.utcnow()
    last_act = current_user.last_activity
        
    elapsed = now - last_act
    remaining = timedelta(minutes=settings.SESSION_TIMEOUT_MINUTES) - elapsed
    
    return {
        "is_active": True,
        "remaining_minutes": max(0, remaining.total_seconds() / 60),
        "warning_threshold": settings.SESSION_WARNING_MINUTES
    }

@router.post("/ping")
def session_ping(current_user: User = Depends(get_current_user)):
    return {"message": "Session kept alive"}
