"""
AI Provider Interfaces - Abstract Base Classes

All AI models must implement these interfaces to be compatible with the platform.
This ensures model-agnostic execution and easy plugin integration.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, AsyncIterator
from pydantic import BaseModel, Field
import uuid
from datetime import datetime


class GenerationRequest(BaseModel):
    """Base request model for all generation tasks."""
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    prompt: str
    negative_prompt: Optional[str] = None
    seed: Optional[int] = None
    steps: Optional[int] = None
    guidance_scale: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None
    duration: Optional[float] = None  # For video/audio
    fps: Optional[int] = None  # For video
    extra_params: Dict[str, Any] = Field(default_factory=dict)


class GenerationResponse(BaseModel):
    """Base response model for all generation tasks."""
    task_id: str
    status: str  # pending, running, completed, failed
    result_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    processing_time_seconds: Optional[float] = None


class ProgressUpdate(BaseModel):
    """Progress update streamed during generation."""
    task_id: str
    progress: float  # 0.0 to 1.0
    stage: str
    message: str
    eta_seconds: Optional[float] = None
    current_step: Optional[int] = None
    total_steps: Optional[int] = None


class BaseProvider(ABC):
    """
    Abstract base class for all AI providers.
    
    Each provider (LLM, Image, Video, Voice, Music) must implement this interface.
    The platform interacts only with this interface, never directly with models.
    """
    
    provider_name: str = "base"
    provider_version: str = "1.0.0"
    supported_models: List[str] = []
    requires_gpu: bool = False
    gpu_memory_mb: int = 0
    
    @abstractmethod
    async def initialize(self, model_name: str, **kwargs) -> bool:
        """
        Initialize the provider with a specific model.
        
        Args:
            model_name: Name of the model to load
            **kwargs: Additional configuration parameters
            
        Returns:
            True if initialization successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Release all resources and unload the model."""
        pass
    
    @abstractmethod
    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """
        Execute a generation task.
        
        Args:
            request: Generation request with all parameters
            
        Returns:
            Generation response with result URL or error
        """
        pass
    
    @abstractmethod
    async def generate_stream(
        self, 
        request: GenerationRequest
    ) -> AsyncIterator[ProgressUpdate]:
        """
        Stream progress updates during generation.
        
        Args:
            request: Generation request
            
        Yields:
            ProgressUpdate objects with current status
        """
        pass
    
    @abstractmethod
    async def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """
        Get information about a specific model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Dictionary with model metadata
        """
        pass
    
    @abstractmethod
    async def validate_request(self, request: GenerationRequest) -> tuple[bool, Optional[str]]:
        """
        Validate a generation request before execution.
        
        Args:
            request: Generation request to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        pass
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check provider health status.
        
        Returns:
            Health status dictionary
        """
        return {
            "provider": self.provider_name,
            "version": self.provider_version,
            "status": "healthy",
            "models_loaded": self.supported_models,
            "gpu_required": self.requires_gpu,
            "gpu_memory_mb": self.gpu_memory_mb
        }


class LLMProvider(BaseProvider):
    """Interface for Large Language Model providers."""
    
    provider_name: str = "llm"
    
    @abstractmethod
    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """Generate text completion."""
        pass
    
    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        output_schema: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """Generate structured JSON output."""
        pass


class ImageProvider(BaseProvider):
    """Interface for Image Generation providers."""
    
    provider_name: str = "image"
    
    @abstractmethod
    async def generate_image(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        width: int = 1024,
        height: int = 1024,
        steps: int = 30,
        guidance_scale: float = 7.5,
        seed: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Generate an image and return the file path.
        
        Returns:
            Path to the generated image file
        """
        pass
    
    @abstractmethod
    async def upscale_image(
        self,
        image_path: str,
        scale_factor: int = 2,
        **kwargs
    ) -> str:
        """Upscale an existing image."""
        pass
    
    @abstractmethod
    async def img2img(
        self,
        image_path: str,
        prompt: str,
        strength: float = 0.75,
        **kwargs
    ) -> str:
        """Image-to-image transformation."""
        pass


class VideoProvider(BaseProvider):
    """Interface for Video Generation providers."""
    
    provider_name: str = "video"
    requires_gpu: bool = True
    gpu_memory_mb: int = 16000  # Default 16GB
    
    @abstractmethod
    async def generate_video(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        duration: float = 5.0,
        fps: int = 24,
        width: int = 1280,
        height: int = 720,
        seed: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Generate a video and return the file path.
        
        Returns:
            Path to the generated video file
        """
        pass
    
    @abstractmethod
    async def img2video(
        self,
        image_path: str,
        prompt: str,
        duration: float = 5.0,
        **kwargs
    ) -> str:
        """Generate video from an image."""
        pass
    
    @abstractmethod
    async def video2video(
        self,
        video_path: str,
        prompt: str,
        strength: float = 0.75,
        **kwargs
    ) -> str:
        """Video-to-video transformation."""
        pass


class VoiceProvider(BaseProvider):
    """Interface for Text-to-Speech providers."""
    
    provider_name: str = "voice"
    
    @abstractmethod
    async def generate_speech(
        self,
        text: str,
        voice_id: str = "default",
        language: str = "en",
        speed: float = 1.0,
        pitch: float = 1.0,
        **kwargs
    ) -> str:
        """
        Generate speech audio and return the file path.
        
        Returns:
            Path to the generated audio file
        """
        pass
    
    @abstractmethod
    async def clone_voice(
        self,
        sample_audio_path: str,
        text: str,
        **kwargs
    ) -> str:
        """Clone a voice from a sample and generate speech."""
        pass


class MusicProvider(BaseProvider):
    """Interface for Music Generation providers."""
    
    provider_name: str = "music"
    requires_gpu: bool = True
    gpu_memory_mb: int = 8000  # Default 8GB
    
    @abstractmethod
    async def generate_music(
        self,
        prompt: str,
        duration: float = 30.0,
        genre: Optional[str] = None,
        tempo: Optional[float] = None,
        **kwargs
    ) -> str:
        """
        Generate music and return the file path.
        
        Returns:
            Path to the generated audio file
        """
        pass
    
    @abstractmethod
    async def generate_sound_effect(
        self,
        prompt: str,
        duration: float = 5.0,
        **kwargs
    ) -> str:
        """Generate a sound effect."""
        pass


class EmbeddingProvider(BaseProvider):
    """Interface for Embedding providers."""
    
    provider_name: str = "embedding"
    
    @abstractmethod
    async def generate_embedding(
        self,
        text: str,
        model_name: str = "default"
    ) -> List[float]:
        """Generate embedding vector for text."""
        pass
    
    @abstractmethod
    async def generate_batch_embeddings(
        self,
        texts: List[str],
        model_name: str = "default"
    ) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        pass


# Provider Registry
class ProviderRegistry:
    """Central registry for all available providers."""
    
    _providers: Dict[str, BaseProvider] = {}
    
    @classmethod
    def register(cls, provider: BaseProvider) -> None:
        """Register a provider instance."""
        cls._providers[provider.provider_name] = provider
    
    @classmethod
    def get_provider(cls, provider_type: str) -> Optional[BaseProvider]:
        """Get a provider by type."""
        return cls._providers.get(provider_type)
    
    @classmethod
    def list_providers(cls) -> List[str]:
        """List all registered provider types."""
        return list(cls._providers.keys())
    
    @classmethod
    def unregister(cls, provider_type: str) -> bool:
        """Unregister a provider."""
        if provider_type in cls._providers:
            del cls._providers[provider_type]
            return True
        return False
