"""
Scene Engine Service.
Manages scene creation, planning, and prompt generation.
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session, joinedload

from app.models.intelligence import (
    Scene, Act, Environment, CharacterProfile, CameraPlan,
    DialogueLine, SceneCharacter, SceneAsset, AssetRegistry,
    ShotType, CameraMovement, LightingStyle
)
from app.schemas.intelligence import SceneCreate, SceneUpdate


class SceneService:
    """
    Service for managing scenes within a production.
    Handles scene creation, ordering, and prompt generation.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_scene(
        self,
        act_id: int,
        title: str,
        order: int,
        slugline: Optional[str] = None,
        action_description: Optional[str] = None,
        environment_id: Optional[int] = None,
        duration_sec: float = 10.0,
    ) -> Scene:
        """Create a new scene"""
        scene = Scene(
            act_id=act_id,
            title=title,
            order=order,
            slugline=slugline,
            action_description=action_description,
            environment_id=environment_id,
            estimated_duration_sec=duration_sec,
        )
        self.db.add(scene)
        self.db.flush()  # assign scene.id before it's referenced by the camera plan FK

        # Auto-generate camera plan
        camera_plan = CameraPlan(scene_id=scene.id)
        self.db.add(camera_plan)

        self.db.commit()
        self.db.refresh(scene)

        return scene
    
    def get_scene(self, scene_id: int) -> Optional[Scene]:
        """Get a scene with all related data"""
        scene = (
            self.db.query(Scene)
            .options(
                joinedload(Scene.environment),
                joinedload(Scene.camera_plan),
                joinedload(Scene.characters),
                joinedload(Scene.dialogues),
                joinedload(Scene.assets_required),
            )
            .filter(Scene.id == scene_id)
            .first()
        )
        return scene
    
    def update_scene(self, scene_id: int, updates: SceneUpdate) -> Scene:
        """Update scene properties"""
        scene = self.db.query(Scene).filter(Scene.id == scene_id).first()
        if not scene:
            raise ValueError(f"Scene {scene_id} not found")
        
        update_data = updates.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(scene, field, value)
        
        self.db.commit()
        self.db.refresh(scene)
        return scene
    
    def reorder_scenes(self, act_id: int, scene_order: List[int]) -> bool:
        """
        Reorder scenes within an act.
        scene_order is a list of scene IDs in the desired order.
        """
        scenes = (
            self.db.query(Scene)
            .filter(Scene.act_id == act_id)
            .filter(Scene.id.in_(scene_order))
            .all()
        )
        
        if len(scenes) != len(scene_order):
            raise ValueError("Scene order list doesn't match available scenes")
        
        for index, scene_id in enumerate(scene_order):
            scene = next(s for s in scenes if s.id == scene_id)
            scene.order = index
        
        self.db.commit()
        return True
    
    def add_character_to_scene(
        self,
        scene_id: int,
        character_id: int,
        role_in_scene: Optional[str] = None,
        emotional_state: Optional[str] = None,
    ) -> SceneCharacter:
        """Add a character to a scene"""
        scene_char = SceneCharacter(
            scene_id=scene_id,
            character_id=character_id,
            role_in_scene=role_in_scene,
            emotional_state=emotional_state,
        )
        self.db.add(scene_char)
        self.db.commit()
        self.db.refresh(scene_char)
        return scene_char
    
    def add_dialogue(
        self,
        scene_id: int,
        character_id: Optional[int],
        text: str,
        order: int,
        emotion: Optional[str] = None,
    ) -> DialogueLine:
        """Add a dialogue line to a scene"""
        dialogue = DialogueLine(
            scene_id=scene_id,
            character_id=character_id,
            text=text,
            order=order,
            emotion=emotion,
        )
        self.db.add(dialogue)
        self.db.commit()
        self.db.refresh(dialogue)
        return dialogue
    
    def generate_scene_prompts(self, scene_id: int) -> Dict[str, str]:
        """
        Generate prompts for AI generation based on scene data.
        In Phase 3, this creates template-based prompts.
        In Phase 4+, AI will enhance these.
        """
        scene = self.get_scene(scene_id)
        if not scene:
            raise ValueError(f"Scene {scene_id} not found")
        
        # Build image prompt
        image_parts = []
        
        # Add slugline/setting
        if scene.slugline:
            image_parts.append(f"Scene: {scene.slugline}")
        
        # Add environment details
        if scene.environment:
            env = scene.environment
            image_parts.append(f"Location: {env.name}")
            if env.description:
                image_parts.append(env.description)
            if env.lighting_style:
                image_parts.append(f"Lighting: {env.lighting_style.value}")
            if env.time_of_day:
                image_parts.append(f"Time: {env.time_of_day}")
            if env.weather_conditions:
                image_parts.append(f"Weather: {env.weather_conditions}")
        
        # Add characters
        if scene.characters:
            char_names = []
            for sc in scene.characters:
                char = sc.character
                char_desc = f"{char.name}"
                if char.appearance_description:
                    char_desc += f", {char.appearance_description}"
                if char.outfit_description:
                    char_desc += f", wearing {char.outfit_description}"
                char_names.append(char_desc)
            image_parts.append(f"Characters: {', '.join(char_names)}")
        
        # Add action
        if scene.action_description:
            image_parts.append(f"Action: {scene.action_description}")
        
        # Add camera direction
        if scene.camera_plan:
            cp = scene.camera_plan
            image_parts.append(f"Shot: {cp.shot_type.value}, {cp.movement.value}")
            image_parts.append(f"Lens: {cp.lens_mm}mm, Aperture: {cp.aperture}")
        
        image_prompt = ". ".join(image_parts) + ". Cinematic, high quality, film still."
        
        # Build negative prompt
        negative_prompt = "blurry, low quality, distorted, deformed, ugly, bad anatomy, watermark, text, signature"
        
        # Build video prompt
        video_prompt = f"{image_prompt} Smooth camera movement: {scene.camera_plan.movement.value if scene.camera_plan else 'static'}. 24fps, cinematic motion."
        
        # Build audio prompt
        audio_parts = []
        if scene.environment:
            audio_parts.append(f"Ambience: {scene.environment.name}")
        if scene.dialogues:
            audio_parts.append(f"Dialogue: {len(scene.dialogues)} lines")
        
        audio_prompt = ". ".join(audio_parts) if audio_parts else "Silent scene"
        
        # Update scene with generated prompts
        scene.image_prompt = image_prompt
        scene.video_prompt = video_prompt
        scene.negative_prompt = negative_prompt
        scene.audio_prompt = audio_prompt
        
        self.db.commit()
        
        return {
            "image_prompt": image_prompt,
            "video_prompt": video_prompt,
            "negative_prompt": negative_prompt,
            "audio_prompt": audio_prompt,
        }
    
    def delete_scene(self, scene_id: int) -> bool:
        """Delete a scene and all related data"""
        scene = self.db.query(Scene).filter(Scene.id == scene_id).first()
        if not scene:
            raise ValueError(f"Scene {scene_id} not found")
        
        self.db.delete(scene)
        self.db.commit()
        return True
    
    def get_scenes_by_act(self, act_id: int) -> List[Scene]:
        """Get all scenes in an act, ordered"""
        scenes = (
            self.db.query(Scene)
            .filter(Scene.act_id == act_id)
            .order_by(Scene.order)
            .all()
        )
        return scenes
    
    def get_scenes_by_story(self, story_id: int) -> List[Scene]:
        """Get all scenes in a story, ordered by act and scene order"""
        scenes = (
            self.db.query(Scene)
            .join(Act)
            .filter(Act.story_id == story_id)
            .order_by(Act.order, Scene.order)
            .all()
        )
        return scenes
