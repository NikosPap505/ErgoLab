from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.core.database import get_db
from app.core.cache import cache, CacheKeys
from app.models.project import Project
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate

router = APIRouter(prefix="/api/projects", tags=["Projects"])


@router.get("/", response_model=List[ProjectResponse])
def list_projects(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
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
    current_user: User = Depends(get_current_user),
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
def get_project(project_id: int, db: Session = Depends(get_db)):
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
    current_user: User = Depends(get_current_user),
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
    current_user: User = Depends(get_current_user),
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
