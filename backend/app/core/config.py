from typing import List, Optional
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database - Required
    DATABASE_URL: str
    
    # Redis - Default for containerized environment
    REDIS_URL: str = "redis://redis:6379/0"
    
    # S3/MinIO - Optional with defaults for testing/CI
    S3_ENDPOINT: str = "http://minio:9000"
    S3_PUBLIC_ENDPOINT: str = "http://localhost:9000"  # Public URL for browser access
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET: str = "ergolab-files"
    
    # Security - Default for testing/CI (CHANGE IN PRODUCTION!)
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS - Comma-separated list of allowed origins
    # Example: CORS_ORIGINS="http://localhost:3000,https://app.ergolab.gr"
    CORS_ORIGINS: str = "http://localhost:3000"

    # SMTP settings - All optional, will disable email if not configured
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_TLS: bool = True
    SMTP_FROM_EMAIL: str = "noreply@ergolab.com"
    SMTP_FROM_NAME: str = "ErgoLab"

    # Frontend URL for links
    FRONTEND_URL: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS_ORIGINS into a list"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(',') if origin.strip()]

    @property
    def smtp_configured(self) -> bool:
        """Check if SMTP is properly configured"""
        return bool(self.SMTP_HOST and self.SMTP_USER and self.SMTP_PASSWORD)

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
