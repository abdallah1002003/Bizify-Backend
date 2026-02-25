"""
AES-256-GCM transparent column encryption for SQLAlchemy.

Usage:
    from app.core.encryption import EncryptedString

    class MyModel(Base):
        token_ref = Column(EncryptedString, nullable=False)

The column is stored in the DB as: base64(iv + ciphertext + tag)
Reads/writes are completely transparent to the application layer.

Requires ENCRYPTION_KEY in settings — a 64-character hex string (32 bytes).
Generate one with: python -c "import secrets; print(secrets.token_hex(32))"
"""

import base64
import os
from typing import Any, Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sqlalchemy import String
from sqlalchemy.types import TypeDecorator

from config.settings import settings

_IV_LENGTH = 12   # 96-bit IV (GCM standard)
_TAG_LENGTH = 16  # 128-bit auth tag (GCM standard)


def _get_key() -> bytes:
    """Derive a 32-byte key from the hex-encoded ENCRYPTION_KEY setting."""
    raw = settings.ENCRYPTION_KEY.strip()
    if not raw:
        if settings.APP_ENV == "test":
            # Use a fixed test key so unit tests don't need the env var
            return bytes.fromhex("00" * 32)
        raise RuntimeError(
            "ENCRYPTION_KEY is not set. "
            "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
        )
    try:
        key = bytes.fromhex(raw)
    except ValueError as exc:
        raise RuntimeError("ENCRYPTION_KEY must be a valid 64-character hex string (32 bytes).") from exc
    if len(key) != 32:
        raise RuntimeError(f"ENCRYPTION_KEY must encode exactly 32 bytes, got {len(key)}.")
    return key


def encrypt(plaintext: str) -> str:
    """Encrypt a string. Returns base64-encoded iv+ciphertext."""
    key = _get_key()
    iv = os.urandom(_IV_LENGTH)
    aesgcm = AESGCM(key)
    ciphertext_with_tag = aesgcm.encrypt(iv, plaintext.encode(), associated_data=None)
    return base64.b64encode(iv + ciphertext_with_tag).decode()


def decrypt(blob: str) -> str:
    """Decrypt a base64-encoded iv+ciphertext string. Returns the original plaintext."""
    key = _get_key()
    raw = base64.b64decode(blob)
    iv = raw[:_IV_LENGTH]
    ciphertext_with_tag = raw[_IV_LENGTH:]
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(iv, ciphertext_with_tag, associated_data=None).decode()


class EncryptedString(TypeDecorator):
    """
    SQLAlchemy column type that encrypts values on write and decrypts on read.

    The underlying DB column is VARCHAR — encrypted values are slightly longer
    than the originals due to IV + auth tag + base64 overhead (~56 chars extra).
    """

    impl = String
    cache_ok = True

    def process_bind_param(self, value: Optional[str], dialect: Any) -> Optional[str]:
        """Encrypt before writing to DB."""
        if value is None:
            return None
        return encrypt(value)

    def process_result_value(self, value: Optional[str], dialect: Any) -> Optional[str]:
        """Decrypt after reading from DB."""
        if value is None:
            return None
        try:
            return decrypt(value)
        except Exception:
            # If decryption fails (e.g. migrating unencrypted legacy data),
            # return the raw value and let the application handle it gracefully.
            return value
