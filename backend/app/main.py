from contextlib import asynccontextmanager

import boto3
from botocore.exceptions import ClientError
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    analytics,
    annotations,
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
from app.core.config import settings
from app.core.metrics import MetricsMiddleware, metrics, get_health_status


def ensure_s3_bucket():
    """Ensure the S3 bucket exists on startup."""
    s3_client = boto3.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT,
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
    )
    try:
        s3_client.head_bucket(Bucket=settings.S3_BUCKET)
        print(f"S3 bucket '{settings.S3_BUCKET}' exists")
    except ClientError:
        try:
            s3_client.create_bucket(Bucket=settings.S3_BUCKET)
            print(f"S3 bucket '{settings.S3_BUCKET}' created")
        except Exception as e:
            print(f"Warning: Could not create S3 bucket: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    ensure_s3_bucket()
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

# Add performance monitoring middleware
app.add_middleware(MetricsMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
app.include_router(reports_full.router, prefix="/api/reports", tags=["Reports System"])


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
