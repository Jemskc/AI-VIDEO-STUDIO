"""
Validation Engine Service.
Validates production blueprints for consistency and completeness.
"""
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session

from app.models.intelligence import (
    Story, Act, Scene, CharacterProfile, Environment,
    CameraPlan, DialogueLine, SceneCharacter, SceneAsset,
    AssetRegistry, ProductionMemory
)


class ValidationError:
    """Represents a validation error or warning"""
    def __init__(self, severity: str, entity_type: str, entity_id: int, message: str):
        self.severity = severity  # "error" or "warning"
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.message = message
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "severity": self.severity,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "message": self.message,
        }


class ValidationService:
    """
    Service for validating production blueprints.
    Checks for missing elements, broken references, and inconsistencies.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.errors: List[ValidationError] = []
    
    def validate_story(self, story_id: int) -> Dict[str, Any]:
        """
        Perform comprehensive validation on a story and its related entities.
        Returns a validation report.
        """
        self.errors = []
        
        story = self.db.query(Story).filter(Story.id == story_id).first()
        if not story:
            return {
                "valid": False,
                "errors": [{"severity": "error", "message": f"Story {story_id} not found"}],
                "warnings": [],
            }
        
        # Run all validations
        self._validate_acts(story_id)
        self._validate_scenes(story_id)
        self._validate_characters(story_id)
        self._validate_environments(story_id)
        self._validate_dependencies(story_id)
        self._validate_timeline(story_id)
        self._validate_assets(story_id)
        
        errors = [e.to_dict() for e in self.errors if e.severity == "error"]
        warnings = [e.to_dict() for e in self.errors if e.severity == "warning"]
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "error_count": len(errors),
            "warning_count": len(warnings),
        }
    
    def _validate_acts(self, story_id: int) -> None:
        """Validate act structure"""
        acts = self.db.query(Act).filter(Act.story_id == story_id).order_by(Act.order).all()
        
        if not acts:
            self.errors.append(ValidationError(
                "error", "story", story_id, "Story has no acts defined"
            ))
            return
        
        # Check for sequential ordering
        for i, act in enumerate(acts):
            if act.order != i + 1:
                self.errors.append(ValidationError(
                    "warning", "act", act.id, f"Act order is not sequential (expected {i+1}, got {act.order})"
                ))
    
    def _validate_scenes(self, story_id: int) -> None:
        """Validate scenes"""
        scenes = (
            self.db.query(Scene)
            .join(Act)
            .filter(Act.story_id == story_id)
            .all()
        )
        
        if not scenes:
            self.errors.append(ValidationError(
                "warning", "story", story_id, "Story has no scenes. Add scenes to continue."
            ))
            return
        
        for scene in scenes:
            # Check for title or description
            if not scene.title and not scene.action_description:
                self.errors.append(ValidationError(
                    "warning", "scene", scene.id, "Scene has no title or action description"
                ))
            
            # Check duration
            if scene.estimated_duration_sec <= 0:
                self.errors.append(ValidationError(
                    "error", "scene", scene.id, "Scene duration must be greater than 0"
                ))
            
            # Check for environment
            if not scene.environment_id:
                self.errors.append(ValidationError(
                    "warning", "scene", scene.id, "Scene has no environment assigned"
                ))
    
    def _validate_characters(self, story_id: int) -> None:
        """Validate characters"""
        characters = self.db.query(CharacterProfile).filter(
            CharacterProfile.story_id == story_id
        ).all()
        
        if not characters:
            self.errors.append(ValidationError(
                "warning", "story", story_id, "Story has no characters defined"
            ))
            return
        
        for char in characters:
            # Check for basic info
            if not char.appearance_description:
                self.errors.append(ValidationError(
                    "warning", "character", char.id, 
                    f"Character '{char.name}' has no appearance description"
                ))
    
    def _validate_environments(self, story_id: int) -> None:
        """Validate environments"""
        environments = self.db.query(Environment).filter(
            Environment.story_id == story_id
        ).all()
        
        if not environments:
            self.errors.append(ValidationError(
                "warning", "story", story_id, "Story has no environments defined"
            ))
    
    def _validate_dependencies(self, story_id: int) -> None:
        """Validate scene dependencies for circular references"""
        scenes = (
            self.db.query(Scene)
            .join(Act)
            .filter(Act.story_id == story_id)
            .all()
        )
        
        scene_ids = {s.id for s in scenes}
        
        for scene in scenes:
            if scene.dependencies:
                for dep_id in scene.dependencies:
                    if dep_id not in scene_ids:
                        self.errors.append(ValidationError(
                            "error", "scene", scene.id,
                            f"Scene depends on non-existent scene {dep_id}"
                        ))
        
        # Check for circular dependencies (simplified)
        # In production, use DFS for cycle detection
        for scene in scenes:
            if scene.dependencies and scene.id in scene.dependencies:
                self.errors.append(ValidationError(
                    "error", "scene", scene.id,
                    "Scene cannot depend on itself"
                ))
    
    def _validate_timeline(self, story_id: int) -> None:
        """Validate timeline consistency"""
        scenes = (
            self.db.query(Scene)
            .join(Act)
            .filter(Act.story_id == story_id)
            .order_by(Act.order, Scene.order)
            .all()
        )
        
        if not scenes:
            return
        
        # Check for duplicate ordering
        seen_orders = set()
        for scene in scenes:
            order_key = (scene.act_id, scene.order)
            if order_key in seen_orders:
                self.errors.append(ValidationError(
                    "error", "scene", scene.id,
                    "Duplicate scene order detected"
                ))
            seen_orders.add(order_key)
    
    def _validate_assets(self, story_id: int) -> None:
        """Validate asset references"""
        scenes = (
            self.db.query(Scene)
            .join(Act)
            .filter(Act.story_id == story_id)
            .all()
        )
        
        project_id = scenes[0].act.story.project_id if scenes else None
        if not project_id:
            return
        
        # Get all assets for this project
        assets = self.db.query(AssetRegistry).filter(
            AssetRegistry.project_id == project_id
        ).all()
        asset_ids = {a.id for a in assets}
        
        # Check scene asset references
        for scene in scenes:
            scene_assets = self.db.query(SceneAsset).filter(
                SceneAsset.scene_id == scene.id
            ).all()
            
            for sa in scene_assets:
                if sa.asset_id not in asset_ids:
                    self.errors.append(ValidationError(
                        "error", "scene_asset", sa.id,
                        f"Scene references non-existent asset {sa.asset_id}"
                    ))
    
    def get_validation_summary(self, story_id: int) -> Dict[str, Any]:
        """Get a quick validation summary"""
        report = self.validate_story(story_id)
        
        return {
            "story_id": story_id,
            "is_ready_for_production": report["valid"] and report["warning_count"] == 0,
            "can_proceed_with_warnings": report["valid"],
            "blocking_errors": report["error_count"],
            "warnings": report["warning_count"],
        }
