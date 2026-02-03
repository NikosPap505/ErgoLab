from datetime import datetime
from typing import Optional
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from app.models.inventory import TransactionType


class InventoryStockResponse(BaseModel):
    id: int
    warehouse_id: int
    material_id: int
    material_name: str
    material_sku: str
    quantity: int
    warehouse_name: str
    last_updated: Optional[datetime]

    class Config:
        from_attributes = True


class StockTransactionCreate(BaseModel):
    warehouse_id: int = Field(..., gt=0)
    material_id: int = Field(..., gt=0)
    transaction_type: TransactionType
    quantity: int = Field(..., gt=0, description="Must be positive")
    unit_cost: Optional[Decimal] = Field(None, ge=0, description="Must be non-negative if provided")
    notes: Optional[str] = Field(None, max_length=1000)

    @field_validator('quantity')
    @classmethod
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError('Quantity must be positive')
        if v > 999999999:
            raise ValueError('Quantity exceeds maximum allowed value')
        return v

    @field_validator('unit_cost')
    @classmethod
    def validate_unit_cost(cls, v):
        if v is not None and v < 0:
            raise ValueError('Unit cost cannot be negative')
        if v is not None and v > 999999999.99:
            raise ValueError('Unit cost exceeds maximum allowed value')
        return v
