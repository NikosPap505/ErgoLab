from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional, List
from enum import Enum

# Enums
class WeatherConditionEnum(str, Enum):
    sunny = "sunny"
    cloudy = "cloudy"
    rainy = "rainy"
    stormy = "stormy"
    windy = "windy"
    snow = "snow"
    fog = "fog"

class IssueSeverityEnum(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"

class IssueStatusEnum(str, Enum):
    open = "open"
    in_progress = "in_progress"
    resolved = "resolved"
    closed = "closed"

class IssueCategoryEnum(str, Enum):
    delay = "delay"
    quality = "quality"
    safety = "safety"
    material = "material"
    equipment = "equipment"
    weather = "weather"
    labor = "labor"
    other = "other"

# ========== DAILY REPORTS ==========

class DailyReportCreate(BaseModel):
    project_id: int
    report_date: date
    
    weather_condition: Optional[WeatherConditionEnum] = None
    temperature: Optional[float] = None
    weather_notes: Optional[str] = None
    
    workers_count: int = 0
    workers_present: Optional[str] = None
    workers_absent: Optional[str] = None
    
    work_description: str
    work_completed: Optional[str] = None
    work_in_progress: Optional[str] = None
    
    progress_percentage: float = 0.0
    progress_notes: Optional[str] = None
    
    materials_used_summary: Optional[str] = None
    equipment_used: Optional[str] = None
    issues_summary: Optional[str] = None
    
    observations: Optional[str] = None
    safety_notes: Optional[str] = None

class DailyReportResponse(BaseModel):
    id: int
    project_id: int
    project_name: Optional[str] = None
    report_date: date
    
    weather_condition: Optional[str]
    temperature: Optional[float]
    weather_notes: Optional[str]
    
    workers_count: int
    workers_present: Optional[str]
    workers_absent: Optional[str]
    
    work_description: str
    work_completed: Optional[str]
    work_in_progress: Optional[str]
    
    progress_percentage: float
    progress_notes: Optional[str]
    
    materials_used_summary: Optional[str]
    equipment_used: Optional[str]
    issues_summary: Optional[str]
    
    observations: Optional[str]
    safety_notes: Optional[str]
    
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# ========== ISSUES ==========

class IssueCreate(BaseModel):
    project_id: int
    daily_report_id: Optional[int] = None

    title: str
    description: str
    category: IssueCategoryEnum
    severity: IssueSeverityEnum
    status: IssueStatusEnum = IssueStatusEnum.open

    due_date: Optional[date] = None
    assigned_to: Optional[int] = None

class IssueUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[IssueStatusEnum] = None
    severity: Optional[IssueSeverityEnum] = None
    assigned_to: Optional[int] = None
    resolution_notes: Optional[str] = None
    resolution_cost: Optional[float] = None
    resolved_date: Optional[datetime] = None
    delay_days: Optional[int] = None


class IssueMove(BaseModel):
    """Schema for moving issue between columns"""
    status: IssueStatusEnum
    position: int

class IssueResponse(BaseModel):
    id: int
    project_id: int
    project_name: Optional[str] = None
    daily_report_id: Optional[int]

    title: str
    description: str
    category: str
    severity: str
    status: str

    reported_date: datetime
    due_date: Optional[date]
    resolved_date: Optional[datetime]

    resolution_notes: Optional[str]
    resolution_cost: Optional[float]
    delay_days: int

    assigned_to: Optional[int]
    assigned_to_name: Optional[str] = None
    reported_by: int
    reported_by_name: Optional[str] = None

    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# ========== WORK ITEMS ==========

class WorkItemCreate(BaseModel):
    project_id: int
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    
    planned_start_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    assigned_to: Optional[str] = None
    depends_on: Optional[str] = None

class WorkItemUpdate(BaseModel):
    status: Optional[str] = None
    completion_percentage: Optional[float] = None
    actual_start_date: Optional[date] = None
    actual_end_date: Optional[date] = None

class WorkItemResponse(BaseModel):
    id: int
    project_id: int
    name: str
    description: Optional[str]
    category: Optional[str]
    
    planned_start_date: Optional[date]
    planned_end_date: Optional[date]
    actual_start_date: Optional[date]
    actual_end_date: Optional[date]
    
    status: str
    completion_percentage: float
    assigned_to: Optional[str]
    depends_on: Optional[str]
    
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# ========== LABOR LOGS ==========

class LaborLogCreate(BaseModel):
    project_id: int
    daily_report_id: Optional[int] = None
    
    worker_name: str
    worker_role: Optional[str] = None
    work_date: date
    hours_worked: float = 8.0
    overtime_hours: float = 0.0
    
    hourly_rate: Optional[float] = None
    tasks_performed: Optional[str] = None
    notes: Optional[str] = None

class LaborLogResponse(BaseModel):
    id: int
    project_id: int
    daily_report_id: Optional[int]
    
    worker_name: str
    worker_role: Optional[str]
    work_date: date
    hours_worked: float
    overtime_hours: float
    
    hourly_rate: Optional[float]
    total_cost: Optional[float]
    tasks_performed: Optional[str]
    notes: Optional[str]
    
    created_at: datetime
    
    class Config:
        from_attributes = True

# ========== EQUIPMENT LOGS ==========

class EquipmentLogCreate(BaseModel):
    project_id: int
    daily_report_id: Optional[int] = None
    
    equipment_name: str
    equipment_type: Optional[str] = None
    usage_date: date
    hours_used: float = 0.0
    
    rental_cost: Optional[float] = None
    fuel_cost: Optional[float] = None
    maintenance_cost: Optional[float] = None
    
    operator_name: Optional[str] = None
    notes: Optional[str] = None

class EquipmentLogResponse(BaseModel):
    id: int
    project_id: int
    daily_report_id: Optional[int]
    
    equipment_name: str
    equipment_type: Optional[str]
    usage_date: date
    hours_used: float
    
    rental_cost: Optional[float]
    fuel_cost: Optional[float]
    maintenance_cost: Optional[float]
    
    operator_name: Optional[str]
    notes: Optional[str]
    
    created_at: datetime
    
    class Config:
        from_attributes = True

# ========== REPORT SUMMARIES (Ελληνικά) ==========

class WeeklySummary(BaseModel):
    project_id: int
    project_name: str
    week_start: date
    week_end: date
    
    total_workers: int
    total_hours: float
    total_cost: float
    
    work_completed: List[str]
    issues_count: int
    critical_issues: int
    
    materials_used: List[dict]
    progress_change: float  # Μεταβολή προόδου %

class MonthlySummary(BaseModel):
    project_id: int
    project_name: str
    month: int
    year: int
    
    total_days_worked: int
    total_workers: int
    total_labor_hours: float
    total_labor_cost: float
    total_materials_cost: float
    total_equipment_cost: float
    total_cost: float
    
    budget_used_percentage: Optional[float]
    progress_percentage: float
    
    issues_opened: int
    issues_resolved: int
    issues_pending: int
    
    major_milestones: List[str]

class FinalProjectReport(BaseModel):
    project_id: int
    project_name: str
    project_code: str
    
    start_date: Optional[date]
    end_date: Optional[date]
    duration_days: int
    
    total_budget: Optional[float]
    total_cost: float
    budget_variance: Optional[float]
    budget_variance_percentage: Optional[float]
    
    materials_cost: float
    labor_cost: float
    equipment_cost: float
    other_costs: float
    
    total_workers_employed: int
    total_labor_hours: float
    
    total_issues: int
    critical_issues: int
    issues_resolved: int
    
    final_progress: float
    completion_status: str
    
    key_achievements: List[str]
    major_challenges: List[str]
    lessons_learned: List[str]
