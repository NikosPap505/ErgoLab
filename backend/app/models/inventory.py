import enum
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, Numeric, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base


class InventoryStock(Base):
    __tablename__ = "inventory_stocks"

    id = Column(Integer, primary_key=True, index=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    quantity = Column(Integer, default=0, nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    warehouse = relationship("Warehouse", back_populates="inventory_stocks")
    material = relationship("Material", back_populates="inventory_stocks")

    __table_args__ = (
        UniqueConstraint("warehouse_id", "material_id", name="unique_warehouse_material"),
    )


class TransactionType(str, enum.Enum):
    PURCHASE = "purchase"
    TRANSFER_OUT = "transfer_out"
    TRANSFER_IN = "transfer_in"
    CONSUMPTION = "consumption"
    RETURN = "return"
    ADJUSTMENT = "adjustment"


class StockTransaction(Base):
    __tablename__ = "stock_transactions"

    id = Column(Integer, primary_key=True, index=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    transaction_type = Column(Enum(TransactionType), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_cost = Column(Numeric(10, 2))
    total_cost = Column(Numeric(12, 2))
    reference_id = Column(Integer)
    notes = Column(Text)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    material = relationship("Material", back_populates="stock_transactions")
    user = relationship("User", back_populates="stock_transactions")
