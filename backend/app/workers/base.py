"""
Enhanced Worker Framework - Generic workers that execute provider interfaces.

Workers are model-agnostic and only interact with providers through abstract interfaces.
This allows new AI models to be added without modifying worker code.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Type
from datetime import datetime
from abc import ABC, abstractmethod
import uuid

from app.providers.base import (
    BaseProvider,
    LLMProvider,
    ImageProvider,
    VideoProvider,
    VoiceProvider,
    MusicProvider,
    GenerationRequest,
    ProgressUpdate
)
from app.gpu.manager import get_gpu_manager
from app.orchestrator.engine import Task, TaskStatus, TaskType, get_orchestrator

logger = logging.getLogger(__name__)


class WorkerStatus:
    """Worker status states."""
    IDLE = "idle"
    BUSY = "busy"
    OFFLINE = "offline"
    ERROR = "error"


class BaseWorker(ABC):
    """
    Abstract base class for all workers.
    
    Workers execute tasks by interacting with provider interfaces.
    They handle progress tracking, retries, timeouts, and error recovery.
    """
    
    worker_type: str = "base"
    
    def __init__(self, worker_id: Optional[str] = None):
        self.worker_id = worker_id or f"{self.worker_type}_{uuid.uuid4().hex[:8]}"
        self.status = WorkerStatus.IDLE
        self.current_task: Optional[Task] = None
        self.provider: Optional[BaseProvider] = None
        self._shutdown_event = asyncio.Event()
        self._heartbeat_interval = 30  # seconds
        self._last_heartbeat = datetime.utcnow()
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the worker and its provider."""
        pass
    
    @abstractmethod
    async def execute_task(self, task: Task) -> Dict[str, Any]:
        """
        Execute a single task.
        
        Args:
            task: Task to execute
            
        Returns:
            Result dictionary
        """
        pass
    
    async def start(self) -> None:
        """Start the worker loop."""
        logger.info(f"Worker {self.worker_id} starting...")
        
        if not await self.initialize():
            logger.error(f"Worker {self.worker_id} failed to initialize")
            self.status = WorkerStatus.ERROR
            return
        
        self.status = WorkerStatus.IDLE
        logger.info(f"Worker {self.worker_id} started and ready")
        
        while not self._shutdown_event.is_set():
            await self._heartbeat()
            
            # Get next task from orchestrator
            orchestrator = get_orchestrator()
            task = await orchestrator.get_next_ready_task(self.worker_type)
            
            if task:
                await self._process_task(task)
            else:
                await asyncio.sleep(1)  # Wait before polling again
        
        await self.shutdown()
        logger.info(f"Worker {self.worker_id} shutdown complete")
    
    async def _process_task(self, task: Task) -> None:
        """Process a single task with error handling."""
        self.status = WorkerStatus.BUSY
        self.current_task = task
        
        orchestrator = get_orchestrator()
        
        try:
            # Mark task as started
            await orchestrator.start_task(task.task_id, self.worker_id)
            logger.info(f"Worker {self.worker_id} executing task {task.task_id}")
            
            # Execute the task
            result = await self.execute_task(task)
            
            # Mark task as completed
            await orchestrator.complete_task(task.task_id, result)
            logger.info(f"Task {task.task_id} completed successfully")
            
        except asyncio.CancelledError:
            logger.warning(f"Task {task.task_id} was cancelled")
            await orchestrator.fail_task(
                task.task_id,
                "Task cancelled",
                should_retry=False
            )
            
        except Exception as e:
            logger.error(f"Task {task.task_id} failed: {str(e)}", exc_info=True)
            await orchestrator.fail_task(
                task.task_id,
                str(e),
                should_retry=True
            )
            
        finally:
            self.status = WorkerStatus.IDLE
            self.current_task = None
    
    async def _heartbeat(self) -> None:
        """Send heartbeat update."""
        now = datetime.utcnow()
        if (now - self._last_heartbeat).total_seconds() >= self._heartbeat_interval:
            self._last_heartbeat = now
            logger.debug(f"Worker {self.worker_id} heartbeat OK")
    
    async def shutdown(self) -> None:
        """Shutdown the worker gracefully."""
        logger.info(f"Shutting down worker {self.worker_id}...")
        self._shutdown_event.set()
        self.status = WorkerStatus.OFFLINE
        
        if self.provider:
            await self.provider.shutdown()
        
        logger.info(f"Worker {self.worker_id} shutdown complete")


class LLMWorker(BaseWorker):
    """Worker for LLM tasks (story generation, dialogue, etc.)."""
    
    worker_type: str = "llm"
    
    async def initialize(self) -> bool:
        """Initialize LLM provider."""
        # In production, load actual LLM provider plugin
        # from app.plugins.llm_qwen import QwenProvider
        # self.provider = QwenProvider()
        # await self.provider.initialize("qwen-72b")
        logger.info(f"LLM Worker {self.worker_id} initialized (provider pending)")
        return True
    
    async def execute_task(self, task: Task) -> Dict[str, Any]:
        """Execute an LLM task."""
        if task.task_type == TaskType.GENERATE_STORY:
            return await self._generate_story(task)
        else:
            raise ValueError(f"Unknown LLM task type: {task.task_type}")
    
    async def _generate_story(self, task: Task) -> Dict[str, Any]:
        """Generate or refine story content."""
        story_data = task.payload.get("story", {})
        
        # TODO: Call LLM provider when implemented
        # result = await self.provider.generate_text(
        #     prompt=story_data.get("prompt", ""),
        #     system_prompt="You are a professional screenwriter..."
        # )
        
        return {
            "status": "completed",
            "story": story_data,
            "generated_at": datetime.utcnow().isoformat()
        }


class ImageWorker(BaseWorker):
    """Worker for image generation tasks."""
    
    worker_type: str = "image"
    
    async def initialize(self) -> bool:
        """Initialize image provider."""
        # Reserve GPU memory
        gpu_manager = get_gpu_manager()
        reservation = await gpu_manager.reserve_gpu(
            task_id=f"init_{self.worker_id}",
            model_name="flux-dev",
            required_memory_mb=12000
        )
        
        if reservation:
            logger.info(f"GPU reserved for image worker {self.worker_id}")
        
        # In production, load actual image provider plugin
        # from app.plugins.image_flux import FluxProvider
        # self.provider = FluxProvider()
        # await self.provider.initialize("flux-dev")
        
        logger.info(f"Image Worker {self.worker_id} initialized (provider pending)")
        return True
    
    async def execute_task(self, task: Task) -> Dict[str, Any]:
        """Execute an image generation task."""
        if task.task_type in [TaskType.GENERATE_IMAGE, TaskType.GENERATE_CHARACTER]:
            return await self._generate_image(task)
        else:
            raise ValueError(f"Unknown image task type: {task.task_type}")
    
    async def _generate_image(self, task: Task) -> Dict[str, Any]:
        """Generate an image from prompt."""
        prompt = task.payload.get("prompt", "")
        width = task.payload.get("width", 1024)
        height = task.payload.get("height", 1024)
        
        # TODO: Call image provider when implemented
        # image_path = await self.provider.generate_image(
        #     prompt=prompt,
        #     width=width,
        #     height=height
        # )
        
        # Mock result for now
        return {
            "status": "completed",
            "image_path": f"/storage/generated/{task.task_id}.png",
            "width": width,
            "height": height,
            "prompt": prompt,
            "generated_at": datetime.utcnow().isoformat()
        }


class VideoWorker(BaseWorker):
    """Worker for video generation tasks."""
    
    worker_type: str = "video"
    
    async def initialize(self) -> bool:
        """Initialize video provider."""
        # Reserve GPU memory
        gpu_manager = get_gpu_manager()
        reservation = await gpu_manager.reserve_gpu(
            task_id=f"init_{self.worker_id}",
            model_name="wan-2.1",
            required_memory_mb=16000
        )
        
        if reservation:
            logger.info(f"GPU reserved for video worker {self.worker_id}")
        
        # In production, load actual video provider plugin
        # from app.plugins.video_wan import WanProvider
        # self.provider = WanProvider()
        # await self.provider.initialize("wan-2.1")
        
        logger.info(f"Video Worker {self.worker_id} initialized (provider pending)")
        return True
    
    async def execute_task(self, task: Task) -> Dict[str, Any]:
        """Execute a video generation task."""
        if task.task_type == TaskType.GENERATE_VIDEO:
            return await self._generate_video(task)
        else:
            raise ValueError(f"Unknown video task type: {task.task_type}")
    
    async def _generate_video(self, task: Task) -> Dict[str, Any]:
        """Generate a video from prompt."""
        prompt = task.payload.get("prompt", "")
        duration = task.payload.get("duration", 5.0)
        fps = task.payload.get("fps", 24)
        width = task.payload.get("width", 1280)
        height = task.payload.get("height", 720)
        
        # TODO: Call video provider when implemented
        # video_path = await self.provider.generate_video(
        #     prompt=prompt,
        #     duration=duration,
        #     fps=fps,
        #     width=width,
        #     height=height
        # )
        
        return {
            "status": "completed",
            "video_path": f"/storage/generated/{task.task_id}.mp4",
            "duration": duration,
            "fps": fps,
            "resolution": f"{width}x{height}",
            "prompt": prompt,
            "generated_at": datetime.utcnow().isoformat()
        }


class VoiceWorker(BaseWorker):
    """Worker for voice/speech generation tasks."""
    
    worker_type: str = "voice"
    
    async def initialize(self) -> bool:
        """Initialize voice provider."""
        gpu_manager = get_gpu_manager()
        reservation = await gpu_manager.reserve_gpu(
            task_id=f"init_{self.worker_id}",
            model_name="xtts-v2",
            required_memory_mb=6000
        )
        
        if reservation:
            logger.info(f"GPU reserved for voice worker {self.worker_id}")
        
        logger.info(f"Voice Worker {self.worker_id} initialized (provider pending)")
        return True
    
    async def execute_task(self, task: Task) -> Dict[str, Any]:
        """Execute a voice generation task."""
        if task.task_type == TaskType.GENERATE_VOICE:
            return await self._generate_speech(task)
        else:
            raise ValueError(f"Unknown voice task type: {task.task_type}")
    
    async def _generate_speech(self, task: Task) -> Dict[str, Any]:
        """Generate speech from text."""
        text = task.payload.get("text", "")
        voice_id = task.payload.get("voice_id", "default")
        
        # TODO: Call voice provider when implemented
        # audio_path = await self.provider.generate_speech(
        #     text=text,
        #     voice_id=voice_id
        # )
        
        return {
            "status": "completed",
            "audio_path": f"/storage/generated/{task.task_id}.wav",
            "text": text,
            "voice_id": voice_id,
            "generated_at": datetime.utcnow().isoformat()
        }


class MusicWorker(BaseWorker):
    """Worker for music generation tasks."""
    
    worker_type: str = "music"
    
    async def initialize(self) -> bool:
        """Initialize music provider."""
        gpu_manager = get_gpu_manager()
        reservation = await gpu_manager.reserve_gpu(
            task_id=f"init_{self.worker_id}",
            model_name="audiocraft",
            required_memory_mb=8000
        )
        
        if reservation:
            logger.info(f"GPU reserved for music worker {self.worker_id}")
        
        logger.info(f"Music Worker {self.worker_id} initialized (provider pending)")
        return True
    
    async def execute_task(self, task: Task) -> Dict[str, Any]:
        """Execute a music generation task."""
        if task.task_type == TaskType.GENERATE_MUSIC:
            return await self._generate_music(task)
        else:
            raise ValueError(f"Unknown music task type: {task.task_type}")
    
    async def _generate_music(self, task: Task) -> Dict[str, Any]:
        """Generate music from prompt."""
        prompt = task.payload.get("audio_plan", {}).get("prompt", "")
        duration = task.payload.get("duration", 30.0)
        
        # TODO: Call music provider when implemented
        # audio_path = await self.provider.generate_music(
        #     prompt=prompt,
        #     duration=duration
        # )
        
        return {
            "status": "completed",
            "audio_path": f"/storage/generated/{task.task_id}.mp3",
            "prompt": prompt,
            "duration": duration,
            "generated_at": datetime.utcnow().isoformat()
        }


class RenderWorker(BaseWorker):
    """Worker for final video rendering (FFmpeg composition)."""
    
    worker_type: str = "render"
    
    async def initialize(self) -> bool:
        """Initialize render worker."""
        logger.info(f"Render Worker {self.worker_id} initialized")
        return True
    
    async def execute_task(self, task: Task) -> Dict[str, Any]:
        """Execute a render task."""
        if task.task_type == TaskType.RENDER:
            return await self._render_movie(task)
        else:
            raise ValueError(f"Unknown render task type: {task.task_type}")
    
    async def _render_movie(self, task: Task) -> Dict[str, Any]:
        """Compose final movie from generated assets."""
        # TODO: Implement FFmpeg rendering
        # This will combine all scene videos, audio, music, subtitles
        
        return {
            "status": "completed",
            "output_path": f"/storage/renders/{task.task_id}.mp4",
            "generated_at": datetime.utcnow().isoformat()
        }


# Worker Registry
class WorkerRegistry:
    """Central registry for available workers."""
    
    _workers: Dict[str, BaseWorker] = {}
    
    @classmethod
    def register(cls, worker: BaseWorker) -> None:
        """Register a worker instance."""
        cls._workers[worker.worker_id] = worker
    
    @classmethod
    def get_worker(cls, worker_id: str) -> Optional[BaseWorker]:
        """Get a worker by ID."""
        return cls._workers.get(worker_id)
    
    @classmethod
    def list_workers(cls) -> List[Dict[str, Any]]:
        """List all registered workers with status."""
        return [
            {
                "worker_id": w.worker_id,
                "worker_type": w.worker_type,
                "status": w.status,
                "current_task": w.current_task.task_id if w.current_task else None
            }
            for w in cls._workers.values()
        ]
    
    @classmethod
    def get_workers_by_type(cls, worker_type: str) -> List[BaseWorker]:
        """Get all workers of a specific type."""
        return [w for w in cls._workers.values() if w.worker_type == worker_type]


def create_worker(worker_type: str, worker_id: Optional[str] = None) -> Optional[BaseWorker]:
    """Factory function to create workers by type."""
    worker_classes: Dict[str, Type[BaseWorker]] = {
        "llm": LLMWorker,
        "image": ImageWorker,
        "video": VideoWorker,
        "voice": VoiceWorker,
        "music": MusicWorker,
        "render": RenderWorker
    }
    
    worker_class = worker_classes.get(worker_type)
    if not worker_class:
        logger.error(f"Unknown worker type: {worker_type}")
        return None
    
    return worker_class(worker_id=worker_id)
