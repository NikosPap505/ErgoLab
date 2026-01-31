from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.core.database import get_db
from app.models.inventory import InventoryStock, StockTransaction, TransactionType
from app.models.transfer import Transfer, TransferItem, TransferStatus
from app.models.user import User
from app.models.warehouse import Warehouse
from app.schemas.transfer import TransferCreate, TransferResponse

router = APIRouter(prefix="/api/transfers", tags=["Transfers"])


@router.get("/", response_model=List[TransferResponse])
def list_transfers(
    skip: int = 0,
    limit: int = 100,
    status: str | None = None,
    db: Session = Depends(get_db),
):
    """List all transfers"""
    query = db.query(Transfer)
    
    if status:
        query = query.filter(Transfer.status == status)
    
    transfers = query.order_by(Transfer.created_at.desc()).offset(skip).limit(limit).all()
    return transfers


@router.get("/{transfer_id}", response_model=TransferResponse)
def get_transfer(
    transfer_id: int,
    db: Session = Depends(get_db),
):
    """Get a single transfer by ID"""
    transfer = db.query(Transfer).filter(Transfer.id == transfer_id).first()
    if not transfer:
        raise HTTPException(status_code=404, detail="Transfer not found")
    return transfer


@router.post("/", response_model=TransferResponse, status_code=status.HTTP_201_CREATED)
def create_transfer(
    payload: TransferCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from_warehouse = (
        db.query(Warehouse).filter(Warehouse.id == payload.from_warehouse_id).first()
    )
    if not from_warehouse:
        raise HTTPException(status_code=404, detail="From warehouse not found")

    to_warehouse = db.query(Warehouse).filter(Warehouse.id == payload.to_warehouse_id).first()
    if not to_warehouse:
        raise HTTPException(status_code=404, detail="To warehouse not found")

    count = db.query(Transfer).count()
    transfer_number = f"TR-{datetime.utcnow().year}-{count + 1:05d}"

    transfer = Transfer(
        transfer_number=transfer_number,
        from_warehouse_id=payload.from_warehouse_id,
        to_warehouse_id=payload.to_warehouse_id,
        notes=payload.notes,
        created_by_id=current_user.id,
        status=TransferStatus.PENDING,
    )
    db.add(transfer)
    db.flush()

    for item in payload.items:
        transfer_item = TransferItem(
            transfer_id=transfer.id,
            material_id=item.material_id,
            quantity=item.quantity,
        )
        db.add(transfer_item)

    db.commit()
    db.refresh(transfer)
    return transfer


@router.put("/{transfer_id}/complete")
def complete_transfer(
    transfer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    transfer = db.query(Transfer).filter(Transfer.id == transfer_id).first()
    if not transfer:
        raise HTTPException(status_code=404, detail="Transfer not found")

    if transfer.status == TransferStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Transfer already completed")

    for item in transfer.items:
        from_stock = (
            db.query(InventoryStock)
            .filter(
                InventoryStock.warehouse_id == transfer.from_warehouse_id,
                InventoryStock.material_id == item.material_id,
            )
            .first()
        )
        if not from_stock or from_stock.quantity < item.quantity:
            raise HTTPException(status_code=400, detail="Insufficient stock for transfer")

        to_stock = (
            db.query(InventoryStock)
            .filter(
                InventoryStock.warehouse_id == transfer.to_warehouse_id,
                InventoryStock.material_id == item.material_id,
            )
            .first()
        )
        if not to_stock:
            to_stock = InventoryStock(
                warehouse_id=transfer.to_warehouse_id,
                material_id=item.material_id,
                quantity=0,
            )
            db.add(to_stock)

        from_stock.quantity -= item.quantity
        to_stock.quantity += item.quantity

        db.add(
            StockTransaction(
                warehouse_id=transfer.from_warehouse_id,
                material_id=item.material_id,
                transaction_type=TransactionType.TRANSFER_OUT,
                quantity=item.quantity,
                reference_id=transfer.id,
            )
        )
        db.add(
            StockTransaction(
                warehouse_id=transfer.to_warehouse_id,
                material_id=item.material_id,
                transaction_type=TransactionType.TRANSFER_IN,
                quantity=item.quantity,
                reference_id=transfer.id,
            )
        )

    transfer.status = TransferStatus.COMPLETED
    transfer.received_at = datetime.utcnow()

    db.commit()
    return {"message": "Transfer completed successfully"}
