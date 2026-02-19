from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/invoice_db"
    SECRET_KEY: str = "your-jwt-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days
    RESEND_API_KEY: str = ""
    EMAIL_FROM: str = "invoices@yourdomain.com"

    model_config = {"env_file": ".env"}


settings = Settings()
