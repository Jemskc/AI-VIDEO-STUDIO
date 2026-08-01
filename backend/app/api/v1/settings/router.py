from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.models import UserSetting, get_db
from app.database.schemas import UserSettingUpdate, UserSettingResponse
from app.auth.dependencies import get_current_user_id
from datetime import datetime

router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get("/", response_model=UserSettingResponse)
def get_user_settings(db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    """Get current user's settings."""
    settings = db.query(UserSetting).filter(UserSetting.user_id == user_id).first()
    
    if not settings:
        # Create default settings if they don't exist
        settings = UserSetting(user_id=user_id)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    
    return settings


@router.put("/", response_model=UserSettingResponse)
def update_user_settings(
    settings_data: UserSettingUpdate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """Update user settings."""
    settings = db.query(UserSetting).filter(UserSetting.user_id == user_id).first()
    
    if not settings:
        # Create new settings if they don't exist
        settings = UserSetting(user_id=user_id)
        db.add(settings)
    
    update_data = settings_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(settings, field, value)
    
    settings.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(settings)
    
    return settings


@router.get("/keyboard-shortcuts")
def get_keyboard_shortcuts(db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    """Get keyboard shortcuts configuration."""
    settings = db.query(UserSetting).filter(UserSetting.user_id == user_id).first()
    
    if not settings:
        return {"shortcuts": {}}
    
    return {"shortcuts": settings.keyboard_shortcuts or {}}


@router.put("/keyboard-shortcuts")
def update_keyboard_shortcuts(shortcuts: dict, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    """Update keyboard shortcuts configuration."""
    settings = db.query(UserSetting).filter(UserSetting.user_id == user_id).first()
    
    if not settings:
        settings = UserSetting(user_id=user_id)
        db.add(settings)
    
    settings.keyboard_shortcuts = shortcuts
    settings.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(settings)
    
    return {"shortcuts": shortcuts}
