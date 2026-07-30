"""
API routes for Movie Intelligence Layer.
Handles story planning, scene management, and production blueprints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database.models import SessionLocal, get_db
from app.models.intelligence import Story, Act, Scene, CharacterProfile, Environment
from app.schemas.intelligence import (
    StoryCreate, StoryResponse, StoryUpdate,
    ActResponse, SceneResponse, SceneCreate, SceneUpdate,
    CharacterResponse, CharacterCreate,
    EnvironmentResponse, EnvironmentCreate,
    ProductionBlueprintResponse
)
from app.services.movie_planning import MoviePlanningService
from app.services.scene_engine import SceneService
from app.services.validation_engine import ValidationService
from app.auth.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/v1/intelligence", tags=["Intelligence"])


# --- Story Endpoints ---

@router.post("/stories", response_model=StoryResponse, status_code=status.HTTP_201_CREATED)
def create_story_from_prompt(
    story_data: StoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new story from a prompt.
    Automatically analyzes the prompt and creates initial structure.
    """
    planner = MoviePlanningService(db)
    
    # Create story with analysis
    story = planner.create_story_from_prompt(
        project_id=story_data.project_id,
        prompt=story_data.synopsis or story_data.logline or "",
        title=story_data.title,
    )
    
    return story


@router.get("/stories/{story_id}", response_model=StoryResponse)
def get_story(story_id: int, db: Session = Depends(get_db)):
    """Get a story by ID"""
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    return story


@router.put("/stories/{story_id}", response_model=StoryResponse)
def update_story(
    story_id: int,
    updates: StoryUpdate,
    db: Session = Depends(get_db),
):
    """Update story properties"""
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    
    update_data = updates.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(story, field, value)
    
    db.commit()
    db.refresh(story)
    return story


@router.get("/stories/{story_id}/blueprint", response_model=ProductionBlueprintResponse)
def get_production_blueprint(story_id: int, db: Session = Depends(get_db)):
    """
    Get the complete production blueprint for a story.
    Includes all acts, scenes, characters, environments, and assets.
    """
    planner = MoviePlanningService(db)
    blueprint = planner.get_production_blueprint(story_id)
    
    # Calculate total duration
    scenes = blueprint["scenes"]
    total_duration = sum(s.estimated_duration_sec for s in scenes) / 60.0
    
    # Run validation
    validator = ValidationService(db)
    validation = validator.validate_story(story_id)
    
    return ProductionBlueprintResponse(
        story=blueprint["story"],
        acts=blueprint["acts"],
        scenes=blueprint["scenes"],
        characters=blueprint["characters"],
        environments=blueprint["environments"],
        assets=blueprint["assets"],
        total_estimated_duration_min=total_duration,
        scene_count=len(scenes),
        validation_warnings=[w["message"] for w in validation["warnings"]],
    )


# --- Act Endpoints ---

@router.get("/acts/{act_id}", response_model=ActResponse)
def get_act(act_id: int, db: Session = Depends(get_db)):
    """Get an act by ID"""
    act = db.query(Act).filter(Act.id == act_id).first()
    if not act:
        raise HTTPException(status_code=404, detail="Act not found")
    return act


@router.get("/acts/{act_id}/scenes", response_model=List[SceneResponse])
def get_act_scenes(act_id: int, db: Session = Depends(get_db)):
    """Get all scenes in an act"""
    scene_service = SceneService(db)
    scenes = scene_service.get_scenes_by_act(act_id)
    return scenes


# --- Scene Endpoints ---

@router.post("/scenes", response_model=SceneResponse, status_code=status.HTTP_201_CREATED)
def create_scene(
    scene_data: SceneCreate,
    db: Session = Depends(get_db),
):
    """Create a new scene"""
    scene_service = SceneService(db)
    
    scene = scene_service.create_scene(
        act_id=scene_data.act_id,
        title=scene_data.title or f"Scene {scene_data.order}",
        order=scene_data.order,
        slugline=scene_data.slugline,
        action_description=scene_data.action_description,
        environment_id=scene_data.environment_id,
        duration_sec=scene_data.estimated_duration_sec,
    )
    
    # Add characters if provided
    for char_link in scene_data.characters:
        scene_service.add_character_to_scene(
            scene_id=scene.id,
            character_id=char_link.character_id,
            role_in_scene=char_link.role_in_scene,
        )
    
    # Add dialogues if provided
    for dialogue in scene_data.dialogues:
        scene_service.add_dialogue(
            scene_id=scene.id,
            character_id=dialogue.character_id,
            text=dialogue.text or "",
            order=dialogue.order,
            emotion=dialogue.emotion,
        )
    
    return scene_service.get_scene(scene.id)


@router.get("/scenes/{scene_id}", response_model=SceneResponse)
def get_scene(scene_id: int, db: Session = Depends(get_db)):
    """Get a scene with all related data"""
    scene_service = SceneService(db)
    scene = scene_service.get_scene(scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    return scene


@router.put("/scenes/{scene_id}", response_model=SceneResponse)
def update_scene(
    scene_id: int,
    updates: SceneUpdate,
    db: Session = Depends(get_db),
):
    """Update scene properties"""
    scene_service = SceneService(db)
    scene = scene_service.update_scene(scene_id, updates)
    return scene


@router.post("/scenes/{scene_id}/generate-prompts")
def generate_scene_prompts(scene_id: int, db: Session = Depends(get_db)):
    """
    Generate AI-ready prompts for a scene.
    Creates image, video, audio, and negative prompts based on scene data.
    """
    scene_service = SceneService(db)
    prompts = scene_service.generate_scene_prompts(scene_id)
    return prompts


@router.delete("/scenes/{scene_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scene(scene_id: int, db: Session = Depends(get_db)):
    """Delete a scene"""
    scene_service = SceneService(db)
    scene_service.delete_scene(scene_id)
    return None


@router.post("/scenes/reorder")
def reorder_scenes(
    act_id: int,
    scene_order: List[int],
    db: Session = Depends(get_db),
):
    """Reorder scenes within an act"""
    scene_service = SceneService(db)
    scene_service.reorder_scenes(act_id, scene_order)
    return {"status": "success", "message": "Scenes reordered"}


# --- Character Endpoints ---

@router.post("/characters", response_model=CharacterResponse, status_code=status.HTTP_201_CREATED)
def create_character(
    character_data: CharacterCreate,
    db: Session = Depends(get_db),
):
    """Create a new character"""
    character = CharacterProfile(**character_data.model_dump())
    db.add(character)
    db.commit()
    db.refresh(character)
    return character


@router.get("/stories/{story_id}/characters", response_model=List[CharacterResponse])
def get_story_characters(story_id: int, db: Session = Depends(get_db)):
    """Get all characters in a story"""
    characters = (
        db.query(CharacterProfile)
        .filter(CharacterProfile.story_id == story_id)
        .all()
    )
    return characters


# --- Environment Endpoints ---

@router.post("/environments", response_model=EnvironmentResponse, status_code=status.HTTP_201_CREATED)
def create_environment(
    env_data: EnvironmentCreate,
    db: Session = Depends(get_db),
):
    """Create a new environment"""
    environment = Environment(**env_data.model_dump())
    db.add(environment)
    db.commit()
    db.refresh(environment)
    return environment


@router.get("/stories/{story_id}/environments", response_model=List[EnvironmentResponse])
def get_story_environments(story_id: int, db: Session = Depends(get_db)):
    """Get all environments in a story"""
    environments = (
        db.query(Environment)
        .filter(Environment.story_id == story_id)
        .all()
    )
    return environments


# --- Validation Endpoints ---

@router.get("/stories/{story_id}/validate")
def validate_story(story_id: int, db: Session = Depends(get_db)):
    """
    Validate a story's production blueprint.
    Returns errors and warnings.
    """
    validator = ValidationService(db)
    report = validator.validate_story(story_id)
    return report


@router.get("/stories/{story_id}/validation-summary")
def get_validation_summary(story_id: int, db: Session = Depends(get_db)):
    """Get a quick validation summary"""
    validator = ValidationService(db)
    summary = validator.get_validation_summary(story_id)
    return summary
