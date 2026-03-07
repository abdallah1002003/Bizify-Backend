"""
Security utilities for authentication and password management.

This module provides functions for:
    - JWT token creation (access, refresh, password reset, email verification)
    - Token verification and validation
    - Password hashing and verification (bcrypt)
    - Secure token generation with JTI (JWT ID) for revocation tracking

All tokens include an expiration time and are signed with the configured algorithm
(RS256 for production with RSA keys, HS256 for development with secret key).
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Union, cast, Dict
from uuid import uuid4
import jwt
from passlib.context import CryptContext
from config.settings import settings

# Bcrypt context for password hashing and verification
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token for user authentication.
    
    Access tokens are short-lived (default 30 minutes) and used to authenticate
    API requests. They include a unique JTI (JWT ID) for tracking.
    
    Args:
        subject: User ID or subject identifier (typically UUID or email string)
        expires_delta: Optional custom expiration time. If None, uses ACCESS_TOKEN_EXPIRE_MINUTES
                      from settings (default 30 minutes)
    
    Returns:
        str: Signed JWT access token that can be used in Authorization header
        
    Example:
        >>> token = create_access_token(subject="user-123")
        >>> # Use in request: Authorization: Bearer {token}
        
    Note:
        - Token includes 'type': 'access' to distinguish from refresh tokens
        - Includes unique 'jti' (JWT ID) for revocation tracking
        - Signed with RS256 (RSA) or HS256 (HMAC) based on configuration
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {"exp": expire, "sub": str(subject), "jti": str(uuid4()), "type": "access"}
    return cast(str, jwt.encode(to_encode, settings.jwt_signing_key, algorithm=settings.jwt_algorithm))



def create_refresh_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT refresh token for obtaining new access tokens.
    
    Refresh tokens are long-lived (default 7 days) and used to request new access tokens
    without requiring user credentials. They cannot be used for API authentication.
    
    Args:
        subject: User ID or subject identifier (typically UUID or email string)
        expires_delta: Optional custom expiration time. If None, defaults to 7 days
    
    Returns:
        str: Signed JWT refresh token for token rotation flow
        
    Example:
        >>> refresh_token = create_refresh_token(subject="user-123")
        >>> # Later, exchange for new access token via /auth/refresh endpoint
        
    Note:
        - Token includes 'type': 'refresh' to distinguish from access tokens
        - Includes unique 'jti' (JWT ID) for revocation tracking
        - Attempting to use as access token raises 401 Unauthorized
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=7)

    to_encode = {"exp": expire, "sub": str(subject), "jti": str(uuid4()), "type": "refresh"}
    return cast(str, jwt.encode(to_encode, settings.jwt_signing_key, algorithm=settings.jwt_algorithm))



def create_password_reset_token(email: str) -> str:
    """
    Create a short-lived token for password reset flow.
    
    Password reset tokens are very short-lived (default 15 minutes) and used
    to verify the user's identity during password reset. Include with reset link.
    
    Args:
        email: User's email address (subject of the token)
    
    Returns:
        str: Time-limited JWT token for single-use password reset
        
    Example:
        >>> token = create_password_reset_token("user@example.com")
        >>> # Send in reset link: https://example.com/reset-password?token={token}
        
    Note:
        - Expires after 15 minutes by default
        - Includes unique 'jti' for revocation/single-use enforcement
        - Token type is 'password_reset' to prevent misuse
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode = {"exp": expire, "sub": email, "type": "password_reset", "jti": str(uuid4())}
    return cast(str, jwt.encode(to_encode, settings.jwt_signing_key, algorithm=settings.jwt_algorithm))


def verify_password_reset_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify and decode a password reset token.
    
    Validates the token signature, expiration, and type. Returns the full payload
    if valid, or None if invalid/expired.
    
    Args:
        token: JWT token string from reset request
    
    Returns:
        Dict containing full token payload if valid (includes 'sub', 'exp', 'jti'),
        None if token is invalid, expired, or wrong type
        
    Example:
        >>> payload = verify_password_reset_token(token)
        >>> if payload:
        ...     email = payload['sub']
        ...     # Proceed with password reset for this email
        ... else:
        ...     # Token invalid or expired
        ...     raise ValueError("Invalid reset token")
    """
    try:
        decoded_token = jwt.decode(token, settings.jwt_verify_key, algorithms=[settings.jwt_algorithm])
        if decoded_token.get("type") != "password_reset":
            return None
        return cast(Dict[str, Any], decoded_token)
    except jwt.InvalidTokenError:
        return None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify that a plaintext password matches a bcrypt hash.
    
    Uses constant-time comparison to prevent timing attacks.
    
    Args:
        plain_password: Plaintext password from user input
        hashed_password: Bcrypt hash from database
    
    Returns:
        bool: True if password matches hash, False otherwise
        
    Example:
        >>> if verify_password("user_input", user.password_hash):
        ...     # Credentials valid, grant access
        ... else:
        ...     # Invalid password
    """
    return cast(bool, pwd_context.verify(plain_password, hashed_password))


def get_password_hash(password: str) -> str:
    """
    Hash a plaintext password using bcrypt.
    
    Generates a secure bcrypt hash suitable for storage in database.
    Uses default cost factor (12 rounds).
    
    Args:
        password: Plaintext password from user (should be 8+ characters)
    
    Returns:
        str: Bcrypt hash starting with '$2b$' prefix
        
    Example:
        >>> hash = get_password_hash("MySecurePassword123!")
        >>> # Store hash in database, never the plaintext
        
    Note:
        - Hash includes salt, so same password produces different hashes
        - Suitable for verifying with verify_password()
        - Takes ~0.5-1 second per call (intentional for security)
    """
    return cast(str, pwd_context.hash(password))


def create_email_verification_token(email: str) -> str:
    """
    Create a token for email verification during user registration.
    
    Email verification tokens are medium-lived (default 24 hours) to allow users
    to verify their email address in registration flow.
    
    Args:
        email: Email address to verify
    
    Returns:
        str: Time-limited JWT token for email verification
        
    Example:
        >>> token = create_email_verification_token("newuser@example.com")
        >>> # Send in verification link: https://example.com/verify-email?token={token}
        
    Note:
        - Expires after 24 hours by default
        - Includes unique 'jti' for single-use enforcement
        - Token type is 'email_verification'
    """
    expire = datetime.now(timezone.utc) + timedelta(hours=24)
    to_encode = {"exp": expire, "sub": email, "type": "email_verification", "jti": str(uuid4())}
    return cast(str, jwt.encode(to_encode, settings.jwt_signing_key, algorithm=settings.jwt_algorithm))


def verify_email_verification_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify and decode an email verification token.
    
    Validates the token signature, expiration, and type. Returns the full payload
    if valid, or None if invalid/expired.
    
    Args:
        token: JWT token string from verification link
    
    Returns:
        Dict containing full token payload if valid (includes 'sub', 'exp', 'jti'),
        None if token is invalid, expired, or wrong type
        
    Example:
        >>> payload = verify_email_verification_token(token)
        >>> if payload:
        ...     email = payload['sub']
        ...     user.is_verified = True
        ...     db.commit()
        ... else:
        ...     raise ValueError("Invalid verification token")
    """
    try:
        decoded_token = jwt.decode(token, settings.jwt_verify_key, algorithms=[settings.jwt_algorithm])
        if decoded_token.get("type") != "email_verification":
            return None
        return cast(Dict[str, Any], decoded_token)
    except jwt.InvalidTokenError:
        return None

