from app.core.security import get_password_hash, verify_password

def test_password_hashing():
    """Verify that the core security password hashing works correctly at a unit level."""
    plain_password = "mysecretpassword123"
    hashed = get_password_hash(plain_password)
    
    assert hashed != plain_password
    assert verify_password(plain_password, hashed) is True
    assert verify_password("wrongpassword", hashed) is False
