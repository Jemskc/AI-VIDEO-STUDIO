"""
Database models for the Movie Intelligence Layer.
Includes Story, Acts, Scenes, Characters, Environments, Camera Plans, Dialogue, and Assets.
"""
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, ForeignKey, 
    Enum, JSON, DateTime, UniqueConstraint, func
)
from sqlalchemy.orm import relationship
import enum

# Import Base from database session - using the existing models.py structure
from app.database.models import Base


# --- Enums ---

class StoryStructure(enum.Enum):
    THREE_ACT = "three_act"
    HERO_JOURNEY = "hero_journey"
    FREYTAG_PYRAMID = "freytag_pyramid"
    SAVE_THE_CAT = "save_the_cat"

class ShotType(enum.Enum):
    EXTREME_LONG = "extreme_long"
    LONG = "long"
    MEDIUM_LONG = "medium_long"
    MEDIUM = "medium"
    MEDIUM_CLOSE = "medium_close"
    CLOSE_UP = "close_up"
    EXTREME_CLOSE_UP = "extreme_close_up"
    OVER_SHOULDER = "over_shoulder"
    POV = "pov"

class CameraMovement(enum.Enum):
    STATIC = "static"
    PAN = "pan"
    TILT = "tilt"
    DOLLY_IN = "dolly_in"
    DOLLY_OUT = "dolly_out"
    TRACKING = "tracking"
    CRANE = "crane"
    HANDHELD = "handheld"

class LightingStyle(enum.Enum):
    NATURAL = "natural"
    HIGH_KEY = "high_key"
    LOW_KEY = "low_key"
    CHIAROSCURO = "chiaroscuro"
    NEON_NOIR = "neon_noir"
    GOLDEN_HOUR = "golden_hour"
    BLUE_HOUR = "blue_hour"

class AssetType(enum.Enum):
    CHARACTER = "character"
    PROP = "prop"
    VEHICLE = "vehicle"
    BUILDING = "building"
    ENVIRONMENT = "environment"
    EFFECT = "effect"
    SOUND = "sound"
    MUSIC = "music"


# --- Core Intelligence Models ---

class Story(Base):
    __tablename__ = "stories"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, unique=True)

    title = Column(String(255), nullable=False)
    logline = Column(Text, nullable=True)
    synopsis = Column(Text, nullable=True)
    genre = Column(String(100), nullable=True)
    mood = Column(String(100), nullable=True)
    tone = Column(String(100), nullable=True)
    target_audience = Column(String(100), nullable=True)
    language = Column(String(10), default="en")
    
    structure_type = Column(Enum(StoryStructure), default=StoryStructure.THREE_ACT)
    theme = Column(String(255), nullable=True)
    moral_premise = Column(Text, nullable=True)
    
    # Metadata
    estimated_duration_minutes = Column(Float, default=15.0)
    status = Column(String(50), default="draft")  # draft, planned, locked
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    project = relationship("Project", back_populates="story")
    acts = relationship("Act", back_populates="story", cascade="all, delete-orphan", order_by="Act.order")
    characters = relationship("CharacterProfile", back_populates="story", cascade="all, delete-orphan")
    environments = relationship("Environment", back_populates="story", cascade="all, delete-orphan")


class Act(Base):
    __tablename__ = "acts"

    id = Column(Integer, primary_key=True, index=True)
    story_id = Column(Integer, ForeignKey("stories.id", ondelete="CASCADE"), nullable=False)
    
    order = Column(Integer, nullable=False)  # 1, 2, 3...
    title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    start_time_min = Column(Float, nullable=True)
    end_time_min = Column(Float, nullable=True)
    
    story = relationship("Story", back_populates="acts")
    scenes = relationship("Scene", back_populates="act", cascade="all, delete-orphan", order_by="Scene.order")


class CharacterProfile(Base):
    __tablename__ = "character_profiles"

    id = Column(Integer, primary_key=True, index=True)
    story_id = Column(Integer, ForeignKey("stories.id", ondelete="CASCADE"), nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)

    name = Column(String(255), nullable=False)
    role = Column(String(100), nullable=True)  # Protagonist, Antagonist, Supporting
    archetype = Column(String(100), nullable=True)
    
    # Detailed Attributes
    personality_traits = Column(JSON, default=[])
    goals = Column(Text, nullable=True)
    motivations = Column(Text, nullable=True)
    backstory = Column(Text, nullable=True)
    
    # Visuals (Placeholders for AI)
    appearance_description = Column(Text, nullable=True)
    outfit_description = Column(Text, nullable=True)
    voice_description = Column(Text, nullable=True)
    
    # Consistency Memory
    memory_embedding_ref = Column(String(255), nullable=True)
    consistency_rules = Column(JSON, default=[])
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    story = relationship("Story", back_populates="characters")
    scene_appearances = relationship("SceneCharacter", back_populates="character")


class Environment(Base):
    __tablename__ = "environments"

    id = Column(Integer, primary_key=True, index=True)
    story_id = Column(Integer, ForeignKey("stories.id", ondelete="CASCADE"), nullable=False)

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    mood = Column(String(100), nullable=True)
    time_of_day = Column(String(50), nullable=True)
    weather_conditions = Column(String(100), nullable=True)
    
    # Visual Prompts
    visual_prompt = Column(Text, nullable=True)
    lighting_style = Column(Enum(LightingStyle), default=LightingStyle.NATURAL)
    
    associated_assets = Column(JSON, default=[]) 

    story = relationship("Story", back_populates="environments")
    scenes = relationship("Scene", back_populates="environment")


class Scene(Base):
    __tablename__ = "scenes"

    id = Column(Integer, primary_key=True, index=True)
    act_id = Column(Integer, ForeignKey("acts.id", ondelete="CASCADE"), nullable=False)
    environment_id = Column(Integer, ForeignKey("environments.id", ondelete="SET NULL"), nullable=True)

    order = Column(Integer, nullable=False)
    scene_number = Column(String(20), nullable=True)
    title = Column(String(255), nullable=True)
    
    # Content
    slugline = Column(String(255), nullable=True)
    action_description = Column(Text, nullable=True)
    purpose = Column(Text, nullable=True)
    
    # Timing
    estimated_duration_sec = Column(Float, default=10.0)
    
    # Status
    status = Column(String(50), default="planned")
    
    # Dependencies
    dependencies = Column(JSON, default=[])
    
    # Generated Prompts (Ready for AI Phase)
    image_prompt = Column(Text, nullable=True)
    video_prompt = Column(Text, nullable=True)
    negative_prompt = Column(Text, nullable=True)
    audio_prompt = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    act = relationship("Act", back_populates="scenes")
    environment = relationship("Environment", back_populates="scenes")
    characters = relationship("SceneCharacter", back_populates="scene", cascade="all, delete-orphan")
    camera_plan = relationship("CameraPlan", back_populates="scene", uselist=False, cascade="all, delete-orphan")
    dialogues = relationship("DialogueLine", back_populates="scene", cascade="all, delete-orphan", order_by="DialogueLine.order")
    assets_required = relationship("SceneAsset", back_populates="scene", cascade="all, delete-orphan")


class SceneCharacter(Base):
    """Link table for Characters in Scenes with specific context"""
    __tablename__ = "scene_characters"

    id = Column(Integer, primary_key=True, index=True)
    scene_id = Column(Integer, ForeignKey("scenes.id", ondelete="CASCADE"), nullable=False)
    character_id = Column(Integer, ForeignKey("character_profiles.id", ondelete="CASCADE"), nullable=False)
    
    role_in_scene = Column(String(100), nullable=True)
    emotional_state = Column(String(100), nullable=True)
    specific_costume_note = Column(Text, nullable=True)
    
    scene = relationship("Scene", back_populates="characters")
    character = relationship("CharacterProfile", back_populates="scene_appearances")
    
    __table_args__ = (UniqueConstraint('scene_id', 'character_id', name='uq_scene_character'),)


class CameraPlan(Base):
    __tablename__ = "camera_plans"

    id = Column(Integer, primary_key=True, index=True)
    scene_id = Column(Integer, ForeignKey("scenes.id", ondelete="CASCADE"), nullable=False)

    shot_type = Column(Enum(ShotType), default=ShotType.MEDIUM)
    movement = Column(Enum(CameraMovement), default=CameraMovement.STATIC)
    lens_mm = Column(Float, default=35.0)
    aperture = Column(String(10), default="f/2.8")
    fps = Column(Integer, default=24)
    aspect_ratio = Column(String(10), default="16:9")
    
    direction_notes = Column(Text, nullable=True)
    focus_point = Column(String(100), nullable=True)
    
    scene = relationship("Scene", back_populates="camera_plan")


class DialogueLine(Base):
    __tablename__ = "dialogue_lines"

    id = Column(Integer, primary_key=True, index=True)
    scene_id = Column(Integer, ForeignKey("scenes.id", ondelete="CASCADE"), nullable=False)
    character_id = Column(Integer, ForeignKey("character_profiles.id", ondelete="SET NULL"), nullable=True)

    order = Column(Integer, nullable=False)
    text = Column(Text, nullable=True)
    emotion = Column(String(100), nullable=True)
    pause_before = Column(Float, default=0.0)
    pause_after = Column(Float, default=0.0)
    
    voice_id_ref = Column(String(255), nullable=True)
    tts_prompt_modifiers = Column(JSON, default={})
    
    scene = relationship("Scene", back_populates="dialogues")
    character = relationship("CharacterProfile")


class AssetRegistry(Base):
    __tablename__ = "asset_registry"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    
    name = Column(String(255), nullable=False)
    type = Column(Enum(AssetType), nullable=False)
    description = Column(Text, nullable=True)
    
    reference_image_path = Column(String(255), nullable=True)
    model_3d_path = Column(String(255), nullable=True)
    
    generation_prompt = Column(Text, nullable=True)
    negative_prompt = Column(Text, nullable=True)
    
    status = Column(String(50), default="pending")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    scenes_used = relationship("SceneAsset", back_populates="asset")


class SceneAsset(Base):
    """Link table for Assets required in a Scene"""
    __tablename__ = "scene_assets"

    id = Column(Integer, primary_key=True, index=True)
    scene_id = Column(Integer, ForeignKey("scenes.id", ondelete="CASCADE"), nullable=False)
    asset_id = Column(Integer, ForeignKey("asset_registry.id", ondelete="CASCADE"), nullable=False)
    
    usage_note = Column(String(255), nullable=True)
    
    scene = relationship("Scene", back_populates="assets_required")
    asset = relationship("AssetRegistry", back_populates="scenes_used")


class ProductionMemory(Base):
    """Persistent memory store for consistency across generations"""
    __tablename__ = "production_memory"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(Integer, nullable=True)
    
    key = Column(String(255), nullable=False)
    value = Column(Text, nullable=False)
    
    confidence_score = Column(Float, default=1.0)
    source = Column(String(100), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
