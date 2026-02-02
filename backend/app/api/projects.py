from typing import List, Optional

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.core.permissions import Permission, check_permission
from app.core.database import get_db
from app.core.cache import cache, CacheKeys
from app.models.project import Project
from app.models.reports import WorkItem
from app.models.user import User
from app.schemas.project import (
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
    WorkItemCreate,
    WorkItemUpdate,
    WorkItemResponse,
    TimelineData,
    WorkItemStatus,
)

router = APIRouter(prefix="/api/projects", tags=["Projects"])


def _normalize_status(value: str) -> WorkItemStatus:
    if value == "pending":
        return WorkItemStatus.planned
    try:
        return WorkItemStatus(value)
    except ValueError:
        return WorkItemStatus.planned


def _parse_assigned_to(value: Optional[str]) -> Optional[int]:
    if not value:
        return None
    try:
        return int(str(value).split(",")[0])
    except ValueError:
        return None


def _parse_depends_on(value: Optional[str]) -> Optional[int]:
    if not value:
        return None
    try:
        return int(str(value).split(",")[0])
    except ValueError:
        return None


def _work_item_to_response(db: Session, work_item: WorkItem) -> WorkItemResponse:
    assigned_to = _parse_assigned_to(work_item.assigned_to)
    depends_on_id = _parse_depends_on(work_item.depends_on)
    assigned_user = None
    depends_on_name = None

    if assigned_to:
        assigned_user = db.query(User).filter(User.id == assigned_to).first()

    if depends_on_id:
        depends_on = db.query(WorkItem).filter(WorkItem.id == depends_on_id).first()
        depends_on_name = depends_on.name if depends_on else None

    planned_start = work_item.planned_start_date or date.today()
    planned_end = work_item.planned_end_date or planned_start

    duration_days = (planned_end - planned_start).days + 1
    is_delayed = work_item.status != "completed" and date.today() > planned_end
    can_start = True
    if depends_on_id:
        depends_on = db.query(WorkItem).filter(WorkItem.id == depends_on_id).first()
        if depends_on and depends_on.status != "completed":
            can_start = False

    return WorkItemResponse(
        id=work_item.id,
        project_id=work_item.project_id,
        name=work_item.name,
        description=work_item.description,
        planned_start=planned_start,
        planned_end=planned_end,
        actual_start=work_item.actual_start_date,
        actual_end=work_item.actual_end_date,
        status=_normalize_status(work_item.status),
        progress_percentage=work_item.completion_percentage or 0.0,
        assigned_to=assigned_to,
        assigned_user_name=assigned_user.full_name if assigned_user else None,
        estimated_hours=None,
        actual_hours=None,
        depends_on_id=depends_on_id,
        depends_on_name=depends_on_name,
        budget=None,
        actual_cost=None,
        duration_days=duration_days,
        is_delayed=is_delayed,
        can_start=can_start,
    )


@router.get("/", response_model=List[ProjectResponse])
def list_projects(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission(Permission.PROJECT_READ)),
):
    # Try cache first
    cache_key = CacheKeys.projects_list()
    cached_data = cache.get(cache_key)
    if cached_data:
        return cached_data
    
    projects = db.query(Project).offset(skip).limit(limit).all()
    
    # Convert to dict for caching
    result = [
        {
            "id": p.id,
            "name": p.name,
            "code": p.code,
            "description": p.description,
            "status": p.status,
            "start_date": p.start_date.isoformat() if p.start_date is not None else None,  # type: ignore[union-attr]
            "end_date": p.end_date.isoformat() if p.end_date is not None else None,  # type: ignore[union-attr]
            "client_name": p.client_name,
            "location": p.location,
        }
        for p in projects
    ]
    
    # Cache for 10 minutes
    cache.set(cache_key, result, expire=600)
    return projects


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission(Permission.PROJECT_CREATE)),
):
    existing = db.query(Project).filter(Project.code == payload.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Project code already exists")

    project = Project(**payload.dict())
    db.add(project)
    db.commit()
    db.refresh(project)
    
    # Invalidate projects list cache
    cache.clear_pattern("projects:*")
    cache.clear_pattern("dashboard:*")
    
    return project


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission(Permission.PROJECT_READ)),
):
    # Try cache first
    cache_key = CacheKeys.project_detail(project_id)
    cached_data = cache.get(cache_key)
    if cached_data:
        return cached_data
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Cache for 10 minutes
    cache.set(cache_key, {
        "id": project.id,
        "name": project.name,
        "code": project.code,
        "description": project.description,
        "status": project.status,
        "start_date": project.start_date.isoformat() if project.start_date is not None else None,  # type: ignore[union-attr]
        "end_date": project.end_date.isoformat() if project.end_date is not None else None,  # type: ignore[union-attr]
        "client_name": project.client_name,
        "location": project.location,
    }, expire=600)
    
    return project


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    payload: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission(Permission.PROJECT_UPDATE)),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    for key, value in payload.dict(exclude_unset=True).items():
        setattr(project, key, value)

    db.commit()
    db.refresh(project)
    
    # Invalidate cache
    cache.delete(CacheKeys.project_detail(project_id))
    cache.clear_pattern("projects:list*")
    cache.clear_pattern("dashboard:*")
    
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission(Permission.PROJECT_DELETE)),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    db.delete(project)
    db.commit()
    
    # Invalidate cache
    cache.delete(CacheKeys.project_detail(project_id))
    cache.clear_pattern("projects:*")
    cache.clear_pattern("dashboard:*")
    
    return None


@router.post("/{project_id}/work-items", response_model=WorkItemResponse, status_code=status.HTTP_201_CREATED)
def create_work_item(
    project_id: int,
    work_item: WorkItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission(Permission.PROJECT_UPDATE)),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if work_item.planned_end < work_item.planned_start:
        raise HTTPException(status_code=400, detail="End date must be after start date")

    if work_item.depends_on_id:
        dependency = db.query(WorkItem).filter(
            WorkItem.id == work_item.depends_on_id,
            WorkItem.project_id == project_id,
        ).first()
        if not dependency:
            raise HTTPException(status_code=400, detail="Dependency not found in this project")

    db_work_item = WorkItem(
        project_id=project_id,
        name=work_item.name,
        description=work_item.description,
        planned_start_date=work_item.planned_start,
        planned_end_date=work_item.planned_end,
        status=work_item.status.value,
        completion_percentage=work_item.progress_percentage,
        assigned_to=str(work_item.assigned_to) if work_item.assigned_to else None,
        depends_on=str(work_item.depends_on_id) if work_item.depends_on_id else None,
    )
    db.add(db_work_item)
    db.commit()
    db.refresh(db_work_item)

    return _work_item_to_response(db, db_work_item)


@router.get("/{project_id}/work-items", response_model=List[WorkItemResponse])
def list_work_items(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission(Permission.PROJECT_READ)),
):
    work_items = db.query(WorkItem).filter(WorkItem.project_id == project_id).all()
    return [_work_item_to_response(db, item) for item in work_items]


@router.put("/work-items/{item_id}", response_model=WorkItemResponse)
def update_work_item(
    item_id: int,
    work_item_update: WorkItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission(Permission.PROJECT_UPDATE)),
):
    db_work_item = db.query(WorkItem).filter(WorkItem.id == item_id).first()
    if not db_work_item:
        raise HTTPException(status_code=404, detail="Work item not found")

    update_data = work_item_update.dict(exclude_unset=True)

    if "name" in update_data:
        db_work_item.name = update_data["name"]
    if "description" in update_data:
        db_work_item.description = update_data["description"]
    if "planned_start" in update_data:
        db_work_item.planned_start_date = update_data["planned_start"]
    if "planned_end" in update_data:
        db_work_item.planned_end_date = update_data["planned_end"]
    if "actual_start" in update_data:
        db_work_item.actual_start_date = update_data["actual_start"]
    if "actual_end" in update_data:
        db_work_item.actual_end_date = update_data["actual_end"]
    if "assigned_to" in update_data:
        assigned_to = update_data["assigned_to"]
        db_work_item.assigned_to = str(assigned_to) if assigned_to else None
    if "depends_on_id" in update_data:
        depends_on_id = update_data["depends_on_id"]
        db_work_item.depends_on = str(depends_on_id) if depends_on_id else None
    if "status" in update_data:
        status_value = update_data["status"]
        db_work_item.status = status_value.value if hasattr(status_value, "value") else str(status_value)
    if "progress_percentage" in update_data:
        progress = update_data["progress_percentage"]
        db_work_item.completion_percentage = progress
        if progress == 100:
            db_work_item.status = WorkItemStatus.completed.value
            if not db_work_item.actual_end_date:
                db_work_item.actual_end_date = date.today()
        elif progress > 0 and db_work_item.status in ["planned", "pending"]:
            db_work_item.status = WorkItemStatus.in_progress.value
            if not db_work_item.actual_start_date:
                db_work_item.actual_start_date = date.today()

    db.commit()
    db.refresh(db_work_item)

    return _work_item_to_response(db, db_work_item)


@router.delete("/work-items/{item_id}")
def delete_work_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission(Permission.PROJECT_UPDATE)),
):
    db_work_item = db.query(WorkItem).filter(WorkItem.id == item_id).first()
    if not db_work_item:
        raise HTTPException(status_code=404, detail="Work item not found")

    dependents = db.query(WorkItem).filter(WorkItem.depends_on == str(item_id)).count()
    if dependents > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete: {dependents} items depend on this",
        )

    db.delete(db_work_item)
    db.commit()

    return {"message": "Work item deleted"}


@router.get("/{project_id}/timeline", response_model=TimelineData)
def get_project_timeline(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_permission(Permission.PROJECT_READ)),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    work_items = (
        db.query(WorkItem)
        .filter(WorkItem.project_id == project_id)
        .order_by(WorkItem.planned_start_date)
        .all()
    )

    if not work_items:
        raise HTTPException(status_code=404, detail="No work items found for this project")

    planned_starts = [wi.planned_start_date for wi in work_items if wi.planned_start_date]
    planned_ends = [wi.planned_end_date for wi in work_items if wi.planned_end_date]
    if not planned_starts or not planned_ends:
        raise HTTPException(status_code=400, detail="Work items missing planned dates")

    start_date = min(planned_starts)
    end_date = max(planned_ends)

    worker_ids = {
        _parse_assigned_to(wi.assigned_to)
        for wi in work_items
        if _parse_assigned_to(wi.assigned_to)
    }
    workers = []
    for worker_id in worker_ids:
        user = db.query(User).filter(User.id == worker_id).first()
        if user:
            workers.append({"id": user.id, "name": user.full_name})

    critical_path = _calculate_critical_path(work_items)

    return TimelineData(
        project_id=project.id,
        project_name=project.name,
        start_date=start_date,
        end_date=end_date,
        work_items=[_work_item_to_response(db, item) for item in work_items],
        workers=workers,
        critical_path=critical_path,
    )


def _calculate_critical_path(work_items: List[WorkItem]) -> List[int]:
    graph = {}
    for item in work_items:
        deps = []
        if item.depends_on:
            try:
                deps = [int(item.depends_on.split(",")[0])]
            except ValueError:
                deps = []
        planned_start = item.planned_start_date or date.today()
        planned_end = item.planned_end_date or planned_start
        duration = (planned_end - planned_start).days + 1
        graph[item.id] = {
            "duration": duration,
            "dependencies": deps,
        }

    earliest_start = {}
    earliest_finish = {}

    for item_id, node in graph.items():
        if not node["dependencies"]:
            earliest_start[item_id] = 0
        else:
            max_finish = max(earliest_finish.get(dep, 0) for dep in node["dependencies"])
            earliest_start[item_id] = max_finish
        earliest_finish[item_id] = earliest_start[item_id] + node["duration"]

    project_duration = max(earliest_finish.values()) if earliest_finish else 0
    latest_finish = {}
    latest_start = {}

    for item_id in reversed(list(graph.keys())):
        dependents = [i for i, n in graph.items() if item_id in n["dependencies"]]
        if not dependents:
            latest_finish[item_id] = project_duration
        else:
            min_start = min(latest_start.get(dep, project_duration) for dep in dependents)
            latest_finish[item_id] = min_start
        latest_start[item_id] = latest_finish[item_id] - graph[item_id]["duration"]

    return [item_id for item_id in graph if earliest_start[item_id] == latest_start[item_id]]
