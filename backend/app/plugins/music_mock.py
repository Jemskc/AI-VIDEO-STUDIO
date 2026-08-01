"""
Mock Music Provider.

Writes a real (if silent) placeholder audio file per task. Swap for a real
music model (AudioCraft/MusicGen, ...) later.
"""
import logging
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, AsyncIterator
from datetime import datetime

from app.providers.base import (
    MusicProvider,
    GenerationRequest,
    GenerationResponse,
    ProgressUpdate,
)
from app.storage.local import get_storage_backend

logger = logging.getLogger(__name__)

PLACEHOLDER_MUSIC = Path(__file__).resolve().parent.parent / "storage" / "placeholders" / "placeholder_music.mp3"


class MockMusicProvider(MusicProvider):
    provider_name: str = "music"
    provider_version: str = "1.0.0-mock"
    supported_models: List[str] = ["mock-music"]
    requires_gpu: bool = True
    gpu_memory_mb: int = 8000

    async def initialize(self, model_name: str = "mock-music", **kwargs) -> bool:
        logger.info(f"Initializing mock music provider with model: {model_name}")
        return True

    async def shutdown(self) -> None:
        pass

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        start_time = datetime.utcnow()
        is_valid, error = await self.validate_request(request)
        if not is_valid:
            return GenerationResponse(task_id=request.task_id, status="failed", error_message=error)

        audio_path = await self.generate_music(prompt=request.prompt, duration=request.duration or 30.0)
        return GenerationResponse(
            task_id=request.task_id,
            status="completed",
            result_url=audio_path,
            metadata={"prompt": request.prompt},
            processing_time_seconds=(datetime.utcnow() - start_time).total_seconds(),
        )

    async def generate_stream(self, request: GenerationRequest) -> AsyncIterator[ProgressUpdate]:
        yield ProgressUpdate(
            task_id=request.task_id, progress=1.0, stage="completed", message="Music ready"
        )

    async def generate_music(
        self,
        prompt: str,
        duration: float = 30.0,
        genre: Optional[str] = None,
        tempo: Optional[float] = None,
        **kwargs,
    ) -> str:
        storage = get_storage_backend()
        relative_path = f"generated/{uuid.uuid4().hex}.mp3"
        return storage.save_file(relative_path, str(PLACEHOLDER_MUSIC))

    async def generate_sound_effect(self, prompt: str, duration: float = 5.0, **kwargs) -> str:
        return await self.generate_music(prompt=prompt, duration=duration)

    async def get_model_info(self, model_name: str) -> Dict[str, Any]:
        return {"name": model_name, "type": "music_mock", "requires_gpu": True}

    async def validate_request(self, request: GenerationRequest) -> tuple[bool, Optional[str]]:
        if not request.prompt:
            return False, "Prompt is required"
        return True, None
