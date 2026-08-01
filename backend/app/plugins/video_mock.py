"""
Mock Video Provider.

Writes a real (if trivial) placeholder video file to disk per task so the
downstream FFmpeg render step has real inputs to concatenate. Swap this out
for a real video model (CogVideoX, Wan2.1, HunyuanVideo, ...) later.
"""
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, AsyncIterator
from datetime import datetime

from app.providers.base import (
    VideoProvider,
    GenerationRequest,
    GenerationResponse,
    ProgressUpdate,
)
from app.storage.local import get_storage_backend

logger = logging.getLogger(__name__)

PLACEHOLDER_VIDEO = Path(__file__).resolve().parent.parent / "storage" / "placeholders" / "placeholder_video.mp4"


class MockVideoProvider(VideoProvider):
    provider_name: str = "video"
    provider_version: str = "1.0.0-mock"
    supported_models: List[str] = ["mock-video"]
    requires_gpu: bool = True
    gpu_memory_mb: int = 16000

    async def initialize(self, model_name: str = "mock-video", **kwargs) -> bool:
        logger.info(f"Initializing mock video provider with model: {model_name}")
        return True

    async def shutdown(self) -> None:
        pass

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        start_time = datetime.utcnow()
        is_valid, error = await self.validate_request(request)
        if not is_valid:
            return GenerationResponse(task_id=request.task_id, status="failed", error_message=error)

        video_path = await self.generate_video(
            prompt=request.prompt,
            duration=request.duration or 5.0,
            fps=request.fps or 24,
        )
        return GenerationResponse(
            task_id=request.task_id,
            status="completed",
            result_url=video_path,
            metadata={"prompt": request.prompt, "duration": request.duration or 5.0},
            processing_time_seconds=(datetime.utcnow() - start_time).total_seconds(),
        )

    async def generate_stream(self, request: GenerationRequest) -> AsyncIterator[ProgressUpdate]:
        yield ProgressUpdate(
            task_id=request.task_id, progress=1.0, stage="completed", message="Video ready"
        )

    async def generate_video(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        duration: float = 5.0,
        fps: int = 24,
        width: int = 1280,
        height: int = 720,
        seed: Optional[int] = None,
        **kwargs,
    ) -> str:
        import uuid

        storage = get_storage_backend()
        relative_path = f"generated/{uuid.uuid4().hex}.mp4"
        return storage.save_file(relative_path, str(PLACEHOLDER_VIDEO))

    async def img2video(self, image_path: str, prompt: str, duration: float = 5.0, **kwargs) -> str:
        return await self.generate_video(prompt=prompt, duration=duration)

    async def video2video(self, video_path: str, prompt: str, strength: float = 0.75, **kwargs) -> str:
        return video_path

    async def get_model_info(self, model_name: str) -> Dict[str, Any]:
        return {"name": model_name, "type": "video_mock", "requires_gpu": True}

    async def validate_request(self, request: GenerationRequest) -> tuple[bool, Optional[str]]:
        if not request.prompt:
            return False, "Prompt is required"
        return True, None
