from typing import List, Optional, cast
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session
import base64

from app.api.auth import get_current_user
from app.core.database import get_db
from app.core.cache import cache, CacheKeys
from app.core.config import settings
from app.models.material import Material
from app.models.user import User
from app.schemas.material import MaterialCreate, MaterialResponse, MaterialUpdate
from app.services.qr_service import qr_service
from app.services.audit_service import AuditService

router = APIRouter(prefix="/api/materials", tags=["Materials"])


@router.get("/", response_model=List[MaterialResponse])
def get_materials(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return (max 1000)"),
    category: Optional[str] = Query(None, max_length=100, pattern=r'^[a-zA-Z0-9\s\-_]+$'),
    db: Session = Depends(get_db),
):
    # Sanitize category input
    if category:
        category = category.strip()

    # Try cache first
    cache_key = CacheKeys.materials_list(page=skip // max(limit, 1), category=category)
    cached_data = cache.get(cache_key)
    if cached_data:
        return cached_data
    
    query = db.query(Material)
    if category:
        query = query.filter(Material.category == category)
    materials = query.offset(skip).limit(limit).all()
    
    # Convert to dict for caching
    result = []
    for m in materials:
        # Convert Decimal to float safely
        unit_price_float: Optional[float] = None
        if m.unit_price is not None:
            unit_price_float = float(cast(Decimal, m.unit_price))

        result.append({
            "id": m.id,
            "name": m.name,
            "sku": m.sku,
            "category": m.category,
            "unit": m.unit,
            "unit_price": unit_price_float,
            "barcode": m.barcode,
            "min_stock_level": m.min_stock_level,
            "description": m.description,
        })
    
    # Use configurable TTL
    cache.set(cache_key, result, expire=settings.CACHE_TTL_LONG)
    return result


@router.post("/", response_model=MaterialResponse, status_code=status.HTTP_201_CREATED)
def create_material(
    material: MaterialCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = db.query(Material).filter(Material.sku == material.sku).first()
    if existing:
        raise HTTPException(status_code=400, detail="SKU already exists")

    db_material = Material(**material.dict())
    db.add(db_material)
    db.commit()
    db.refresh(db_material)
    
    # Audit log
    AuditService.log_action(
        db=db,
        user=current_user,
        action="CREATE",
        table_name="materials",
        record_id=db_material.id,
        new_values=material.dict(),
        request=request,
    )
    
    # Invalidate cache AFTER successful commit
    cache.clear_pattern("materials:*")
    
    return db_material


@router.get("/{material_id}", response_model=MaterialResponse)
def get_material(material_id: int, db: Session = Depends(get_db)):
    # Try cache first
    cache_key = CacheKeys.materials_detail(material_id)
    cached_data = cache.get(cache_key)
    if cached_data:
        return cached_data
    
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    # Get unit_price value for proper type handling
    unit_price_value = material.unit_price
    
    # Use configurable TTL
    cache.set(cache_key, {
        "id": material.id,
        "name": material.name,
        "sku": material.sku,
        "category": material.category,
        "unit": material.unit,
        "unit_price": float(cast(Decimal, unit_price_value)) if unit_price_value is not None else None,
        "barcode": material.barcode,
        "min_stock_level": material.min_stock_level,
        "description": material.description,
    }, expire=settings.CACHE_TTL_LONG)
    
    return material


@router.put("/{material_id}", response_model=MaterialResponse)
def update_material(
    material_id: int,
    material_update: MaterialUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")

    # Capture old values
    old_values = {
        "name": material.name,
        "sku": material.sku,
        "category": material.category,
        "unit": material.unit,
        "unit_price": float(material.unit_price) if material.unit_price is not None else None,
        "barcode": material.barcode,
        "min_stock_level": material.min_stock_level,
        "description": material.description,
    }

    for key, value in material_update.dict(exclude_unset=True).items():
        setattr(material, key, value)

    db.commit()
    db.refresh(material)
    
    # Audit log
    AuditService.log_action(
        db=db,
        user=current_user,
        action="UPDATE",
        table_name="materials",
        record_id=material_id,
        old_values=old_values,
        new_values=material_update.dict(exclude_unset=True),
        request=request,
    )
    
    # Invalidate cache AFTER successful commit
    cache.delete(CacheKeys.materials_detail(material_id))
    cache.clear_pattern("materials:list:*")
    
    return material


@router.delete("/{material_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_material(
    material_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")

    # Capture old values
    old_values = {
        "name": material.name,
        "sku": material.sku,
        "category": material.category,
    }

    db.delete(material)
    db.commit()
    
    # Audit log
    AuditService.log_action(
        db=db,
        user=current_user,
        action="DELETE",
        table_name="materials",
        record_id=material_id,
        old_values=old_values,
        request=request,
    )
    
    # Invalidate cache AFTER successful commit
    cache.delete(CacheKeys.materials_detail(material_id))
    cache.clear_pattern("materials:list:*")
    
    return None


@router.get("/{material_id}/qr")
def get_material_qr(
    material_id: int,
    format: str = "base64",
    printable: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")

    qr_base64 = qr_service.generate_material_qr(
        material_id=material.id,
        sku=material.sku,
        name=material.name,
        category=material.category or "",
    )

    if printable:
        label = qr_service.generate_printable_label(
            qr_base64=qr_base64,
            title=material.name,
            subtitle=f"SKU: {material.sku}",
            info_text=f"Category: {material.category or '-'}",
        )

        if format == "png":
            img_data = base64.b64decode(label.split(",")[1])
            return Response(content=img_data, media_type="image/png")
        return {"qr_code": label, "material_id": material_id}

    if format == "png":
        img_data = base64.b64decode(qr_base64.split(",")[1])
        return Response(content=img_data, media_type="image/png")

    return {
        "qr_code": qr_base64,
        "material_id": material_id,
        "sku": material.sku,
        "name": material.name,
    }


@router.get("/qr/batch")
def generate_batch_qr(
    material_ids: str = Query(..., max_length=2000),  # Limit URL length
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate QR codes for multiple materials.
    
    Limits:
    - Maximum 100 materials per request
    - Maximum URL length of 2000 characters
    
    For larger batches, make multiple requests.
    """
    # Parse and validate IDs
    try:
        ids = [int(item_id.strip()) for item_id in material_ids.split(",") if item_id.strip()]
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid material ID format. Use comma-separated integers."
        )
    
    # Enforce batch size limit
    if len(ids) > 100:
        raise HTTPException(
            status_code=400,
            detail=f"Batch size exceeds maximum. Requested: {len(ids)}, Maximum: 100. "
                   f"Please split your request into multiple batches."
        )
    
    if not ids:
        raise HTTPException(
            status_code=400,
            detail="No valid material IDs provided"
        )
    
    # Remove duplicates and fetch materials
    unique_ids = list(set(ids))
    materials = db.query(Material).filter(Material.id.in_(unique_ids)).all()
    
    # Check if all requested materials were found
    found_ids = {m.id for m in materials}
    missing_ids = set(unique_ids) - found_ids
    if missing_ids:
        raise HTTPException(
            status_code=404,
            detail=f"Materials not found: {sorted(missing_ids)}"
        )

    qr_codes = []
    for material in materials:
        qr_base64 = qr_service.generate_material_qr(
            material_id=material.id,
            sku=material.sku,
            name=material.name,
            category=material.category or "",
        )
        qr_codes.append({
            "material_id": material.id,
            "sku": material.sku,
            "name": material.name,
            "qr_code": qr_base64,
        })

    return {
        "total": len(qr_codes),
        "qr_codes": qr_codes
    }
