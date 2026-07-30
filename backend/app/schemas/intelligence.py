"""
Pydantic schemas for the Movie Intelligence Layer.
Used for request/response validation and serialization.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# --- Enums (mirroring DB) ---

class StoryStructureEnum(str, Enum):
    THREE_ACT = "three_act"
    HERO_JOURNEY = "hero_journey"
    FREYTAG_PYRAMID = "freytag_pyramid"
    SAVE_THE_CAT = "save_the_cat"

class ShotTypeEnum(str, Enum):
    EXTREME_LONG = "extreme_long"
    LONG = "long"
    MEDIUM_LONG = "medium_long"
    MEDIUM = "medium"
    MEDIUM_CLOSE = "medium_close"
    CLOSE_UP = "close_up"
    EXTREME_CLOSE_UP = "extreme_close_up"
    OVER_SHOULDER = "over_shoulder"
    POV = "pov"

class CameraMovementEnum(str, Enum):
    STATIC = "static"
    PAN = "pan"
    TILT = "tilt"
    DOLLY_IN = "dolly_in"
    DOLLY_OUT = "dolly_out"
    TRACKING = "tracking"
    CRANE = "crane"
    HANDHELD = "handheld"

class LightingStyleEnum(str, Enum):
    NATURAL = "natural"
    HIGH_KEY = "high_key"
    LOW_KEY = "low_key"
    CHIAROSCURO = "chiaroscuro"
    NEON_NOIR = "neon_noir"
    GOLDEN_HOUR = "golden_hour"
    BLUE_HOUR = "blue_hour"

class AssetTypeEnum(str, Enum):
    CHARACTER = "character"
    PROP = "prop"
    VEHICLE = "vehicle"
    BUILDING = "building"
    ENVIRONMENT = "environment"
    EFFECT = "effect"
    SOUND = "sound"
    MUSIC = "music"


# --- Base Schemas ---

class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# --- Story Schemas ---

class StoryBase(BaseSchema):
    title: str
    logline: Optional[str] = None
    synopsis: Optional[str] = None
    genre: Optional[str] = None
    mood: Optional[str] = None
    tone: Optional[str] = None
    target_audience: Optional[str] = None
    language: str = "en"
    structure_type: StoryStructureEnum = StoryStructureEnum.THREE_ACT
    theme: Optional[str] = None
    moral_premise: Optional[str] = None
    estimated_duration_minutes: float = 5.0

class StoryCreate(StoryBase):
    project_id: int

class StoryUpdate(BaseSchema):
    title: Optional[str] = None
    logline: Optional[str] = None
    synopsis: Optional[str] = None
    genre: Optional[str] = None
    mood: Optional[str] = None
    status: Optional[str] = None

class StoryResponse(StoryBase):
    id: int
    project_id: int
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# --- Act Schemas ---

class ActBase(BaseSchema):
    order: int
    title: Optional[str] = None
    description: Optional[str] = None
    start_time_min: Optional[float] = None
    end_time_min: Optional[float] = None

class ActCreate(ActBase):
    story_id: int

class ActResponse(ActBase):
    id: int
    story_id: int
    
    class Config:
        from_attributes = True


# --- Character Schemas ---

class CharacterBase(BaseSchema):
    name: str
    role: Optional[str] = None
    archetype: Optional[str] = None
    personality_traits: List[str] = []
    goals: Optional[str] = None
    motivations: Optional[str] = None
    backstory: Optional[str] = None
    appearance_description: Optional[str] = None
    outfit_description: Optional[str] = None
    voice_description: Optional[str] = None
    consistency_rules: List[str] = []

class CharacterCreate(CharacterBase):
    story_id: Optional[int] = None
    project_id: int

class CharacterResponse(CharacterBase):
    id: int
    story_id: Optional[int]
    project_id: int
    memory_embedding_ref: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# --- Environment Schemas ---

class EnvironmentBase(BaseSchema):
    name: str
    description: Optional[str] = None
    mood: Optional[str] = None
    time_of_day: Optional[str] = None
    weather_conditions: Optional[str] = None
    visual_prompt: Optional[str] = None
    lighting_style: LightingStyleEnum = LightingStyleEnum.NATURAL
    associated_assets: List[str] = []

class EnvironmentCreate(EnvironmentBase):
    story_id: int

class EnvironmentResponse(EnvironmentBase):
    id: int
    story_id: int
    
    class Config:
        from_attributes = True


# --- Camera Plan Schemas ---

class CameraPlanBase(BaseSchema):
    shot_type: ShotTypeEnum = ShotTypeEnum.MEDIUM
    movement: CameraMovementEnum = CameraMovementEnum.STATIC
    lens_mm: float = 35.0
    aperture: str = "f/2.8"
    fps: int = 24
    aspect_ratio: str = "16:9"
    direction_notes: Optional[str] = None
    focus_point: Optional[str] = None

class CameraPlanCreate(CameraPlanBase):
    scene_id: int

class CameraPlanResponse(CameraPlanBase):
    id: int
    scene_id: int
    
    class Config:
        from_attributes = True


# --- Dialogue Schemas ---

class DialogueLineBase(BaseSchema):
    order: int
    text: Optional[str] = None
    emotion: Optional[str] = None
    pause_before: float = 0.0
    pause_after: float = 0.0
    voice_id_ref: Optional[str] = None
    tts_prompt_modifiers: Dict[str, Any] = {}

class DialogueLineCreate(DialogueLineBase):
    scene_id: int
    character_id: Optional[int] = None

class DialogueLineResponse(DialogueLineBase):
    id: int
    scene_id: int
    character_id: Optional[int]
    
    class Config:
        from_attributes = True


# --- Asset Schemas ---

class AssetRegistryBase(BaseSchema):
    name: str
    type: AssetTypeEnum
    description: Optional[str] = None
    generation_prompt: Optional[str] = None
    negative_prompt: Optional[str] = None

class AssetRegistryCreate(AssetRegistryBase):
    project_id: int

class AssetRegistryResponse(AssetRegistryBase):
    id: int
    project_id: int
    reference_image_path: Optional[str] = None
    model_3d_path: Optional[str] = None
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# --- Scene Schemas ---

class SceneCharacterLink(BaseSchema):
    character_id: int
    role_in_scene: Optional[str] = None
    emotional_state: Optional[str] = None
    specific_costume_note: Optional[str] = None

class SceneAssetLink(BaseSchema):
    asset_id: int
    usage_note: Optional[str] = None

class SceneBase(BaseSchema):
    order: int
    scene_number: Optional[str] = None
    title: Optional[str] = None
    slugline: Optional[str] = None
    action_description: Optional[str] = None
    purpose: Optional[str] = None
    estimated_duration_sec: float = 10.0
    status: str = "planned"
    dependencies: List[int] = []
    image_prompt: Optional[str] = None
    video_prompt: Optional[str] = None
    negative_prompt: Optional[str] = None
    audio_prompt: Optional[str] = None

class SceneCreate(SceneBase):
    act_id: int
    environment_id: Optional[int] = None
    characters: List[SceneCharacterLink] = []
    assets: List[SceneAssetLink] = []
    camera_plan: Optional[CameraPlanCreate] = None
    dialogues: List[DialogueLineCreate] = []

class SceneUpdate(BaseSchema):
    title: Optional[str] = None
    action_description: Optional[str] = None
    status: Optional[str] = None
    image_prompt: Optional[str] = None
    video_prompt: Optional[str] = None

class SceneResponse(SceneBase):
    id: int
    act_id: int
    environment_id: Optional[int]
    created_at: datetime
    
    # Nested responses
    environment: Optional[EnvironmentResponse] = None
    camera_plan: Optional[CameraPlanResponse] = None
    characters: List[SceneCharacterLink] = []
    dialogues: List[DialogueLineResponse] = []
    assets: List[SceneAssetLink] = []
    
    class Config:
        from_attributes = True


# --- Production Memory Schema ---

class ProductionMemoryBase(BaseSchema):
    entity_type: str
    entity_id: Optional[int] = None
    key: str
    value: str
    confidence_score: float = 1.0
    source: Optional[str] = None

class ProductionMemoryCreate(ProductionMemoryBase):
    project_id: int

class ProductionMemoryResponse(ProductionMemoryBase):
    id: int
    project_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# --- Blueprint & Planning Response Schemas ---

class ProductionBlueprintResponse(BaseSchema):
    """Complete production blueprint for a movie"""
    story: StoryResponse
    acts: List[ActResponse]
    scenes: List[SceneResponse]
    characters: List[CharacterResponse]
    environments: List[EnvironmentResponse]
    assets: List[AssetRegistryResponse]
    total_estimated_duration_min: float
    scene_count: int
    validation_warnings: List[str] = []
