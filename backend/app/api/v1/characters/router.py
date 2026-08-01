from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database.models import Character, get_db
from app.database.schemas import CharacterCreate, CharacterUpdate, CharacterResponse
from app.auth.dependencies import get_current_user_id
from datetime import datetime

router = APIRouter(prefix="/characters", tags=["Characters"])


@router.post("/", response_model=CharacterResponse, status_code=status.HTTP_201_CREATED)
def create_character(character_data: CharacterCreate, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    """Create a new character."""
    new_character = Character(
        user_id=user_id,
        **character_data.model_dump()
    )
    
    db.add(new_character)
    db.commit()
    db.refresh(new_character)
    
    return new_character


@router.get("/", response_model=List[CharacterResponse])
def get_characters(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    """Get all characters for the current user."""
    characters = db.query(Character).filter(
        Character.user_id == user_id
    ).offset(skip).limit(limit).all()
    
    return characters


@router.get("/{character_id}", response_model=CharacterResponse)
def get_character(character_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    """Get a specific character by ID."""
    character = db.query(Character).filter(
        Character.id == character_id,
        Character.user_id == user_id
    ).first()
    
    if not character:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found"
        )
    
    return character


@router.put("/{character_id}", response_model=CharacterResponse)
def update_character(
    character_id: int,
    character_data: CharacterUpdate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """Update a character."""
    character = db.query(Character).filter(
        Character.id == character_id,
        Character.user_id == user_id
    ).first()
    
    if not character:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found"
        )
    
    update_data = character_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(character, field, value)
    
    character.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(character)
    
    return character


@router.delete("/{character_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_character(character_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    """Delete a character."""
    character = db.query(Character).filter(
        Character.id == character_id,
        Character.user_id == user_id
    ).first()
    
    if not character:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found"
        )
    
    db.delete(character)
    db.commit()
    
    return None
