from typing import List, Optional
from functools import lru_cache
import re

from pydantic import model_validator
from pydantic_settings import BaseSettings

# CORS origin regex (scheme://host[:port], no path)
URL_PATTERN = re.compile(
    r'^https?://'  # http:// or https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
    r'localhost|'  # localhost
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
    r'(?::\d+)?$', re.IGNORECASE  # optional port, anchored end
)


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
    EMAIL_HASH_KEY: str = "dev-email-hash-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Cache TTL settings (in seconds)
    CACHE_TTL_SHORT: int = 120      # 2 minutes - for frequently changing data
    CACHE_TTL_MEDIUM: int = 300     # 5 minutes - for moderate changes
    CACHE_TTL_LONG: int = 600       # 10 minutes - for stable data
    CACHE_TTL_DASHBOARD: int = 60   # 1 minute - for dashboard/analytics
    
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

    # Proxy Configuration
    TRUST_PROXY_HEADERS: bool = True  # Set to True only if behind a trusted reverse proxy (e.g. Nginx/ALB)

    @property
    def is_production(self) -> bool:
        """Detect if running in production environment"""
        import os
        return os.getenv('ENVIRONMENT', 'development').lower() == 'production'

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse and validate CORS_ORIGINS into a list"""
        origins = [origin.strip() for origin in self.CORS_ORIGINS.split(',') if origin.strip()]
        
        for origin in origins:
            if not URL_PATTERN.match(origin):
                raise ValueError(f"Invalid CORS origin: {origin} (paths not allowed)")
        
        return origins

    @property
    def smtp_configured(self) -> bool:
        """Check if SMTP is properly configured"""
        return bool(self.SMTP_HOST and self.SMTP_USER and self.SMTP_PASSWORD)

    @model_validator(mode="after")
    def validate_production_settings_validator(self) -> "Settings":
        """Run production validation after model assignment"""
        try:
            self.validate_production_settings()
        except ValueError as e:
            # We catch and print here if we want to mimic the old behavior, 
            # OR we let it bubble up. 
            # The prompt implies we want it "wired into the lifecycle". 
            # Since the original method raises ValueError, Pydantic will wrap this in a ValidationError 
            # if we let it bubble.
            # However, for cleaner error messages on startup, re-raising or letting it crash is fine.
            raise e
        return self

    def validate_production_settings(self) -> None:
        """Enhanced production validation"""
        import sys
        
        if not self.is_production:
            print("ℹ️  Running in DEVELOPMENT mode", file=sys.stderr)
            return
        
        print("🚀 Running in PRODUCTION mode - validating security...", file=sys.stderr)
        
        # 1. SECRET_KEY validation
        if self.SECRET_KEY == "dev-secret-key-change-in-production":
            raise ValueError(
                "🔒 SECURITY ERROR: SECRET_KEY must be changed from default value!\n"
                "Generate a secure key with: openssl rand -hex 32\n"
                "Then set SECRET_KEY environment variable."
            )
        
        if len(self.SECRET_KEY) < 32:
            raise ValueError(
                f"🔒 SECURITY ERROR: SECRET_KEY must be at least 32 characters long!\n"
                f"Current length: {len(self.SECRET_KEY)} characters"
            )
        
        # 2. MinIO/S3 credentials validation
        if self.S3_ACCESS_KEY == "minioadmin" or self.S3_SECRET_KEY == "minioadmin":
            raise ValueError(
                "🔒 SECURITY ERROR: Default MinIO credentials detected!\n"
                "Change S3_ACCESS_KEY and S3_SECRET_KEY before deploying to production."
            )
        
        # 3. CORS validation
        from urllib.parse import urlparse
        
        origins_to_check = self.CORS_ORIGINS.split(',') if isinstance(self.CORS_ORIGINS, str) else self.CORS_ORIGINS
        has_localhost = False
        
        for origin in origins_to_check:
            origin = origin.strip()
            if not origin:
                continue
                
            # Iterate parsed origins to be robust
            target = origin if "://" in origin else f"http://{origin}"
            try:
                hostname = urlparse(target).hostname
            except ValueError:
                hostname = None
                
            if hostname in ("localhost", "127.0.0.1"):
                has_localhost = True
                break

        if has_localhost:
            print(
                "⚠️  WARNING: CORS_ORIGINS contains 'localhost' or '127.0.0.1'. "
                "Ensure this is intentional for production!",
                file=sys.stderr
            )
        
        # 4. Database URL validation
        if "localhost" in self.DATABASE_URL or "127.0.0.1" in self.DATABASE_URL:
            print(
                "⚠️  WARNING: DATABASE_URL points to localhost. "
                "Ensure this is intentional for production!",
                file=sys.stderr
            )
        
        print("✅ Production security validation passed!", file=sys.stderr)

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
