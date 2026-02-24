import os

from pydantic import ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_ENV: str = "development"
    DATABASE_URL: str = "postgresql+psycopg2://localhost:5432/postgres"
    SECRET_KEY: str = "change-me-in-env"
    ALGORITHM: str = "HS256"  # Used only as fallback when RSA keys are absent
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # RS256 asymmetric keys (production). When set, RS256 is used automatically.
    # Leave empty in dev/test to use HS256 + SECRET_KEY instead.
    # Generate with: python scripts/generate_rsa_keys.py
    JWT_PRIVATE_KEY: str = ""   # PEM-encoded RSA private key (signing)
    JWT_PUBLIC_KEY: str = ""    # PEM-encoded RSA public key  (verification)
    AUTO_CREATE_TABLES: bool = False
    VERIFY_DB_ON_STARTUP: bool = True
    CORS_ALLOWED_ORIGINS: str = (
        "http://localhost:3000,http://127.0.0.1:3000,"
        "http://localhost:5173,http://127.0.0.1:5173"
    )
    CORS_ALLOW_CREDENTIALS: bool = True
    RATE_LIMIT_PER_MINUTE: int = 120
    REDIS_ENABLED: bool = False
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    ALLOW_ADMIN_BOOTSTRAP: bool = False
    ADMIN_BOOTSTRAP_TOKEN: str = ""
    AI_PROVIDER: str = "mock"
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_CHAT_MODEL: str = "gpt-4.1-mini"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    AI_REQUEST_TIMEOUT_SECONDS: int = 30

    # Email / SMTP
    MAIL_ENABLED: bool = True
    MAIL_USERNAME: str = ""
    MAIL_PASSWORD: str = ""
    MAIL_FROM: str = "noreply@bizify.app"
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_PORT: int = 587
    MAIL_TLS: bool = True
    MAIL_SSL: bool = False
    FRONTEND_URL: str = "http://localhost:3000"

    # Stripe Payments
    STRIPE_ENABLED: bool = False
    STRIPE_SECRET_KEY: str = ""         # sk_live_... or sk_test_...
    STRIPE_WEBHOOK_SECRET: str = ""     # whsec_... from Stripe dashboard

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        # Support legacy postgres:// URLs from some providers.
        if isinstance(value, str) and value.startswith("postgres://"):
            return value.replace("postgres://", "postgresql://", 1)
        return value

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, value: str, info: ValidationInfo) -> str:
        if not value or not value.strip():
            raise ValueError("DATABASE_URL must not be empty")

        if value.startswith(("postgresql://", "postgresql+")):
            return value

        app_env = str(info.data.get("APP_ENV", os.getenv("APP_ENV", "development"))).lower()
        if app_env == "test" and value.startswith("sqlite://"):
            return value

        raise ValueError(
            "DATABASE_URL must be PostgreSQL in normal runtime. "
            "SQLite is allowed only when APP_ENV=test."
        )

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, value: str, info: ValidationInfo) -> str:
        if not value or not value.strip():
            raise ValueError("SECRET_KEY must not be empty")

        app_env = str(info.data.get("APP_ENV", os.getenv("APP_ENV", "development"))).lower()
        weak_values = {
            "change-me-in-env",
            "replace-with-a-long-random-secret",
            "changeme",
            "secret",
            "default",
        }

        normalized = value.strip()
        if app_env != "test":
            if normalized.lower() in weak_values:
                raise ValueError("SECRET_KEY must be changed from the default placeholder")
            if len(normalized) < 32:
                raise ValueError("SECRET_KEY must be at least 32 characters")

        return normalized

    @field_validator("AI_PROVIDER")
    @classmethod
    def validate_ai_provider(cls, value: str) -> str:
        normalized = value.strip().lower()
        allowed = {"mock", "openai"}
        if normalized not in allowed:
            raise ValueError("AI_PROVIDER must be one of: mock, openai")
        return normalized

    @field_validator("AI_REQUEST_TIMEOUT_SECONDS")
    @classmethod
    def validate_ai_timeout(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("AI_REQUEST_TIMEOUT_SECONDS must be greater than 0")
        return value

    @property
    def jwt_algorithm(self) -> str:
        """RS256 when RSA keys are configured, HS256 otherwise."""
        return "RS256" if self.JWT_PRIVATE_KEY.strip() else "HS256"

    @property
    def jwt_signing_key(self) -> str:
        """Key used to *sign* tokens (RSA private key or shared secret)."""
        return self.JWT_PRIVATE_KEY.strip() if self.JWT_PRIVATE_KEY.strip() else self.SECRET_KEY

    @property
    def jwt_verify_key(self) -> str:
        """Key used to *verify* tokens (RSA public key or shared secret)."""
        pk = self.JWT_PUBLIC_KEY.strip()
        priv = self.JWT_PRIVATE_KEY.strip()
        if priv:
            # Public key required when using RS256
            return pk if pk else priv  # fallback to private key if public not set (not recommended)
        return self.SECRET_KEY

    @property
    def cors_allowed_origins_list(self) -> list[str]:
        origins = [origin.strip() for origin in self.CORS_ALLOWED_ORIGINS.split(",") if origin.strip()]
        return origins or ["http://localhost:3000"]


settings = Settings()
