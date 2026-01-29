import enum
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class ReportType(str, enum.Enum):
    CONSUMABLES_BY_PROJECT = "consumables_by_project"
    CONSUMABLES_TOTAL = "consumables_total"
    INVENTORY_STATUS = "inventory_status"
    TRANSFER_HISTORY = "transfer_history"


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    report_type = Column(Enum(ReportType), nullable=False)
    title = Column(String(255), nullable=False)
    period_start = Column(DateTime)
    period_end = Column(DateTime)
    total_cost = Column(Numeric(12, 2))
    report_data = Column(Text)
    generated_by_id = Column(Integer, ForeignKey("users.id"))
    generated_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="reports")
