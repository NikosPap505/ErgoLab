from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session
import base64

from app.api.auth import get_current_user
from app.core.database import get_db
from app.core.cache import cache, CacheKeys
from app.models.material import Material
from app.models.user import User
from app.schemas.material import MaterialCreate, MaterialResponse, MaterialUpdate
from app.services.qr_service import qr_service

router = APIRouter(prefix="/api/materials", tags=["Materials"])


@router.get("/", response_model=List[MaterialResponse])
def get_materials(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
):
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
        unit_price_value = m.unit_price
        result.append({
            "id": m.id,
            "name": m.name,
            "sku": m.sku,
            "category": m.category,
            "unit": m.unit,
            "unit_price": float(unit_price_value) if unit_price_value is not None else None,  # type: ignore[arg-type]
            "barcode": m.barcode,
            "min_stock_level": m.min_stock_level,
            "description": m.description,
        })
    
    # Cache for 10 minutes
    cache.set(cache_key, result, expire=600)
    return materials


@router.post("/", response_model=MaterialResponse, status_code=status.HTTP_201_CREATED)
def create_material(
    material: MaterialCreate,
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
    
    # Invalidate materials list cache
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
    
    # Cache for 10 minutes
    cache.set(cache_key, {
        "id": material.id,
        "name": material.name,
        "sku": material.sku,
        "category": material.category,
        "unit": material.unit,
        "unit_price": float(unit_price_value) if unit_price_value is not None else None,  # type: ignore[arg-type]
        "barcode": material.barcode,
        "min_stock_level": material.min_stock_level,
        "description": material.description,
    }, expire=600)
    
    return material


@router.put("/{material_id}", response_model=MaterialResponse)
def update_material(
    material_id: int,
    material_update: MaterialUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")

    for key, value in material_update.dict(exclude_unset=True).items():
        setattr(material, key, value)

    db.commit()
    db.refresh(material)
    
    # Invalidate cache
    cache.delete(CacheKeys.materials_detail(material_id))
    cache.clear_pattern("materials:list:*")
    
    return material


@router.delete("/{material_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_material(
    material_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")

    db.delete(material)
    db.commit()
    
    # Invalidate cache
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
    material_ids: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ids = [int(item_id) for item_id in material_ids.split(",") if item_id.strip()]
    materials = db.query(Material).filter(Material.id.in_(ids)).all()

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

    return qr_codes
