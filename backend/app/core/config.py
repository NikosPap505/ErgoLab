from typing import List
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str = "redis://redis:6379/0"
    S3_ENDPOINT: str
    S3_PUBLIC_ENDPOINT: str = "http://localhost:9000"  # Public URL for browser access
    S3_ACCESS_KEY: str
    S3_SECRET_KEY: str
    S3_BUCKET: str = "ergolab-files"
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    CORS_ORIGINS: str = "http://localhost:3000"

    # SMTP settings
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_TLS: bool = True
    SMTP_FROM_EMAIL: str = "noreply@ergolab.com"
    SMTP_FROM_NAME: str = "ErgoLab"


    # Frontend URL for links
    FRONTEND_URL: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        return [item.strip() for item in self.CORS_ORIGINS.split(",") if item.strip()]

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
