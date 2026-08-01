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
from app.services.scene_engine import SceneService


class MoviePlanningService:
    """
    Main service for analyzing movie prompts and generating production blueprints.
    In Phase 3, this uses rule-based logic. In Phase 4+, AI models will enhance this.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    AVG_SCENE_SECONDS = 30  # used to derive scene count from a target duration

    def analyze_prompt(
        self, prompt: str, target_duration_minutes: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Analyze a movie prompt to extract key elements.
        Returns structured data about genre, mood, themes, etc.

        If target_duration_minutes is given, it takes priority over the
        prompt-derived estimate for both duration and scene count.
        """
        analysis = {
            "genre": self._detect_genre(prompt),
            "mood": self._detect_mood(prompt),
            "themes": self._detect_themes(prompt),
            "estimated_scenes": self._estimate_scene_count(prompt, target_duration_minutes),
            "estimated_duration": self._estimate_duration(prompt, target_duration_minutes),
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
    
    def _estimate_scene_count(
        self, prompt: str, target_duration_minutes: Optional[float] = None
    ) -> int:
        """Estimate number of scenes based on prompt complexity, or from a target duration."""
        if target_duration_minutes:
            return max(1, round(target_duration_minutes * 60 / self.AVG_SCENE_SECONDS))

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

    def _estimate_duration(
        self, prompt: str, target_duration_minutes: Optional[float] = None
    ) -> float:
        """Estimate movie duration in minutes, or return an explicit target if given."""
        if target_duration_minutes:
            return float(target_duration_minutes)

        # Check for explicit duration mentions
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
            match = re.search(pattern, prompt_lower)
            if match:
                elements["characters"].append(match.group())
        
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
        title: Optional[str] = None,
        target_duration_minutes: Optional[float] = None,
    ) -> Story:
        """
        Create a complete story structure from a prompt.
        This is the main entry point for movie planning.

        target_duration_minutes lets the caller pick the movie's runtime
        (e.g. 15 minutes); scene count is derived from it instead of the
        prompt's word count when provided.
        """
        # Analyze the prompt
        analysis = self.analyze_prompt(prompt, target_duration_minutes)
        
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
        
        story_fields = story_data.model_dump()
        # StoryCreate.structure_type is the API-facing StoryStructureEnum (value-keyed, e.g.
        # "three_act"); the ORM column is typed against the separate StoryStructure enum, which
        # SQLAlchemy binds/looks-up by member name. Convert explicitly so round-tripping works.
        story_fields["structure_type"] = StoryStructure(story_fields["structure_type"])

        story = Story(**story_fields)
        self.db.add(story)
        self.db.commit()
        self.db.refresh(story)

        # Create basic structure (three acts)
        acts = self._create_act_structure(story.id, analysis)

        # Auto-populate characters and scenes so there's something to render
        characters = self._create_characters_from_analysis(project_id, story.id, analysis)
        self._create_scenes_from_analysis(acts, characters, analysis)

        # Store analysis in memory
        self._store_production_memory(project_id, "analysis", analysis)

        return story

    def _create_act_structure(self, story_id: int, analysis: Dict[str, Any]) -> List[Act]:
        """Create the three-act structure for a story"""
        act_configs = [
            {"order": 1, "title": "Act I - The Setup", "description": "Introduction to characters and world"},
            {"order": 2, "title": "Act II - The Confrontation", "description": "Rising action and conflicts"},
            {"order": 3, "title": "Act III - The Resolution", "description": "Climax and resolution"},
        ]

        acts = []
        for config in act_configs:
            act = Act(
                story_id=story_id,
                **config
            )
            self.db.add(act)
            acts.append(act)

        self.db.commit()
        for act in acts:
            self.db.refresh(act)

        return acts

    def _create_characters_from_analysis(
        self, project_id: int, story_id: int, analysis: Dict[str, Any]
    ) -> List[CharacterProfile]:
        """Create character profiles from names detected in the prompt (falls back to one protagonist)."""
        names = analysis["detected_elements"]["characters"] or ["Protagonist"]

        characters = []
        for index, name in enumerate(names):
            character = CharacterProfile(
                project_id=project_id,
                story_id=story_id,
                name=name.title(),
                role="Protagonist" if index == 0 else "Supporting",
                appearance_description=f"A {analysis['genre']} story character, {analysis['mood']} mood.",
            )
            self.db.add(character)
            characters.append(character)

        self.db.commit()
        for character in characters:
            self.db.refresh(character)

        return characters

    def _create_scenes_from_analysis(
        self, acts: List[Act], characters: List[CharacterProfile], analysis: Dict[str, Any]
    ) -> List[Scene]:
        """Distribute the estimated scene count round-robin across acts and generate prompts for each."""
        scene_service = SceneService(self.db)
        scene_count = analysis["estimated_scenes"]
        locations = analysis["detected_elements"]["locations"] or ["Unspecified Location"]
        # Spread the story's total target duration evenly across scenes so
        # total_estimated_duration_min (summed from scenes) matches story.estimated_duration_minutes.
        scene_duration_sec = (analysis["estimated_duration"] * 60) / scene_count

        scenes = []
        for i in range(scene_count):
            act = acts[i % len(acts)]
            order_in_act = i // len(acts)
            location = locations[i % len(locations)]

            scene = scene_service.create_scene(
                act_id=act.id,
                title=f"Scene {i + 1}",
                order=order_in_act,
                slugline=f"{location.upper()} - {analysis['mood'].upper()}",
                action_description=f"Action reflecting the story's {', '.join(analysis['themes'])} theme(s).",
                duration_sec=scene_duration_sec,
            )

            if characters:
                scene_service.add_character_to_scene(
                    scene_id=scene.id,
                    character_id=characters[i % len(characters)].id,
                )

            scene_service.generate_scene_prompts(scene.id)
            scenes.append(scene)

        return scenes
    
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
