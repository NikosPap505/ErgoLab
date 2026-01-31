"""
Analytics Schemas for ErgoLab Business Intelligence

Pydantic models for analytics API requests and responses.
"""
from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional, List


# ==================== COST TRACKING ====================

class CostTrackingCreate(BaseModel):
    project_id: int
    material_id: int
    quantity: int = Field(ge=1)
    unit_cost: float = Field(ge=0)
    notes: Optional[str] = None


class CostTrackingResponse(BaseModel):
    id: int
    project_id: int
    material_id: int
    quantity: int
    unit_cost: float
    total_cost: float
    transaction_date: datetime
    notes: Optional[str]
    
    class Config:
        from_attributes = True


# ==================== BUDGET ====================

class BudgetCreate(BaseModel):
    project_id: int
    total_budget: float = Field(ge=0)
    materials_budget: float = Field(ge=0)
    labor_budget: float = Field(ge=0)
    other_budget: float = Field(ge=0)


class BudgetUpdate(BaseModel):
    total_budget: Optional[float] = Field(None, ge=0)
    materials_budget: Optional[float] = Field(None, ge=0)
    labor_budget: Optional[float] = Field(None, ge=0)
    other_budget: Optional[float] = Field(None, ge=0)


class BudgetResponse(BaseModel):
    id: int
    project_id: int
    total_budget: float
    materials_budget: float
    labor_budget: float
    other_budget: float
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# ==================== ANALYTICS SUMMARIES ====================

class ProjectCostSummary(BaseModel):
    """Cost summary for a single project"""
    project_id: int
    project_name: str
    project_code: str
    status: str
    total_budget: Optional[float]
    total_spent: float
    materials_cost: float
    budget_remaining: Optional[float]
    budget_utilization: Optional[float]  # percentage
    cost_per_day: Optional[float]
    days_active: int


class MaterialConsumptionTrend(BaseModel):
    """Material consumption trend over a period"""
    material_id: int
    material_name: str
    material_sku: str
    unit: str
    period_start: date
    period_end: date
    total_quantity: int
    total_cost: float
    avg_daily_usage: float
    projects: List[str]  # project names where material was used


class ProjectProfitability(BaseModel):
    """Profitability analysis for a project"""
    project_id: int
    project_name: str
    project_code: str
    total_budget: Optional[float]
    total_cost: float
    profit_margin: Optional[float]  # percentage
    roi: Optional[float]  # percentage
    status: str
    days_active: int
    cost_breakdown: dict  # {materials: X, labor: Y, other: Z}


class WarehouseAnalytics(BaseModel):
    """Analytics for a single warehouse"""
    warehouse_id: int
    warehouse_name: str
    warehouse_code: str
    total_items: int
    total_value: float
    low_stock_items: int
    out_of_stock_items: int
    top_materials: List[dict]


# ==================== DASHBOARD ====================

class DashboardStats(BaseModel):
    """Comprehensive dashboard statistics"""
    # Counts
    total_projects: int
    active_projects: int
    completed_projects: int
    total_materials: int
    low_stock_count: int
    out_of_stock_count: int
    total_warehouses: int
    pending_transfers: int
    
    # Budget & Spending
    total_budget: float
    total_spent: float
    budget_remaining: float
    budget_utilization: float  # percentage
    
    # Trends
    top_consuming_materials: List[dict]
    recent_transactions: List[dict]
    spending_by_project: List[dict]
    
    # Alerts
    active_alerts: int
    critical_alerts: int


class TrendDataPoint(BaseModel):
    """Single data point for time-series charts"""
    date: date
    value: float
    label: Optional[str] = None


class SpendingTrend(BaseModel):
    """Spending trend over time"""
    period: str  # "daily", "weekly", "monthly"
    data_points: List[TrendDataPoint]
    total: float
    average: float


# ==================== ALERTS ====================

class AlertCreate(BaseModel):
    alert_type: str
    severity: str = "warning"
    title: str
    message: str
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None


class AlertResponse(BaseModel):
    id: int
    alert_type: str
    severity: str
    title: str
    message: str
    entity_type: Optional[str]
    entity_id: Optional[int]
    is_read: bool
    is_resolved: bool
    created_at: datetime
    resolved_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class AlertStats(BaseModel):
    total: int
    unread: int
    critical: int
    warnings: int
    info: int


# ==================== REPORTS ====================

class ReportRequest(BaseModel):
    """Request for generating a report"""
    report_type: str  # "project_costs", "material_usage", "inventory_value"
    format: str = "json"  # "json", "csv", "pdf", "excel"
    project_id: Optional[int] = None
    warehouse_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class ReportMetadata(BaseModel):
    """Metadata for a generated report"""
    report_type: str
    generated_at: datetime
    parameters: dict
    row_count: int
    format: str
