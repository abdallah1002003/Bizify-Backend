import pytest
import os
import secrets
from unittest.mock import patch
from app.core.encryption import (
    encrypt,
    decrypt,
    EncryptedString,
    _get_key,
)
from config.settings import settings

def test_get_key_test_env_fallback():
    with patch.object(settings, "ENCRYPTION_KEY", ""):
        with patch.object(settings, "APP_ENV", "test"):
            key = _get_key()
            assert key == bytes.fromhex("00" * 32)

def test_get_key_production_failure():
    with patch.object(settings, "ENCRYPTION_KEY", ""):
        with patch.object(settings, "APP_ENV", "production"):
            with pytest.raises(RuntimeError, match="ENCRYPTION_KEY is not set"):
                _get_key()

def test_get_key_invalid_hex():
    with patch.object(settings, "ENCRYPTION_KEY", "invalid hex string"):
        with pytest.raises(RuntimeError, match="must be a valid 64-character hex string"):
            _get_key()

def test_get_key_wrong_length():
    with patch.object(settings, "ENCRYPTION_KEY", "0123456789abcdef"): # too short
        with pytest.raises(RuntimeError, match="must encode exactly 32 bytes"):
            _get_key()

def test_get_key_valid():
    valid_key_hex = secrets.token_hex(32)
    with patch.object(settings, "ENCRYPTION_KEY", valid_key_hex):
        key = _get_key()
        assert key == bytes.fromhex(valid_key_hex)

def test_encrypt_decrypt_roundtrip():
    plaintext = "Sensitive data 123 !@#"
    encrypted = encrypt(plaintext)
    assert encrypted != plaintext
    assert decrypt(encrypted) == plaintext

def test_encrypt_distinct_ciphertexts():
    plaintext = "Same text"
    # IV should be random, so two encryptions of same text should differ
    e1 = encrypt(plaintext)
    e2 = encrypt(plaintext)
    assert e1 != e2
    assert decrypt(e1) == plaintext
    assert decrypt(e2) == plaintext

def test_encrypted_string_type_decorator():
    decorator = EncryptedString()
    
    # process_bind_param (write)
    assert decorator.process_bind_param(None, None) is None
    val = "secret"
    encrypted = decorator.process_bind_param(val, None)
    assert encrypted != val
    
    # process_result_value (read)
    assert decorator.process_result_value(None, None) is None
    assert decorator.process_result_value(encrypted, None) == val
    
    # Graceful failure for invalid/unencrypted data
    assert decorator.process_result_value("not-base64-!", None) == "not-base64-!"
    assert decorator.process_result_value("bm90LWVuY3J5cHRlZA==", None) == "bm90LWVuY3J5cHRlZA==" # base64 for "not-encrypted" but too short for IV 
