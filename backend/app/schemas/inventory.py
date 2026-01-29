from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.inventory import TransactionType


class InventoryStockResponse(BaseModel):
    id: int
    warehouse_id: int
    material_id: int
    material_name: str
    material_sku: str
    quantity: int
    warehouse_name: str
    last_updated: datetime

    class Config:
        from_attributes = True


class StockTransactionCreate(BaseModel):
    warehouse_id: int
    material_id: int
    transaction_type: TransactionType
    quantity: int
    unit_cost: Optional[float] = None
    notes: Optional[str] = None
