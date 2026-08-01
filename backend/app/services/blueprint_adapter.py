"""
Adapts MoviePlanningService.get_production_blueprint()'s ORM-object blueprint
into the flat dict shape Orchestrator._generate_tasks_from_blueprint expects
(characters/scenes/dialogue as plain dict lists, project_id as str).
"""
from typing import Any, Dict


def to_orchestrator_blueprint(blueprint: Dict[str, Any]) -> Dict[str, Any]:
    story = blueprint["story"]

    characters = [
        {
            "id": c.id,
            # CharacterProfile has no dedicated image_prompt field; reuse the
            # appearance description as the image prompt for the mock pipeline.
            "image_prompt": c.appearance_description or f"{c.name}, {c.role or 'character'}",
        }
        for c in blueprint["characters"]
    ]

    scenes = [
        {"id": s.id, "image_prompt": s.image_prompt or "", "video_prompt": s.video_prompt or ""}
        for s in blueprint["scenes"]
    ]

    dialogue = [
        {"scene_id": s.id, "text": line.text or "", "voice_id": line.voice_id_ref or "default"}
        for s in blueprint["scenes"]
        for line in s.dialogues
    ]

    return {
        "id": story.id,
        "project_id": str(story.project_id),
        "story": {"id": story.id, "title": story.title, "synopsis": story.synopsis},
        "characters": characters,
        "scenes": scenes,
        "dialogue": dialogue,
        "audio_plan": {"prompt": f"{story.genre} {story.mood} soundtrack"},
    }
