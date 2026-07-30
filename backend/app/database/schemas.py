from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"


class JobStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    PREPARING = "preparing"
    GENERATING_STORY = "generating_story"
    PREPARING_SCENES = "preparing_scenes"
    WAITING_FOR_AI = "waiting_for_ai"
    FINALIZING = "finalizing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AssetType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"


# Auth Schemas
class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    role: UserRole
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Project Schemas
class ProjectCreate(BaseModel):
    title: str
    description: Optional[str] = None
    genre: Optional[str] = None


class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    genre: Optional[str] = None
    status: Optional[str] = None
    is_favorite: Optional[bool] = None


class ProjectResponse(BaseModel):
    id: int
    user_id: int
    title: str
    description: Optional[str]
    genre: Optional[str]
    status: str
    is_favorite: bool
    thumbnail_url: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Character Schemas
class CharacterCreate(BaseModel):
    name: str
    description: Optional[str] = None
    appearance: Optional[str] = None
    outfit: Optional[str] = None
    voice_style: Optional[str] = None
    personality: Optional[str] = None
    prompt_template: Optional[str] = None
    notes: Optional[str] = None


class CharacterUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    appearance: Optional[str] = None
    outfit: Optional[str] = None
    voice_style: Optional[str] = None
    personality: Optional[str] = None
    prompt_template: Optional[str] = None
    notes: Optional[str] = None
    reference_image_url: Optional[str] = None
    consistency_status: Optional[str] = None


class CharacterResponse(BaseModel):
    id: int
    user_id: int
    name: str
    description: Optional[str]
    appearance: Optional[str]
    outfit: Optional[str]
    voice_style: Optional[str]
    personality: Optional[str]
    prompt_template: Optional[str]
    notes: Optional[str]
    reference_image_url: Optional[str]
    consistency_status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Scene Schemas
class SceneCreate(BaseModel):
    scene_number: int
    title: str
    prompt: Optional[str] = None
    duration: Optional[int] = None
    environment: Optional[str] = None
    camera_settings: Optional[Dict[str, Any]] = None
    dialogue: Optional[str] = None
    lighting: Optional[str] = None
    weather: Optional[str] = None
    characters: Optional[List[int]] = None


class SceneUpdate(BaseModel):
    scene_number: Optional[int] = None
    title: Optional[str] = None
    prompt: Optional[str] = None
    duration: Optional[int] = None
    environment: Optional[str] = None
    camera_settings: Optional[Dict[str, Any]] = None
    dialogue: Optional[str] = None
    lighting: Optional[str] = None
    weather: Optional[str] = None
    characters: Optional[List[int]] = None
    status: Optional[str] = None
    order_index: Optional[int] = None


class SceneResponse(BaseModel):
    id: int
    project_id: int
    scene_number: int
    title: str
    prompt: Optional[str]
    duration: Optional[int]
    environment: Optional[str]
    camera_settings: Optional[Dict[str, Any]]
    dialogue: Optional[str]
    lighting: Optional[str]
    weather: Optional[str]
    characters: Optional[List[int]]
    status: str
    order_index: int
    thumbnail_url: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Storyboard Schemas
class StoryboardCreate(BaseModel):
    title: str
    description: Optional[str] = None
    scenes_order: Optional[List[int]] = None


class StoryboardUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    scenes_order: Optional[List[int]] = None
    status: Optional[str] = None


class StoryboardResponse(BaseModel):
    id: int
    project_id: int
    title: str
    description: Optional[str]
    scenes_order: Optional[List[int]]
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Asset Schemas
class AssetCreate(BaseModel):
    filename: str
    original_filename: Optional[str] = None
    asset_type: AssetType
    file_path: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    duration: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class AssetResponse(BaseModel):
    id: int
    user_id: int
    filename: str
    original_filename: Optional[str]
    asset_type: AssetType
    file_path: str
    file_size: Optional[int]
    mime_type: Optional[str]
    width: Optional[int]
    height: Optional[int]
    duration: Optional[int]
    thumbnail_url: Optional[str]
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Render Job Schemas
class RenderJobCreate(BaseModel):
    project_id: Optional[int] = None
    movie_id: Optional[int] = None
    job_type: str
    parameters: Optional[Dict[str, Any]] = None
    priority: int = 0


class RenderJobUpdate(BaseModel):
    status: Optional[JobStatus] = None
    progress: Optional[int] = None
    error_message: Optional[str] = None
    output_url: Optional[str] = None


class RenderJobResponse(BaseModel):
    id: int
    user_id: int
    project_id: Optional[int]
    movie_id: Optional[int]
    job_type: str
    status: JobStatus
    progress: int
    priority: int
    parameters: Optional[Dict[str, Any]]
    error_message: Optional[str]
    output_url: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Notification Schemas
class NotificationCreate(BaseModel):
    title: str
    message: str
    type: str = "info"


class NotificationResponse(BaseModel):
    id: int
    user_id: int
    title: str
    message: str
    type: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


# AI Model Schemas
class AIModelCreate(BaseModel):
    name: str
    version: Optional[str] = None
    description: Optional[str] = None
    category: str
    vram_required: Optional[int] = None
    disk_required: Optional[int] = None
    capabilities: Optional[List[str]] = None


class AIModelResponse(BaseModel):
    id: int
    name: str
    version: Optional[str]
    description: Optional[str]
    category: str
    status: str
    vram_required: Optional[int]
    disk_required: Optional[int]
    capabilities: Optional[List[str]]
    installation_status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Settings Schemas
class UserSettingUpdate(BaseModel):
    theme: Optional[str] = None
    language: Optional[str] = None
    notification_preferences: Optional[Dict[str, Any]] = None
    storage_preferences: Optional[Dict[str, Any]] = None
    ai_settings: Optional[Dict[str, Any]] = None
    keyboard_shortcuts: Optional[Dict[str, Any]] = None


class UserSettingResponse(BaseModel):
    id: int
    user_id: int
    theme: str
    language: str
    notification_preferences: Optional[Dict[str, Any]]
    storage_preferences: Optional[Dict[str, Any]]
    ai_settings: Optional[Dict[str, Any]]
    keyboard_shortcuts: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Generic Response
class ResponseModel(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None
