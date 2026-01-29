from contextlib import asynccontextmanager

import boto3
from botocore.exceptions import ClientError
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    annotations,
    auth,
    documents,
    inventory,
    materials,
    projects,
    reports,
    transfers,
    users,
    warehouses,
)
from app.core.config import settings


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
    yield
    # Shutdown
    pass


app = FastAPI(
    title="ErgoLab API",
    description="Field Service Management API",
    version="1.0.0",
    lifespan=lifespan,
)

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
app.include_router(users.router)


@app.get("/")
def read_root():
    return {"message": "ErgoLab API is running"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
