from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings and environment variable configuration management.
    Handles defaults, environment variable loading, and nested configurations.
    """

    PROJECT_NAME: str = "Bizify"
    API_V1_STR: str = "/api/v1"
    
    POSTGRES_SERVER: Optional[str] = None
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_DB: Optional[str] = None
    DATABASE_URL: Optional[str] = None
    
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_URL: Optional[str] = None
    
    SECRET_KEY: str = "your-super-secret-key-for-dev-only"
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

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )

    def get_database_url(self) -> str:
        """
        Constructs the SQLAlchemy database URL from settings components.
        Supports both direct URL overrides and individual parameter assembly.
        """
        if self.DATABASE_URL:
            return self.DATABASE_URL
            
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"


settings = Settings()