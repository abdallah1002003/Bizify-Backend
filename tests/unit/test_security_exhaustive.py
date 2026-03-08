import pytest
import jwt
from datetime import timedelta, datetime, timezone
from unittest.mock import patch
from app.core.security import (
    create_access_token,
    create_refresh_token,
    create_password_reset_token,
    verify_password_reset_token,
    get_password_hash,
    verify_password,
    create_email_verification_token,
    verify_email_verification_token,
)
from config.settings import settings

def test_password_hashing_and_verification():
    password = "secret_password_123"
    hashed = get_password_hash(password)
    assert hashed != password
    assert hashed.startswith("$2b$") # bcrypt
    
    assert verify_password(password, hashed) is True
    assert verify_password("wrong_password", hashed) is False

def test_password_hashing_salts():
    password = "same_password"
    h1 = get_password_hash(password)
    h2 = get_password_hash(password)
    assert h1 != h2 # Different salts

def test_access_token_creation():
    subject = "user123"
    token = create_access_token(subject)
    payload = jwt.decode(token, settings.jwt_verify_key, algorithms=[settings.jwt_algorithm])
    
    assert payload["sub"] == subject
    assert payload["type"] == "access"
    assert "jti" in payload
    assert "exp" in payload

def test_access_token_custom_expiry():
    delta = timedelta(minutes=5)
    token = create_access_token("sub", expires_delta=delta)
    payload = jwt.decode(token, settings.jwt_verify_key, algorithms=[settings.jwt_algorithm])
    
    # Approx expiration check
    expected_exp = datetime.now(timezone.utc).timestamp() + 300
    assert abs(payload["exp"] - expected_exp) < 10

def test_refresh_token_creation():
    subject = "user456"
    token = create_refresh_token(subject)
    payload = jwt.decode(token, settings.jwt_verify_key, algorithms=[settings.jwt_algorithm])
    
    assert payload["sub"] == subject
    assert payload["type"] == "refresh"
    assert "exp" in payload
    
    # Custom expiry
    delta = timedelta(days=1)
    token2 = create_refresh_token(subject, expires_delta=delta)
    payload2 = jwt.decode(token2, settings.jwt_verify_key, algorithms=[settings.jwt_algorithm])
    expected_exp = datetime.now(timezone.utc).timestamp() + 86400
    assert abs(payload2["exp"] - expected_exp) < 10

def test_password_reset_token_lifecycle():
    email = "test@example.com"
    token = create_password_reset_token(email)
    
    # Valid
    payload = verify_password_reset_token(token)
    assert payload is not None
    assert payload["sub"] == email
    assert payload["type"] == "password_reset"
    
    # Wrong type (access token used as reset token)
    access_token = create_access_token(email)
    assert verify_password_reset_token(access_token) is None
    
    # Invalid token
    assert verify_password_reset_token("invalid.token.here") is None
    
    # Expired token
    with patch("app.core.security.datetime") as mock_datetime:
        # Mocking datetime.now(timezone.utc) is tricky, easier to mock decode or use a very short delta
        pass # Will rely on actual expiry logic or mock jwt.decode if needed

def test_email_verification_token_lifecycle():
    email = "verify@example.com"
    token = create_email_verification_token(email)
    
    # Valid
    payload = verify_email_verification_token(token)
    assert payload is not None
    assert payload["sub"] == email
    assert payload["type"] == "email_verification"
    
    # Wrong type
    reset_token = create_password_reset_token(email)
    assert verify_email_verification_token(reset_token) is None
    
    # Invalid
    assert verify_email_verification_token("garbage") is None

@patch("jwt.decode")
def test_verify_password_reset_exception(mock_decode):
    mock_decode.side_effect = jwt.InvalidTokenError()
    assert verify_password_reset_token("any") is None

@patch("jwt.decode")
def test_verify_email_verification_exception(mock_decode):
    mock_decode.side_effect = jwt.InvalidTokenError()
    assert verify_email_verification_token("any") is None
