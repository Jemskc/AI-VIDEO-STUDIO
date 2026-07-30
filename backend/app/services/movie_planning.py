"""
Movie Planning Engine Service.
Analyzes prompts and creates complete production blueprints.
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import re

from app.models.intelligence import (
    Story, Act, Scene, CharacterProfile, Environment,
    CameraPlan, DialogueLine, AssetRegistry, SceneCharacter,
    SceneAsset, ProductionMemory, StoryStructure, LightingStyle
)
from app.schemas.intelligence import StoryCreate, CharacterCreate, EnvironmentCreate


class MoviePlanningService:
    """
    Main service for analyzing movie prompts and generating production blueprints.
    In Phase 3, this uses rule-based logic. In Phase 4+, AI models will enhance this.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def analyze_prompt(self, prompt: str) -> Dict[str, Any]:
        """
        Analyze a movie prompt to extract key elements.
        Returns structured data about genre, mood, themes, etc.
        """
        analysis = {
            "genre": self._detect_genre(prompt),
            "mood": self._detect_mood(prompt),
            "themes": self._detect_themes(prompt),
            "estimated_scenes": self._estimate_scene_count(prompt),
            "estimated_duration": self._estimate_duration(prompt),
            "detected_elements": self._extract_elements(prompt),
        }
        return analysis
    
    def _detect_genre(self, prompt: str) -> str:
        """Detect genre from keywords in prompt"""
        prompt_lower = prompt.lower()
        
        genre_keywords = {
            "sci-fi": ["space", "alien", "mars", "future", "robot", "spaceship", "planet", "sci-fi", "scifi"],
            "fantasy": ["magic", "dragon", "wizard", "kingdom", "fantasy", "enchanted", "mythical"],
            "horror": ["horror", "scary", "ghost", "monster", "dark", "terrifying", "nightmare"],
            "action": ["action", "chase", "fight", "battle", "explosion", "hero", "adventure"],
            "drama": ["drama", "emotional", "relationship", "family", "love", "tragedy"],
            "comedy": ["comedy", "funny", "humor", "laugh", "hilarious", "comedic"],
            "documentary": ["documentary", "real", "factual", "history", "nature"],
        }
        
        for genre, keywords in genre_keywords.items():
            if any(keyword in prompt_lower for keyword in keywords):
                return genre
        
        return "general"
    
    def _detect_mood(self, prompt: str) -> str:
        """Detect mood from prompt"""
        prompt_lower = prompt.lower()
        
        mood_keywords = {
            "dark": ["dark", "ominous", "sinister", "foreboding", "gloomy"],
            "uplifting": ["uplifting", "hopeful", "inspiring", "joyful", "triumphant"],
            "tense": ["tense", "suspenseful", "thrilling", "intense", "nervous"],
            "melancholic": ["melancholic", "sad", "somber", "poignant", "reflective"],
            "mysterious": ["mysterious", "enigmatic", "puzzling", "cryptic", "unknown"],
            "epic": ["epic", "grand", "majestic", "spectacular", "monumental"],
        }
        
        for mood, keywords in mood_keywords.items():
            if any(keyword in prompt_lower for keyword in keywords):
                return mood
        
        return "neutral"
    
    def _detect_themes(self, prompt: str) -> List[str]:
        """Extract themes from prompt"""
        themes = []
        prompt_lower = prompt.lower()
        
        theme_map = {
            "survival": ["survive", "stranded", "alone", "desperate"],
            "discovery": ["discover", "find", "uncover", "explore", "exploration"],
            "redemption": ["redemption", "forgive", "atonement", "second chance"],
            "conflict": ["war", "battle", "fight", "conflict", "struggle"],
            "identity": ["identity", "who am i", "self-discovery", "belonging"],
            "technology": ["technology", "ai", "machine", "digital", "cyber"],
            "nature": ["nature", "environment", "natural", "wilderness"],
        }
        
        for theme, keywords in theme_map.items():
            if any(keyword in prompt_lower for keyword in keywords):
                themes.append(theme)
        
        return themes if themes else ["general"]
    
    def _estimate_scene_count(self, prompt: str) -> int:
        """Estimate number of scenes based on prompt complexity"""
        # Simple heuristic: longer prompts suggest more complex stories
        word_count = len(prompt.split())
        
        if word_count < 20:
            return 5
        elif word_count < 50:
            return 8
        elif word_count < 100:
            return 12
        else:
            return 15
    
    def _estimate_duration(self, prompt: str) -> float:
        """Estimate movie duration in minutes"""
        # Check for explicit duration mentions
        import re
        match = re.search(r'(\d+)\s*(minute|min)', prompt.lower())
        if match:
            return float(match.group(1))
        
        # Default based on scene count estimate
        scene_count = self._estimate_scene_count(prompt)
        return scene_count * 0.5  # Average 30 seconds per scene
    
    def _extract_elements(self, prompt: str) -> Dict[str, List[str]]:
        """Extract specific elements like characters, locations, objects"""
        elements = {
            "characters": [],
            "locations": [],
            "objects": [],
        }
        
        # Simple extraction - in Phase 4+ AI will do NER
        prompt_lower = prompt.lower()
        
        # Character patterns
        char_patterns = [r'astronaut[s]?', r'alien[s]?', r'scientist[s]?', r'doctor[s]?', 
                        r'captain', r'crew', r'team', r'protagonist', r'hero']
        for pattern in char_patterns:
            if re.search(pattern, prompt_lower):
                elements["characters"].append(re.match(pattern, prompt_lower).group())
        
        # Location patterns
        loc_patterns = [r'mars', r'space station', r'spaceship', r'city', r'planet', 
                       r'base', r'laboratory', r'facility']
        for pattern in loc_patterns:
            if re.search(pattern, prompt_lower):
                elements["locations"].append(pattern.replace('_', ' ').title())
        
        return elements
    
    def create_story_from_prompt(
        self, 
        project_id: int, 
        prompt: str,
        title: Optional[str] = None
    ) -> Story:
        """
        Create a complete story structure from a prompt.
        This is the main entry point for movie planning.
        """
        # Analyze the prompt
        analysis = self.analyze_prompt(prompt)
        
        # Create story
        story_data = StoryCreate(
            project_id=project_id,
            title=title or f"Untitled Project {project_id}",
            logline=prompt[:255],
            synopsis=prompt,
            genre=analysis["genre"],
            mood=analysis["mood"],
            theme=", ".join(analysis["themes"]),
            estimated_duration_minutes=analysis["estimated_duration"],
            structure_type=StoryStructure.THREE_ACT
        )
        
        story = Story(**story_data.model_dump())
        self.db.add(story)
        self.db.commit()
        self.db.refresh(story)
        
        # Create basic structure (acts, initial scenes placeholder)
        self._create_act_structure(story.id, analysis)
        
        # Store analysis in memory
        self._store_production_memory(project_id, "analysis", analysis)
        
        return story
    
    def _create_act_structure(self, story_id: int, analysis: Dict[str, Any]) -> None:
        """Create the three-act structure for a story"""
        act_configs = [
            {"order": 1, "title": "Act I - The Setup", "description": "Introduction to characters and world"},
            {"order": 2, "title": "Act II - The Confrontation", "description": "Rising action and conflicts"},
            {"order": 3, "title": "Act III - The Resolution", "description": "Climax and resolution"},
        ]
        
        for config in act_configs:
            act = Act(
                story_id=story_id,
                **config
            )
            self.db.add(act)
        
        self.db.commit()
    
    def _store_production_memory(
        self, 
        project_id: int, 
        entity_type: str, 
        data: Dict[str, Any]
    ) -> None:
        """Store important production decisions in memory"""
        for key, value in data.items():
            if isinstance(value, (list, dict)):
                value = str(value)
            
            memory = ProductionMemory(
                project_id=project_id,
                entity_type=entity_type,
                key=key,
                value=value,
                source="planning_engine"
            )
            self.db.add(memory)
        
        self.db.commit()
    
    def get_production_blueprint(self, story_id: int) -> Dict[str, Any]:
        """
        Retrieve the complete production blueprint for a story.
        Includes all acts, scenes, characters, environments, and assets.
        """
        story = self.db.query(Story).filter(Story.id == story_id).first()
        if not story:
            raise ValueError(f"Story {story_id} not found")
        
        # Gather all related data
        acts = self.db.query(Act).filter(Act.story_id == story_id).order_by(Act.order).all()
        scenes = self.db.query(Scene).join(Act).filter(Act.story_id == story_id).order_by(Scene.order).all()
        characters = self.db.query(CharacterProfile).filter(CharacterProfile.story_id == story_id).all()
        environments = self.db.query(Environment).filter(Environment.story_id == story_id).all()
        assets = self.db.query(AssetRegistry).filter(AssetRegistry.project_id == story.project_id).all()
        
        # Calculate totals
        total_duration = sum(scene.estimated_duration_sec for scene in scenes) / 60.0
        
        blueprint = {
            "story": story,
            "acts": acts,
            "scenes": scenes,
            "characters": characters,
            "environments": environments,
            "assets": assets,
            "total_estimated_duration_min": total_duration,
            "scene_count": len(scenes),
        }
        
        return blueprint
