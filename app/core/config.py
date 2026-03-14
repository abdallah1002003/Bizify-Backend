from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Bizify"
    API_V1_STR: str = "/api/v1"
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    DATABASE_URL: Optional[str] = None
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

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")

    def get_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"

settings = Settings()
