from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class WarehouseBase(BaseModel):
    name: str = Field(..., max_length=255)
    code: str = Field(..., max_length=50)
    location: Optional[str] = None
    is_central: bool = False
    project_id: Optional[int] = None


class WarehouseCreate(WarehouseBase):
    pass


class WarehouseUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    is_central: Optional[bool] = None
    project_id: Optional[int] = None


class WarehouseResponse(WarehouseBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
