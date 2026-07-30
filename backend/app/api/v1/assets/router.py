from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database.models import Asset, AssetType, get_db
from app.database.schemas import AssetCreate, AssetResponse
from datetime import datetime
import os
import uuid
from app.core.config import settings

router = APIRouter(prefix="/assets", tags=["Assets"])


@router.post("/upload", response_model=AssetResponse, status_code=status.HTTP_201_CREATED)
async def upload_asset(
    file: UploadFile = File(...),
    asset_type: str = Form(...),
    db: Session = Depends(get_db),
    user_id: int = 1
):
    """Upload a new asset."""
    # Validate asset type
    try:
        asset_type_enum = AssetType(asset_type.lower())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid asset type. Must be one of: {[t.value for t in AssetType]}"
        )
    
    # Create storage directory if not exists
    storage_dir = settings.STORAGE_PATH
    os.makedirs(storage_dir, exist_ok=True)
    
    # Generate unique filename
    file_extension = file.filename.split(".")[-1] if "." in file.filename else ""
    unique_filename = f"{uuid.uuid4()}.{file_extension}" if file_extension else uuid.uuid4().hex
    file_path = os.path.join(storage_dir, unique_filename)
    
    # Save file
    try:
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
            
        file_size = len(content)
        
        # Check file size limit
        if file_size > settings.MAX_UPLOAD_SIZE:
            os.remove(file_path)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large. Max size is {settings.MAX_UPLOAD_SIZE} bytes"
            )
        
        # Create asset record
        new_asset = Asset(
            user_id=user_id,
            filename=unique_filename,
            original_filename=file.filename,
            asset_type=asset_type_enum,
            file_path=file_path,
            file_size=file_size,
            mime_type=file.content_type
        )
        
        db.add(new_asset)
        db.commit()
        db.refresh(new_asset)
        
        return new_asset
        
    except Exception as e:
        # Clean up file if something went wrong
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )


@router.get("/", response_model=List[AssetResponse])
def get_assets(
    asset_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    user_id: int = 1
):
    """Get all assets for the current user."""
    query = db.query(Asset).filter(Asset.user_id == user_id)
    
    if asset_type:
        try:
            asset_type_enum = AssetType(asset_type.lower())
            query = query.filter(Asset.asset_type == asset_type_enum)
        except ValueError:
            pass
    
    if search:
        query = query.filter(
            (Asset.original_filename.ilike(f"%{search}%")) |
            (Asset.filename.ilike(f"%{search}%"))
        )
    
    assets = query.order_by(Asset.created_at.desc()).offset(skip).limit(limit).all()
    return assets


@router.get("/{asset_id}", response_model=AssetResponse)
def get_asset(asset_id: int, db: Session = Depends(get_db), user_id: int = 1):
    """Get a specific asset by ID."""
    asset = db.query(Asset).filter(
        Asset.id == asset_id,
        Asset.user_id == user_id
    ).first()
    
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found"
        )
    
    return asset


@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_asset(asset_id: int, db: Session = Depends(get_db), user_id: int = 1):
    """Delete an asset."""
    asset = db.query(Asset).filter(
        Asset.id == asset_id,
        Asset.user_id == user_id
    ).first()
    
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found"
        )
    
    # Delete file from storage
    if os.path.exists(asset.file_path):
        os.remove(asset.file_path)
    
    db.delete(asset)
    db.commit()
    
    return None


@router.get("/{asset_id}/download")
async def download_asset(asset_id: int, db: Session = Depends(get_db), user_id: int = 1):
    """Download an asset file."""
    from fastapi.responses import FileResponse
    
    asset = db.query(Asset).filter(
        Asset.id == asset_id,
        Asset.user_id == user_id
    ).first()
    
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found"
        )
    
    if not os.path.exists(asset.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on disk"
        )
    
    return FileResponse(
        asset.file_path,
        filename=asset.original_filename or asset.filename,
        media_type=asset.mime_type
    )
