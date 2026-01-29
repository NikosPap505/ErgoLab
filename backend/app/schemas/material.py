from typing import Optional

from pydantic import BaseModel, Field

from app.models.material import MaterialUnit


class MaterialBase(BaseModel):
    sku: str = Field(..., max_length=50)
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    category: Optional[str] = None
    unit: MaterialUnit = MaterialUnit.PIECE
    unit_price: Optional[float] = None
    min_stock_level: int = 0
    barcode: Optional[str] = None
    supplier: Optional[str] = None


class MaterialCreate(MaterialBase):
    pass


class MaterialUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    unit: Optional[MaterialUnit] = None
    unit_price: Optional[float] = None
    min_stock_level: Optional[int] = None
    barcode: Optional[str] = None
    supplier: Optional[str] = None


class MaterialResponse(MaterialBase):
    id: int

    class Config:
        from_attributes = True
