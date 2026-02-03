from contextlib import asynccontextmanager
import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging
import sys

import boto3
from botocore.exceptions import ClientError
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from app.api import (
    analytics,
    annotations,
    audit,
    auth,
    documents,
    inventory,
    materials,
    notifications,
    projects,
    reports,
    transfers,
    users,
    warehouses,
)
from app.api import reports_full
from app.api import websockets
from app.core.config import settings
from app.core.limiter import limiter
from app.core.metrics import MetricsMiddleware, metrics, get_health_status


def _ensure_s3_bucket_sync():
    """Synchronous S3 bucket check/creation - runs in thread pool."""
    s3_client = boto3.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT,
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
    )
    try:
        s3_client.head_bucket(Bucket=settings.S3_BUCKET)
        print(f"✓ S3 bucket '{settings.S3_BUCKET}' exists")
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        if error_code == '404':
            try:
                s3_client.create_bucket(Bucket=settings.S3_BUCKET)
                print(f"✓ S3 bucket '{settings.S3_BUCKET}' created")
            except Exception as create_error:
                print(f"⚠ Warning: Could not create S3 bucket: {create_error}")
        else:
            print(f"⚠ Warning: S3 bucket check failed: {e}")
    except Exception as e:
        print(f"⚠ Warning: Could not connect to S3: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Validate production settings on startup
    try:
        settings.validate_production_settings()
    except ValueError as e:
        logging.error("Production settings validation failed: %s", e)
        sys.exit(1)
    
    # Configurable S3 timeout
    s3_timeout = 30.0 if settings.is_production else 10.0
    
    loop = asyncio.get_running_loop()
    # Use explicit executor for S3 check
    with ThreadPoolExecutor(max_workers=1) as executor:
        try:
            await asyncio.wait_for(
                loop.run_in_executor(executor, _ensure_s3_bucket_sync),
                timeout=s3_timeout
            )
            print("✓ S3 bucket initialized successfully")
        except asyncio.TimeoutError:
            print(f"⚠️  S3 bucket initialization timed out after {s3_timeout}s")
            print("   The application will continue, but file uploads may fail")
        except Exception as e:
            print(f"⚠️  S3 initialization failed: {e}")
            print("   The application will continue, but file uploads may fail")
    
    print("✓ ErgoLab API started with performance monitoring")
    yield
    # Shutdown
    pass


app = FastAPI(
    title="ErgoLab API",
    description="Field Service Management API",
    version="1.0.0",
    lifespan=lifespan,
)
# Configure rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Add performance monitoring middleware
app.add_middleware(MetricsMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "Accept",
        "Origin",
        "X-Requested-With",
    ],
    expose_headers=["Content-Length", "Content-Type"],
    max_age=3600,  # Cache preflight requests for 1 hour
)

# Log CORS configuration on startup
@app.on_event("startup")
async def log_cors_config():
    import sys
    print(f"🌐 CORS enabled for origins: {settings.cors_origins_list}", file=sys.stderr)

app.include_router(materials.router)
app.include_router(inventory.router)
app.include_router(transfers.router)
app.include_router(projects.router)
app.include_router(warehouses.router)
app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(annotations.router)
app.include_router(reports.router)
app.include_router(notifications.router)
app.include_router(users.router)
app.include_router(analytics.router)
app.include_router(audit.router)
app.include_router(reports_full.router, prefix="/api/reports", tags=["Reports System"])
app.include_router(websockets.router)


@app.get("/")
def read_root():
    return {"message": "ErgoLab API is running"}


@app.get("/health")
def health_check():
    """Application health check endpoint"""
    return get_health_status()


@app.get("/metrics")
def get_metrics():
    """Get performance metrics"""
    return metrics.get_stats()


@app.post("/metrics/reset")
def reset_metrics():
    """Reset performance metrics"""
    metrics.reset()
    return {"message": "Metrics reset successfully"}


@app.get("/cache/stats")
def get_cache_stats():
    """Get cache statistics"""
    from app.core.cache import cache
    return cache.get_stats()


@app.post("/cache/clear")
def clear_cache():
    """Clear all cache entries"""
    from app.core.cache import cache
    cache.flush_all()
    return {"message": "Cache cleared successfully"}
