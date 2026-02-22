import os

from pydantic import ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_ENV: str = "development"
    DATABASE_URL: str = "postgresql+psycopg2://localhost:5432/postgres"
    SECRET_KEY: str = "change-me-in-env"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    AUTO_CREATE_TABLES: bool = False
    VERIFY_DB_ON_STARTUP: bool = True
    CORS_ALLOWED_ORIGINS: str = (
        "http://localhost:3000,http://127.0.0.1:3000,"
        "http://localhost:5173,http://127.0.0.1:5173"
    )
    CORS_ALLOW_CREDENTIALS: bool = True
    RATE_LIMIT_PER_MINUTE: int = 120

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

    @property
    def cors_allowed_origins_list(self) -> list[str]:
        origins = [origin.strip() for origin in self.CORS_ALLOWED_ORIGINS.split(",") if origin.strip()]
        return origins or ["http://localhost:3000"]


settings = Settings()
