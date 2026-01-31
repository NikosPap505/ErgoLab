import enum

from sqlalchemy import Column, Enum, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class MaterialUnit(str, enum.Enum):
    PIECE = "piece"
    METER = "meter"
    KILOGRAM = "kilogram"
    LITER = "liter"
    BOX = "box"
    PACKAGE = "package"


class Material(Base):
    __tablename__ = "materials"

    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(100))
    unit = Column(Enum(MaterialUnit), default=MaterialUnit.PIECE)
    unit_price = Column(Numeric(10, 2))
    min_stock_level = Column(Integer, default=0)
    barcode = Column(String(100), unique=True, index=True)
    supplier = Column(String(255))

    inventory_stocks = relationship("InventoryStock", back_populates="material")
    stock_transactions = relationship("StockTransaction", back_populates="material")
    cost_entries = relationship("CostTracking", back_populates="material")
