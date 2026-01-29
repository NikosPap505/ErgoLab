from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.models.transfer import TransferStatus


class TransferItemCreate(BaseModel):
    material_id: int
    quantity: int


class TransferCreate(BaseModel):
    from_warehouse_id: int
    to_warehouse_id: int
    items: List[TransferItemCreate]
    notes: Optional[str] = None


class TransferResponse(BaseModel):
    id: int
    transfer_number: str
    from_warehouse_id: int
    to_warehouse_id: int
    status: TransferStatus
    notes: Optional[str] = None
    created_by_id: int
    created_at: datetime
    shipped_at: Optional[datetime] = None
    received_at: Optional[datetime] = None

    class Config:
        from_attributes = True
