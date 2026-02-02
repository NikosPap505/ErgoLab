from typing import List, Dict, Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.core.database import get_db
from app.core.cache import cache, CacheKeys
from app.models.inventory import InventoryStock, StockTransaction, TransactionType
from app.models.material import Material
from app.models.notification import NotificationPreferences
from app.models.user import User, UserRole
from app.models.warehouse import Warehouse
from app.schemas.inventory import InventoryStockResponse, StockTransactionCreate
from app.services.email_service import EmailService
from app.services.fcm_service import FCMService

router = APIRouter(prefix="/api/inventory", tags=["Inventory"])


class ScanData(BaseModel):
    type: str
    id: int
    action: str
    additional_data: Dict[str, Any] = {}


@router.get("/warehouse/{warehouse_id}", response_model=List[InventoryStockResponse])
def get_warehouse_inventory(warehouse_id: int, db: Session = Depends(get_db)):
    # Try cache first
    cache_key = CacheKeys.inventory_warehouse(warehouse_id)
    cached_data = cache.get(cache_key)
    if cached_data:
        return cached_data
    
    stocks = (
        db.query(
            InventoryStock.id,
            InventoryStock.warehouse_id,
            InventoryStock.material_id,
            InventoryStock.quantity,
            InventoryStock.last_updated,
            Material.name.label("material_name"),
            Material.sku.label("material_sku"),
            Warehouse.name.label("warehouse_name"),
        )
        .join(Material, InventoryStock.material_id == Material.id)
        .join(Warehouse, InventoryStock.warehouse_id == Warehouse.id)
        .filter(InventoryStock.warehouse_id == warehouse_id)
        .all()
    )

    result = [
        {
            "id": s.id,
            "warehouse_id": s.warehouse_id,
            "material_id": s.material_id,
            "quantity": s.quantity,
            "last_updated": s.last_updated.isoformat() if s.last_updated else None,
            "material_name": s.material_name,
            "material_sku": s.material_sku,
            "warehouse_name": s.warehouse_name,
        }
        for s in stocks
    ]
    
    # Cache for 5 minutes (inventory changes more frequently)
    cache.set(cache_key, result, expire=300)
    
    return result


@router.get("/low-stock", response_model=List[InventoryStockResponse])
def get_low_stock_materials(db: Session = Depends(get_db)):
    # Try cache first
    cache_key = CacheKeys.inventory_low_stock()
    cached_data = cache.get(cache_key)
    if cached_data:
        return cached_data
    
    stocks = (
        db.query(
            InventoryStock.id,
            InventoryStock.warehouse_id,
            InventoryStock.material_id,
            InventoryStock.quantity,
            InventoryStock.last_updated,
            Material.name.label("material_name"),
            Material.sku.label("material_sku"),
            Warehouse.name.label("warehouse_name"),
        )
        .join(Material, InventoryStock.material_id == Material.id)
        .join(Warehouse, InventoryStock.warehouse_id == Warehouse.id)
        .filter(InventoryStock.quantity <= Material.min_stock_level)
        .all()
    )

    result = [
        {
            "id": s.id,
            "warehouse_id": s.warehouse_id,
            "material_id": s.material_id,
            "quantity": s.quantity,
            "last_updated": s.last_updated.isoformat() if s.last_updated else None,
            "material_name": s.material_name,
            "material_sku": s.material_sku,
            "warehouse_name": s.warehouse_name,
        }
        for s in stocks
    ]
    
    # Cache for 2 minutes (low stock alerts should be fresh)
    cache.set(cache_key, result, expire=120)
    
    return result


@router.post("/transaction", status_code=status.HTTP_201_CREATED)
async def create_stock_transaction(
    transaction: StockTransactionCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    warehouse = db.query(Warehouse).filter(Warehouse.id == transaction.warehouse_id).first()
    if not warehouse:
        raise HTTPException(status_code=404, detail="Warehouse not found")

    material = db.query(Material).filter(Material.id == transaction.material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")

    stock = (
        db.query(InventoryStock)
        .filter(
            InventoryStock.warehouse_id == transaction.warehouse_id,
            InventoryStock.material_id == transaction.material_id,
        )
        .first()
    )

    if not stock:
        stock = InventoryStock(
            warehouse_id=transaction.warehouse_id,
            material_id=transaction.material_id,
            quantity=0,
        )
        db.add(stock)

    if transaction.transaction_type in [
        TransactionType.PURCHASE,
        TransactionType.TRANSFER_IN,
        TransactionType.RETURN,
    ]:
        stock.quantity += transaction.quantity  # type: ignore[assignment,operator]
    elif transaction.transaction_type in [
        TransactionType.TRANSFER_OUT,
        TransactionType.CONSUMPTION,
    ]:
        current_qty: int = stock.quantity  # type: ignore[assignment]
        if current_qty < transaction.quantity:
            raise HTTPException(status_code=400, detail="Insufficient stock")
        stock.quantity -= transaction.quantity  # type: ignore[assignment,operator]
    elif transaction.transaction_type == TransactionType.ADJUSTMENT:
        stock.quantity = transaction.quantity  # type: ignore[assignment]

    total_cost = (
        transaction.unit_cost * transaction.quantity if transaction.unit_cost is not None else None
    )
    db_transaction = StockTransaction(
        warehouse_id=transaction.warehouse_id,
        material_id=transaction.material_id,
        transaction_type=transaction.transaction_type,
        quantity=transaction.quantity,
        unit_cost=transaction.unit_cost,
        total_cost=total_cost,
        notes=transaction.notes,
        user_id=current_user.id,
    )
    db.add(db_transaction)

    db.commit()
    db.refresh(stock)
    
    # Invalidate relevant caches
    cache.delete(CacheKeys.inventory_warehouse(transaction.warehouse_id))
    cache.delete(CacheKeys.inventory_low_stock())
    cache.clear_pattern("inventory:*")
    cache.clear_pattern("dashboard:*")

    if stock.material and stock.quantity <= (stock.material.min_stock_level or 0):
        admins = (
            db.query(User)
            .filter(User.role.in_([UserRole.ADMIN, UserRole.MANAGER]))
            .all()
        )

        for admin in admins:
            if not admin.email:
                continue

            prefs = (
                db.query(NotificationPreferences)
                .filter(NotificationPreferences.user_id == admin.id)
                .first()
            )

            if prefs and not prefs.email_low_stock:
                continue

            background_tasks.add_task(
                EmailService.send_low_stock_alert,
                recipient=admin.email,
                material_name=stock.material.name,
                sku=stock.material.sku,
                current_quantity=stock.quantity,
                minimum_quantity=stock.material.min_stock_level or 0,
                warehouse_name=stock.warehouse.name if stock.warehouse else "",
            )

        await FCMService.send_to_role(
            db=db,
            role="manager",
            title="⚠️ Χαμηλό Απόθεμα",
            body=(
                f"{stock.material.name} - Απομένουν {stock.quantity} "
                f"{stock.material.unit.value if hasattr(stock.material.unit, 'value') else stock.material.unit}"
            ),
            data={
                "type": "low_stock",
                "material_id": str(stock.material.id),
                "warehouse_id": str(stock.warehouse_id),
                "screen": "MaterialDetail",
            },
        )

        await FCMService.send_to_role(
            db=db,
            role="admin",
            title="⚠️ Χαμηλό Απόθεμα",
            body=(
                f"{stock.material.name} - Απομένουν {stock.quantity} "
                f"{stock.material.unit.value if hasattr(stock.material.unit, 'value') else stock.material.unit}"
            ),
            data={
                "type": "low_stock",
                "material_id": str(stock.material.id),
                "warehouse_id": str(stock.warehouse_id),
                "screen": "MaterialDetail",
            },
        )

    return {"message": "Transaction completed", "new_quantity": stock.quantity}


@router.post("/scan")
def handle_qr_scan(
    scan_data: ScanData,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if scan_data.type == "material":
        material = db.query(Material).filter(Material.id == scan_data.id).first()
        if not material:
            raise HTTPException(status_code=404, detail="Material not found")

        stocks = (
            db.query(InventoryStock)
            .join(Warehouse, InventoryStock.warehouse_id == Warehouse.id)
            .filter(InventoryStock.material_id == scan_data.id)
            .all()
        )

        return {
            "type": "material",
            "data": {
                "id": material.id,
                "sku": material.sku,
                "name": material.name,
                "category": material.category,
                "unit": material.unit.value if hasattr(material.unit, "value") else str(material.unit),
                "cost": float(material.unit_price) if material.unit_price is not None else 0,
                "stocks": [
                    {
                        "warehouse_id": stock.warehouse_id,
                        "warehouse_name": stock.warehouse.name if stock.warehouse else "",
                        "quantity": stock.quantity,
                    }
                    for stock in stocks
                ],
            },
        }

    if scan_data.type == "equipment":
        return {"type": "equipment", "message": "Equipment scanning coming soon"}

    if scan_data.type == "worker":
        user = db.query(User).filter(User.id == scan_data.id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Worker not found")

        role_value = user.role.value if hasattr(user.role, "value") else str(user.role)
        return {
            "type": "worker",
            "data": {
                "id": user.id,
                "username": user.username,
                "full_name": user.full_name,
                "role": role_value,
            },
        }

    raise HTTPException(status_code=400, detail="Unknown QR type")
