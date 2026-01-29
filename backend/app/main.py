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

app = FastAPI(
    title="ErgoLab API",
    description="Field Service Management API",
    version="1.0.0",
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
