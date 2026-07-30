from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database.models import AIModel, get_db
from app.database.schemas import AIModelCreate, AIModelResponse
from datetime import datetime

router = APIRouter(prefix="/models", tags=["AI Models"])


@router.post("/", response_model=AIModelResponse, status_code=status.HTTP_201_CREATED)
def create_ai_model(model_data: AIModelCreate, db: Session = Depends(get_db)):
    """Register a new AI model (admin only)."""
    new_model = AIModel(
        **model_data.model_dump()
    )
    
    db.add(new_model)
    db.commit()
    db.refresh(new_model)
    
    return new_model


@router.get("/", response_model=List[AIModelResponse])
def get_ai_models(category: str = None, db: Session = Depends(get_db)):
    """Get all registered AI models."""
    query = db.query(AIModel)
    
    if category:
        query = query.filter(AIModel.category == category)
    
    models = query.all()
    return models


@router.get("/{model_id}", response_model=AIModelResponse)
def get_ai_model(model_id: int, db: Session = Depends(get_db)):
    """Get a specific AI model by ID."""
    model = db.query(AIModel).filter(AIModel.id == model_id).first()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI model not found"
        )
    
    return model


@router.put("/{model_id}", response_model=AIModelResponse)
def update_ai_model(
    model_id: int,
    model_data: AIModelCreate,
    db: Session = Depends(get_db)
):
    """Update an AI model (admin only)."""
    model = db.query(AIModel).filter(AIModel.id == model_id).first()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI model not found"
        )
    
    update_data = model_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(model, field, value)
    
    model.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(model)
    
    return model


@router.post("/{model_id}/install", response_model=AIModelResponse)
def install_ai_model(model_id: int, db: Session = Depends(get_db)):
    """Install an AI model (placeholder)."""
    model = db.query(AIModel).filter(AIModel.id == model_id).first()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI model not found"
        )
    
    # Placeholder: In production, this would trigger the installation process
    model.installation_status = "installing"
    model.status = "installing"
    model.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(model)
    
    return model


@router.delete("/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ai_model(model_id: int, db: Session = Depends(get_db)):
    """Delete an AI model (admin only)."""
    model = db.query(AIModel).filter(AIModel.id == model_id).first()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI model not found"
        )
    
    db.delete(model)
    db.commit()
    
    return None


@router.get("/categories")
def get_model_categories(db: Session = Depends(get_db)):
    """Get all available model categories."""
    categories = db.query(AIModel.category).distinct().all()
    return {"categories": [c[0] for c in categories if c[0]]}
