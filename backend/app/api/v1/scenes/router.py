from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database.models import Scene, get_db
from app.database.schemas import SceneCreate, SceneUpdate, SceneResponse
from datetime import datetime

router = APIRouter(prefix="/scenes", tags=["Scenes"])


@router.post("/", response_model=SceneResponse, status_code=status.HTTP_201_CREATED)
def create_scene(scene_data: SceneCreate, db: Session = Depends(get_db), user_id: int = 1):
    """Create a new scene."""
    new_scene = Scene(
        project_id=scene_data.project_id if hasattr(scene_data, 'project_id') else 1,
        **scene_data.model_dump()
    )
    
    db.add(new_scene)
    db.commit()
    db.refresh(new_scene)
    
    return new_scene


@router.get("/", response_model=List[SceneResponse])
def get_scenes(
    project_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    user_id: int = 1
):
    """Get all scenes, optionally filtered by project."""
    query = db.query(Scene)
    
    if project_id:
        query = query.filter(Scene.project_id == project_id)
    
    scenes = query.order_by(Scene.order_index).offset(skip).limit(limit).all()
    return scenes


@router.get("/{scene_id}", response_model=SceneResponse)
def get_scene(scene_id: int, db: Session = Depends(get_db), user_id: int = 1):
    """Get a specific scene by ID."""
    scene = db.query(Scene).filter(Scene.id == scene_id).first()
    
    if not scene:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scene not found"
        )
    
    return scene


@router.put("/{scene_id}", response_model=SceneResponse)
def update_scene(
    scene_id: int,
    scene_data: SceneUpdate,
    db: Session = Depends(get_db),
    user_id: int = 1
):
    """Update a scene."""
    scene = db.query(Scene).filter(Scene.id == scene_id).first()
    
    if not scene:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scene not found"
        )
    
    update_data = scene_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(scene, field, value)
    
    scene.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(scene)
    
    return scene


@router.delete("/{scene_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scene(scene_id: int, db: Session = Depends(get_db), user_id: int = 1):
    """Delete a scene."""
    scene = db.query(Scene).filter(Scene.id == scene_id).first()
    
    if not scene:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scene not found"
        )
    
    db.delete(scene)
    db.commit()
    
    return None


@router.post("/reorder", response_model=List[SceneResponse])
def reorder_scenes(scene_order: List[int], db: Session = Depends(get_db)):
    """Reorder scenes based on provided order."""
    scenes = []
    for index, scene_id in enumerate(scene_order):
        scene = db.query(Scene).filter(Scene.id == scene_id).first()
        if scene:
            scene.order_index = index
            scene.updated_at = datetime.utcnow()
            db.add(scene)
            scenes.append(scene)
    
    db.commit()
    
    # Refresh all scenes
    refreshed_scenes = [db.query(Scene).get(s.id) for s in scenes]
    return refreshed_scenes
