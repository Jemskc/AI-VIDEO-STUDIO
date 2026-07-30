from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database.models import Storyboard, get_db
from app.database.schemas import StoryboardCreate, StoryboardUpdate, StoryboardResponse
from datetime import datetime

router = APIRouter(prefix="/storyboards", tags=["Storyboards"])


@router.post("/", response_model=StoryboardResponse, status_code=status.HTTP_201_CREATED)
def create_storyboard(storyboard_data: StoryboardCreate, db: Session = Depends(get_db), user_id: int = 1):
    """Create a new storyboard."""
    # Get project_id from first scene if not provided
    project_id = 1  # Placeholder
    
    new_storyboard = Storyboard(
        project_id=project_id,
        **storyboard_data.model_dump()
    )
    
    db.add(new_storyboard)
    db.commit()
    db.refresh(new_storyboard)
    
    return new_storyboard


@router.get("/", response_model=List[StoryboardResponse])
def get_storyboards(project_id: int = None, db: Session = Depends(get_db), user_id: int = 1):
    """Get all storyboards, optionally filtered by project."""
    query = db.query(Storyboard)
    
    if project_id:
        query = query.filter(Storyboard.project_id == project_id)
    
    storyboards = query.all()
    return storyboards


@router.get("/{storyboard_id}", response_model=StoryboardResponse)
def get_storyboard(storyboard_id: int, db: Session = Depends(get_db)):
    """Get a specific storyboard by ID."""
    storyboard = db.query(Storyboard).filter(Storyboard.id == storyboard_id).first()
    
    if not storyboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Storyboard not found"
        )
    
    return storyboard


@router.put("/{storyboard_id}", response_model=StoryboardResponse)
def update_storyboard(
    storyboard_id: int,
    storyboard_data: StoryboardUpdate,
    db: Session = Depends(get_db)
):
    """Update a storyboard."""
    storyboard = db.query(Storyboard).filter(Storyboard.id == storyboard_id).first()
    
    if not storyboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Storyboard not found"
        )
    
    update_data = storyboard_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(storyboard, field, value)
    
    storyboard.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(storyboard)
    
    return storyboard


@router.delete("/{storyboard_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_storyboard(storyboard_id: int, db: Session = Depends(get_db)):
    """Delete a storyboard."""
    storyboard = db.query(Storyboard).filter(Storyboard.id == storyboard_id).first()
    
    if not storyboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Storyboard not found"
        )
    
    db.delete(storyboard)
    db.commit()
    
    return None


@router.post("/{storyboard_id}/reorder")
def reorder_storyboard_scenes(
    storyboard_id: int,
    scenes_order: List[int],
    db: Session = Depends(get_db)
):
    """Reorder scenes in a storyboard."""
    storyboard = db.query(Storyboard).filter(Storyboard.id == storyboard_id).first()
    
    if not storyboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Storyboard not found"
        )
    
    storyboard.scenes_order = scenes_order
    storyboard.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(storyboard)
    
    return storyboard
