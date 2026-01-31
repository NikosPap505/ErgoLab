from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.core.database import get_db
from app.core.cache import cache, CacheKeys
from app.models.warehouse import Warehouse
from app.models.user import User
from app.schemas.warehouse import WarehouseCreate, WarehouseResponse, WarehouseUpdate

router = APIRouter(prefix="/api/warehouses", tags=["Warehouses"])


@router.get("/", response_model=List[WarehouseResponse])
def list_warehouses(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    # Try cache first
    cache_key = CacheKeys.warehouses_list()
    cached_data = cache.get(cache_key)
    if cached_data:
        return cached_data
    
    warehouses = db.query(Warehouse).offset(skip).limit(limit).all()
    
    # Convert to dict for caching (include all fields for response model)
    result = [
        {
            "id": w.id,
            "name": w.name,
            "code": w.code,
            "location": w.location,
            "project_id": w.project_id,
            "is_central": w.is_central,
            "created_at": w.created_at.isoformat() if w.created_at else None, # pyright: ignore[reportGeneralTypeIssues]
            "updated_at": w.updated_at.isoformat() if w.updated_at else None,
        }
        for w in warehouses
    ]
    
    # Cache for 10 minutes
    cache.set(cache_key, result, expire=600)
    return result


@router.post("/", response_model=WarehouseResponse, status_code=status.HTTP_201_CREATED)
def create_warehouse(
    payload: WarehouseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = db.query(Warehouse).filter(Warehouse.code == payload.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Warehouse code already exists")

    warehouse = Warehouse(**payload.dict())
    db.add(warehouse)
    db.commit()
    db.refresh(warehouse)
    
    # Invalidate warehouses list cache
    cache.clear_pattern("warehouses:*")
    
    return warehouse


@router.get("/{warehouse_id}", response_model=WarehouseResponse)
def get_warehouse(warehouse_id: int, db: Session = Depends(get_db)):
    # Try cache first
    cache_key = CacheKeys.warehouse_detail(warehouse_id)
    cached_data = cache.get(cache_key)
    if cached_data:
        return cached_data
    
    warehouse = db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
    if not warehouse:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    
    # Cache for 10 minutes
    cache.set(cache_key, {
        "id": warehouse.id,
        "name": warehouse.name,
        "code": warehouse.code,
        "address": warehouse.address,
        "project_id": warehouse.project_id,
        "is_central": warehouse.is_central,
    }, expire=600)
    
    return warehouse


@router.put("/{warehouse_id}", response_model=WarehouseResponse)
def update_warehouse(
    warehouse_id: int,
    payload: WarehouseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    warehouse = db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
    if not warehouse:
        raise HTTPException(status_code=404, detail="Warehouse not found")

    for key, value in payload.dict(exclude_unset=True).items():
        setattr(warehouse, key, value)

    db.commit()
    db.refresh(warehouse)
    
    # Invalidate cache
    cache.delete(CacheKeys.warehouse_detail(warehouse_id))
    cache.clear_pattern("warehouses:list*")
    
    return warehouse


@router.delete("/{warehouse_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_warehouse(
    warehouse_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    warehouse = db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
    if not warehouse:
        raise HTTPException(status_code=404, detail="Warehouse not found")

    db.delete(warehouse)
    db.commit()
    
    # Invalidate cache
    cache.delete(CacheKeys.warehouse_detail(warehouse_id))
    cache.clear_pattern("warehouses:*")
    
    return None
