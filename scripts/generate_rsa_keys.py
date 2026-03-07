#!/usr/bin/env python3
"""
Generate a 4096-bit RSA key pair for RS256 JWT signing.

Usage:
    python scripts/generate_rsa_keys.py

Output:
    Two PEM-encoded keys ready to paste into .env as:
        JWT_PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----\\n..."
        JWT_PUBLIC_KEY="-----BEGIN PUBLIC KEY-----\\n..."

WARNING: Keep the private key secret. Never commit it to source control.
"""

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend


def generate_rsa_keypair(key_size: int = 4096) -> tuple[str, str]:
    """Return (private_pem, public_pem) as single-line escaped strings."""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size,
        backend=default_backend(),
    )

    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()

    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()

    return private_pem, public_pem


def to_env_value(pem: str) -> str:
    """Escape newlines so the key fits on a single .env line."""
    return pem.replace("\n", "\\n")


if __name__ == "__main__":
    print("Generating 4096-bit RSA key pair for RS256 JWT signing...")
    print("This may take a few seconds.\n")

    private_pem, public_pem = generate_rsa_keypair()

    print("=" * 70)
    print("Add these lines to your .env file (production only):")
    print("=" * 70)
    print(f'JWT_PRIVATE_KEY="{to_env_value(private_pem)}"')
    print(f'JWT_PUBLIC_KEY="{to_env_value(public_pem)}"')
    print("=" * 70)
    print("\nWARNING: Keep JWT_PRIVATE_KEY secret. Do NOT commit to git.")
    print("Add .env to .gitignore if not already done.")
