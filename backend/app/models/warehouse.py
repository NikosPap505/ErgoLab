from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class Warehouse(Base):
    __tablename__ = "warehouses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, index=True, nullable=False)
    location = Column(String(255))
    is_central = Column(Boolean, default=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project", back_populates="warehouse")
    inventory_stocks = relationship("InventoryStock", back_populates="warehouse")
    transfers_from = relationship(
        "Transfer",
        foreign_keys="Transfer.from_warehouse_id",
        back_populates="from_warehouse",
    )
    transfers_to = relationship(
        "Transfer",
        foreign_keys="Transfer.to_warehouse_id",
        back_populates="to_warehouse",
    )
