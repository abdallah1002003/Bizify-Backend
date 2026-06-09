import sys
from typing import Optional

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Known insecure development default — must never be used in production.
_INSECURE_SECRET_KEY = "your-super-secret-key-for-dev-only"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    PROJECT_NAME: str = "Bizify"
    API_V1_STR: str = "/api/v1"

    # Expose interactive API docs (/docs, /redoc). Enabled by default.
    ENABLE_DOCS: bool = True

    POSTGRES_SERVER: Optional[str] = None
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_DB: Optional[str] = None
    DATABASE_URL: Optional[str] = None

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_URL: Optional[str] = None

    SECRET_KEY: str = _INSECURE_SECRET_KEY
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080

    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = 587
    SMTP_HOST: Optional[str] = "smtp.gmail.com"
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[str] = None

    SESSION_TIMEOUT_MINUTES: int = 240
    SESSION_WARNING_MINUTES: int = 5

    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    PAYPAL_CLIENT_ID: Optional[str] = None
    PAYPAL_CLIENT_SECRET: Optional[str] = None
    PAYPAL_MODE: str = "sandbox"
    PAYPAL_WEBHOOK_ID: Optional[str] = None
    FRONTEND_URL: str = "http://localhost:3000"

    # Paymob (Visa / Mastercard)
    PAYMOB_API_KEY: Optional[str] = None
    PAYMOB_HMAC_SECRET: Optional[str] = None
    PAYMOB_INTEGRATION_ID: Optional[int] = None
    PAYMOB_IFRAME_ID: Optional[str] = None

    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None

    SUPABASE_URL: Optional[str] = None
    SUPABASE_KEY: Optional[str] = None
    SUPABASE_BUCKET_NAME: str = "partner-documents"

    AI_PIPELINE_BASE_URL: str = "https://bizifyai-production.up.railway.app"
    AI_PIPELINE_API_KEY: Optional[str] = None

    RESEND_API_KEY: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=None if "pytest" in sys.modules else ".env",
        case_sensitive=True,
        extra="ignore",
    )

    @model_validator(mode="after")
    def _enforce_secure_secret_key(self) -> "Settings":
        """Refuse to boot in production with a missing/insecure JWT signing key."""
        if "pytest" in sys.modules:
            return self
        if not self.SECRET_KEY or self.SECRET_KEY == _INSECURE_SECRET_KEY:
            raise RuntimeError(
                "SECRET_KEY must be set to a strong, unique value in production "
                "(it is currently missing or using the insecure development default)."
            )
        return self

    def get_database_url(self) -> str:
        """Return the configured database URL or build it from components."""
        if self.DATABASE_URL:
            return self.DATABASE_URL

        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"
        )


settings = Settings()
