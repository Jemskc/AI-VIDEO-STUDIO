"""
Mock Voice (TTS) Provider.

Writes a real (if silent) placeholder audio file per task. Swap for a real
TTS model (XTTS v2, ...) later.
"""
import logging
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, AsyncIterator
from datetime import datetime

from app.providers.base import (
    VoiceProvider,
    GenerationRequest,
    GenerationResponse,
    ProgressUpdate,
)
from app.storage.local import get_storage_backend

logger = logging.getLogger(__name__)

PLACEHOLDER_VOICE = Path(__file__).resolve().parent.parent / "storage" / "placeholders" / "placeholder_voice.wav"


class MockVoiceProvider(VoiceProvider):
    provider_name: str = "voice"
    provider_version: str = "1.0.0-mock"
    supported_models: List[str] = ["mock-voice"]
    requires_gpu: bool = True
    gpu_memory_mb: int = 6000

    async def initialize(self, model_name: str = "mock-voice", **kwargs) -> bool:
        logger.info(f"Initializing mock voice provider with model: {model_name}")
        return True

    async def shutdown(self) -> None:
        pass

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        start_time = datetime.utcnow()
        is_valid, error = await self.validate_request(request)
        if not is_valid:
            return GenerationResponse(task_id=request.task_id, status="failed", error_message=error)

        audio_path = await self.generate_speech(text=request.prompt)
        return GenerationResponse(
            task_id=request.task_id,
            status="completed",
            result_url=audio_path,
            metadata={"text": request.prompt},
            processing_time_seconds=(datetime.utcnow() - start_time).total_seconds(),
        )

    async def generate_stream(self, request: GenerationRequest) -> AsyncIterator[ProgressUpdate]:
        yield ProgressUpdate(
            task_id=request.task_id, progress=1.0, stage="completed", message="Speech ready"
        )

    async def generate_speech(
        self,
        text: str,
        voice_id: str = "default",
        language: str = "en",
        speed: float = 1.0,
        pitch: float = 1.0,
        **kwargs,
    ) -> str:
        storage = get_storage_backend()
        relative_path = f"generated/{uuid.uuid4().hex}.wav"
        return storage.save_file(relative_path, str(PLACEHOLDER_VOICE))

    async def clone_voice(self, sample_audio_path: str, text: str, **kwargs) -> str:
        return await self.generate_speech(text=text)

    async def get_model_info(self, model_name: str) -> Dict[str, Any]:
        return {"name": model_name, "type": "voice_mock", "requires_gpu": True}

    async def validate_request(self, request: GenerationRequest) -> tuple[bool, Optional[str]]:
        if not request.prompt:
            return False, "Text is required"
        return True, None
