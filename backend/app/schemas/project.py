from datetime import datetime, date
from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, Field

from app.models.project import ProjectStatus


class ProjectBase(BaseModel):
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    location: Optional[str] = None
    client_name: Optional[str] = None
    status: ProjectStatus = ProjectStatus.PLANNING
    budget: Optional[float] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    client_name: Optional[str] = None
    status: Optional[ProjectStatus] = None
    budget: Optional[float] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class ProjectResponse(ProjectBase):
    id: int

    class Config:
        from_attributes = True


class WorkItemStatus(str, Enum):
    planned = "planned"
    in_progress = "in_progress"
    completed = "completed"
    delayed = "delayed"
    blocked = "blocked"


class WorkItemBase(BaseModel):
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    planned_start: date
    planned_end: date
    status: WorkItemStatus = WorkItemStatus.planned
    progress_percentage: float = Field(default=0.0, ge=0, le=100)
    assigned_to: Optional[int] = None
    estimated_hours: Optional[float] = None
    depends_on_id: Optional[int] = None
    budget: Optional[float] = None


class WorkItemCreate(WorkItemBase):
    project_id: int


class WorkItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    planned_start: Optional[date] = None
    planned_end: Optional[date] = None
    actual_start: Optional[date] = None
    actual_end: Optional[date] = None
    status: Optional[WorkItemStatus] = None
    progress_percentage: Optional[float] = None
    assigned_to: Optional[int] = None
    depends_on_id: Optional[int] = None
    actual_hours: Optional[float] = None
    actual_cost: Optional[float] = None


class WorkItemResponse(WorkItemBase):
    id: int
    project_id: int
    actual_start: Optional[date] = None
    actual_end: Optional[date] = None
    actual_hours: Optional[float] = None
    actual_cost: Optional[float] = None
    assigned_user_name: Optional[str] = None
    depends_on_name: Optional[str] = None
    duration_days: int
    is_delayed: bool
    can_start: bool

    class Config:
        from_attributes = True


class TimelineData(BaseModel):
    project_id: int
    project_name: str
    start_date: date
    end_date: date
    work_items: List[WorkItemResponse]
    workers: List[dict]
    critical_path: List[int]
