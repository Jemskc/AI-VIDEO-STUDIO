from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database.models import Project, get_db
from app.database.schemas import ProjectCreate, ProjectUpdate, ProjectResponse
from datetime import datetime

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(project_data: ProjectCreate, db: Session = Depends(get_db), user_id: int = 1):
    """Create a new project."""
    new_project = Project(
        user_id=user_id,
        title=project_data.title,
        description=project_data.description,
        genre=project_data.genre
    )
    
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    
    return new_project


@router.get("/", response_model=List[ProjectResponse])
def get_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    status_filter: Optional[str] = None,
    favorite_only: bool = False,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    user_id: int = 1
):
    """Get all projects with filtering and pagination."""
    query = db.query(Project).filter(Project.user_id == user_id, Project.deleted_at.is_(None))
    
    if status_filter:
        query = query.filter(Project.status == status_filter)
    
    if favorite_only:
        query = query.filter(Project.is_favorite == True)
    
    if search:
        query = query.filter(
            (Project.title.ilike(f"%{search}%")) |
            (Project.description.ilike(f"%{search}%"))
        )
    
    projects = query.offset(skip).limit(limit).all()
    return projects


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: int, db: Session = Depends(get_db), user_id: int = 1):
    """Get a specific project by ID."""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == user_id,
        Project.deleted_at.is_(None)
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    return project


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    db: Session = Depends(get_db),
    user_id: int = 1
):
    """Update a project."""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == user_id,
        Project.deleted_at.is_(None)
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Update only provided fields
    update_data = project_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)
    
    project.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(project)
    
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: int, db: Session = Depends(get_db), user_id: int = 1):
    """Soft delete a project."""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == user_id,
        Project.deleted_at.is_(None)
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    project.deleted_at = datetime.utcnow()
    project.status = "deleted"
    db.commit()
    
    return None


@router.post("/{project_id}/archive", response_model=ProjectResponse)
def archive_project(project_id: int, db: Session = Depends(get_db), user_id: int = 1):
    """Archive a project."""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == user_id,
        Project.deleted_at.is_(None)
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    project.status = "archived"
    project.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(project)
    
    return project


@router.post("/{project_id}/duplicate", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def duplicate_project(project_id: int, db: Session = Depends(get_db), user_id: int = 1):
    """Duplicate a project."""
    original = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == user_id,
        Project.deleted_at.is_(None)
    ).first()
    
    if not original:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    duplicated = Project(
        user_id=user_id,
        title=f"{original.title} (Copy)",
        description=original.description,
        genre=original.genre,
        thumbnail_url=original.thumbnail_url
    )
    
    db.add(duplicated)
    db.commit()
    db.refresh(duplicated)
    
    return duplicated


@router.post("/{project_id}/favorite", response_model=ProjectResponse)
def toggle_favorite(project_id: int, db: Session = Depends(get_db), user_id: int = 1):
    """Toggle project favorite status."""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == user_id,
        Project.deleted_at.is_(None)
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    project.is_favorite = not project.is_favorite
    project.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(project)
    
    return project
