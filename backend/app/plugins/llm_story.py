"""
Mock LLM Provider for story/dialogue text.

No real model call: MoviePlanningService already deterministically builds the
story structure (genre/mood/scenes/prompts) via rule-based analysis, so this
provider's job in the mock pipeline is just to pass that text through the
provider abstraction the same way a real LLM provider eventually would.
"""
import logging
from typing import Any, Dict, List, Optional, AsyncIterator
from datetime import datetime

from app.providers.base import (
    LLMProvider,
    GenerationRequest,
    GenerationResponse,
    ProgressUpdate,
)

logger = logging.getLogger(__name__)


class StoryLLMProvider(LLMProvider):
    provider_name: str = "llm"
    provider_version: str = "1.0.0-mock"
    supported_models: List[str] = ["mock-story"]
    requires_gpu: bool = False

    async def initialize(self, model_name: str = "mock-story", **kwargs) -> bool:
        logger.info(f"Initializing mock LLM provider with model: {model_name}")
        return True

    async def shutdown(self) -> None:
        pass

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        start_time = datetime.utcnow()
        text = await self.generate_text(request.prompt)
        return GenerationResponse(
            task_id=request.task_id,
            status="completed",
            metadata={"text": text},
            processing_time_seconds=(datetime.utcnow() - start_time).total_seconds(),
        )

    async def generate_stream(self, request: GenerationRequest) -> AsyncIterator[ProgressUpdate]:
        yield ProgressUpdate(
            task_id=request.task_id, progress=1.0, stage="completed", message="Story text ready"
        )

    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        **kwargs,
    ) -> str:
        return prompt

    async def generate_structured(
        self, prompt: str, output_schema: Dict[str, Any], **kwargs
    ) -> Dict[str, Any]:
        return {"prompt": prompt}

    async def get_model_info(self, model_name: str) -> Dict[str, Any]:
        return {"name": model_name, "type": "llm_mock", "requires_gpu": False}

    async def validate_request(self, request: GenerationRequest) -> tuple[bool, Optional[str]]:
        if not request.prompt:
            return False, "Prompt is required"
        return True, None
