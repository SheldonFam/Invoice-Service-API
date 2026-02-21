from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/invoice_db"
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # 30 minutes
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    RESEND_API_KEY: str = ""
    EMAIL_FROM: str = "invoices@yourdomain.com"
    CORS_ORIGINS: List[str] = ["http://localhost:5173"]

    @field_validator("SECRET_KEY")
    @classmethod
    def secret_key_must_be_strong(cls, v: str) -> str:
        if v in ("", "your-jwt-secret-key", "changeme", "secret"):
            raise ValueError(
                "SECRET_KEY must be set to a strong, unique value. "
                "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(64))\""
            )
        return v

    model_config = {"env_file": ".env"}


settings = Settings()
