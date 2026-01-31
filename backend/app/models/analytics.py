"""
Analytics Models for ErgoLab Business Intelligence

Provides cost tracking, budgeting, and material usage trends
for data-driven decision making.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Date, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class CostTracking(Base):
    """Track material costs per project transaction"""
    __tablename__ = "cost_tracking"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_cost = Column(Float, nullable=False)
    total_cost = Column(Float, nullable=False)
    transaction_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    notes = Column(Text)
    
    # Relationships
    project = relationship("Project", back_populates="costs")
    material = relationship("Material", back_populates="cost_entries")


class Budget(Base):
    """Project budget allocation and tracking"""
    __tablename__ = "budgets"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, unique=True)
    total_budget = Column(Float, nullable=False)
    materials_budget = Column(Float, nullable=False)
    labor_budget = Column(Float, nullable=False)
    other_budget = Column(Float, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="budget_allocation")


class MaterialUsageTrend(Base):
    """Aggregated material usage trends for analytics"""
    __tablename__ = "material_usage_trends"
    
    id = Column(Integer, primary_key=True, index=True)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    total_quantity = Column(Integer, nullable=False)
    total_cost = Column(Float, nullable=False)
    avg_daily_usage = Column(Float)
    calculated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    material = relationship("Material")
    project = relationship("Project")


class Alert(Base):
    """System alerts for low stock, budget overruns, etc."""
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    alert_type = Column(String(50), nullable=False)  # low_stock, budget_warning, budget_exceeded
    severity = Column(String(20), nullable=False, default="warning")  # info, warning, critical
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    
    # Reference to related entity
    entity_type = Column(String(50))  # material, project, warehouse
    entity_id = Column(Integer)
    
    is_read = Column(Integer, default=0)  # 0=unread, 1=read
    is_resolved = Column(Integer, default=0)  # 0=active, 1=resolved
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    resolved_at = Column(DateTime)
    resolved_by = Column(Integer, ForeignKey("users.id"))
