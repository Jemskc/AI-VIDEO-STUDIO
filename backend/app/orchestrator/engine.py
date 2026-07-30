"""
AI Orchestrator - Central coordinator for AI execution.

The orchestrator receives production blueprints, splits them into tasks,
manages dependencies, schedules workers, and tracks overall progress.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
import uuid

from app.models.render_job import RenderJobStatus
from app.database.session import get_db

logger = logging.getLogger(__name__)


class TaskType(Enum):
    """Types of AI tasks."""
    GENERATE_STORY = "generate_story"
    GENERATE_CHARACTER = "generate_character"
    GENERATE_IMAGE = "generate_image"
    GENERATE_VIDEO = "generate_video"
    GENERATE_VOICE = "generate_voice"
    GENERATE_MUSIC = "generate_music"
    GENERATE_SUBTITLES = "generate_subtitles"
    UPSCALE = "upscale"
    RENDER = "render"
    VALIDATE = "validate"


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


@dataclass
class Task:
    """Represents a single executable task."""
    task_id: str
    task_type: TaskType
    project_id: str
    scene_id: Optional[str] = None
    character_id: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    priority: int = 0  # Higher = more urgent
    dependencies: Set[str] = field(default_factory=set)
    retry_count: int = 0
    max_retries: int = 3
    assigned_worker: Optional[str] = None
    gpu_required: bool = False
    gpu_memory_mb: int = 0
    payload: Dict[str, Any] = field(default_factory=dict)
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "task_type": self.task_type.value,
            "project_id": self.project_id,
            "scene_id": self.scene_id,
            "character_id": self.character_id,
            "status": self.status.value,
            "priority": self.priority,
            "dependencies": list(self.dependencies),
            "retry_count": self.retry_count,
            "assigned_worker": self.assigned_worker,
            "gpu_required": self.gpu_required,
            "gpu_memory_mb": self.gpu_memory_mb,
            "payload": self.payload,
            "result": self.result,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "progress": self.progress
        }


@dataclass
class ExecutionPlan:
    """Complete execution plan for a movie project."""
    plan_id: str
    project_id: str
    blueprint_id: str
    tasks: List[Task] = field(default_factory=list)
    status: str = "pending"
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    
    @property
    def progress(self) -> float:
        if self.total_tasks == 0:
            return 0.0
        return self.completed_tasks / self.total_tasks
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "project_id": self.project_id,
            "blueprint_id": self.blueprint_id,
            "status": self.status,
            "total_tasks": self.total_tasks,
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "progress": self.progress,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "tasks": [task.to_dict() for task in self.tasks]
        }


class Orchestrator:
    """
    Central AI Orchestrator.
    
    Responsibilities:
    - Receive production blueprints
    - Split into executable tasks
    - Resolve dependencies
    - Schedule tasks to workers
    - Track progress
    - Handle retries and failures
    - Generate execution reports
    """
    
    def __init__(self):
        self._execution_plans: Dict[str, ExecutionPlan] = {}
        self._tasks: Dict[str, Task] = {}
        self._pending_tasks: Set[str] = set()
        self._running_tasks: Set[str] = set()
        self._lock = asyncio.Lock()
        self._initialized = False
        self._shutdown_event = asyncio.Event()
    
    async def initialize(self) -> None:
        """Initialize the orchestrator."""
        logger.info("Initializing AI Orchestrator...")
        self._initialized = True
        logger.info("AI Orchestrator initialized")
    
    async def create_execution_plan(
        self,
        project_id: str,
        blueprint_id: str,
        blueprint_data: Dict[str, Any]
    ) -> ExecutionPlan:
        """
        Create an execution plan from a production blueprint.
        
        Args:
            project_id: Project identifier
            blueprint_id: Blueprint identifier
            blueprint_data: Complete blueprint data from Phase 3
            
        Returns:
            ExecutionPlan with all tasks created
        """
        plan_id = f"plan_{uuid.uuid4().hex[:12]}"
        plan = ExecutionPlan(
            plan_id=plan_id,
            project_id=project_id,
            blueprint_id=blueprint_id
        )
        
        # Generate tasks based on blueprint structure
        tasks = await self._generate_tasks_from_blueprint(plan_id, blueprint_data)
        plan.tasks = tasks
        plan.total_tasks = len(tasks)
        
        # Build dependency graph
        self._resolve_dependencies(plan)
        
        async with self._lock:
            self._execution_plans[plan_id] = plan
            for task in tasks:
                self._tasks[task.task_id] = task
                if task.status == TaskStatus.PENDING:
                    self._pending_tasks.add(task.task_id)
        
        logger.info(f"Created execution plan {plan_id} with {len(tasks)} tasks")
        return plan
    
    async def _generate_tasks_from_blueprint(
        self,
        plan_id: str,
        blueprint: Dict[str, Any]
    ) -> List[Task]:
        """Generate tasks from a movie blueprint."""
        tasks = []
        
        # 1. Story generation task (if needed)
        if "story" in blueprint:
            tasks.append(Task(
                task_id=f"task_{uuid.uuid4().hex[:12]}",
                task_type=TaskType.GENERATE_STORY,
                project_id=blueprint.get("project_id", ""),
                payload={"story": blueprint["story"]},
                priority=10
            ))
        
        # 2. Character image generation tasks
        characters = blueprint.get("characters", [])
        character_task_ids = []
        for char in characters:
            task = Task(
                task_id=f"task_{uuid.uuid4().hex[:12]}",
                task_type=TaskType.GENERATE_CHARACTER,
                project_id=blueprint.get("project_id", ""),
                character_id=char.get("id"),
                payload={
                    "character": char,
                    "prompt": char.get("image_prompt", "")
                },
                gpu_required=True,
                gpu_memory_mb=8000
            )
            tasks.append(task)
            character_task_ids.append(task.task_id)
        
        # 3. Scene generation tasks (images + videos)
        scenes = blueprint.get("scenes", [])
        scene_task_ids = []
        for scene in scenes:
            # Image generation for scene
            img_task = Task(
                task_id=f"task_{uuid.uuid4().hex[:12]}",
                task_type=TaskType.GENERATE_IMAGE,
                project_id=blueprint.get("project_id", ""),
                scene_id=scene.get("id"),
                payload={
                    "scene": scene,
                    "prompt": scene.get("image_prompt", "")
                },
                dependencies=set(character_task_ids),  # Depends on characters
                gpu_required=True,
                gpu_memory_mb=12000
            )
            tasks.append(img_task)
            
            # Video generation for scene
            video_task = Task(
                task_id=f"task_{uuid.uuid4().hex[:12]}",
                task_type=TaskType.GENERATE_VIDEO,
                project_id=blueprint.get("project_id", ""),
                scene_id=scene.get("id"),
                payload={
                    "scene": scene,
                    "prompt": scene.get("video_prompt", ""),
                    "image_dependency": img_task.task_id
                },
                dependencies={img_task.task_id},
                gpu_required=True,
                gpu_memory_mb=16000
            )
            tasks.append(video_task)
            scene_task_ids.append(video_task.task_id)
        
        # 4. Voice/Audio generation tasks
        dialogue = blueprint.get("dialogue", [])
        for line in dialogue:
            voice_task = Task(
                task_id=f"task_{uuid.uuid4().hex[:12]}",
                task_type=TaskType.GENERATE_VOICE,
                project_id=blueprint.get("project_id", ""),
                scene_id=line.get("scene_id"),
                payload={
                    "text": line.get("text", ""),
                    "voice_id": line.get("voice_id", "default")
                },
                dependencies=set(scene_task_ids),
                gpu_required=True,
                gpu_memory_mb=6000
            )
            tasks.append(voice_task)
        
        # 5. Music generation
        if "audio_plan" in blueprint:
            music_task = Task(
                task_id=f"task_{uuid.uuid4().hex[:12]}",
                task_type=TaskType.GENERATE_MUSIC,
                project_id=blueprint.get("project_id", ""),
                payload={"audio_plan": blueprint["audio_plan"]},
                dependencies=set(scene_task_ids),
                gpu_required=True,
                gpu_memory_mb=8000
            )
            tasks.append(music_task)
        
        # 6. Final render task
        render_task = Task(
            task_id=f"task_{uuid.uuid4().hex[:12]}",
            task_type=TaskType.RENDER,
            project_id=blueprint.get("project_id", ""),
            payload={"blueprint_id": blueprint.get("id")},
            dependencies=set(scene_task_ids),  # Depends on all scene videos
            priority=1
        )
        tasks.append(render_task)
        
        return tasks
    
    def _resolve_dependencies(self, plan: ExecutionPlan) -> None:
        """Resolve and validate task dependencies."""
        task_map = {t.task_id: t for t in plan.tasks}
        
        for task in plan.tasks:
            # Validate dependencies exist
            invalid_deps = task.dependencies - set(task_map.keys())
            if invalid_deps:
                logger.warning(f"Task {task.task_id} has invalid dependencies: {invalid_deps}")
                task.dependencies -= invalid_deps
        
        # Topological sort could be added here for optimal ordering
        logger.info(f"Resolved dependencies for plan {plan.plan_id}")
    
    async def get_next_ready_task(self, worker_type: str) -> Optional[Task]:
        """
        Get the next task ready for execution by a worker.
        
        Args:
            worker_type: Type of worker requesting a task
            
        Returns:
            Next ready task or None
        """
        async with self._lock:
            ready_tasks = []
            
            for task_id in self._pending_tasks:
                task = self._tasks.get(task_id)
                if not task:
                    continue
                
                # Check if task matches worker type
                if not self._task_matches_worker(task, worker_type):
                    continue
                
                # Check if all dependencies are completed
                if self._are_dependencies_met(task):
                    ready_tasks.append(task)
            
            if not ready_tasks:
                return None
            
            # Sort by priority (higher first), then by creation time
            ready_tasks.sort(key=lambda t: (-t.priority, t.created_at))
            return ready_tasks[0]
    
    def _task_matches_worker(self, task: Task, worker_type: str) -> bool:
        """Check if a task can be handled by a worker type."""
        type_mapping = {
            "llm": [TaskType.GENERATE_STORY],
            "image": [TaskType.GENERATE_IMAGE, TaskType.GENERATE_CHARACTER],
            "video": [TaskType.GENERATE_VIDEO],
            "voice": [TaskType.GENERATE_VOICE],
            "music": [TaskType.GENERATE_MUSIC],
            "render": [TaskType.RENDER],
            "validate": [TaskType.VALIDATE]
        }
        return task.task_type in type_mapping.get(worker_type, [])
    
    def _are_dependencies_met(self, task: Task) -> bool:
        """Check if all task dependencies are completed."""
        for dep_id in task.dependencies:
            dep_task = self._tasks.get(dep_id)
            if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                return False
        return True
    
    async def start_task(self, task_id: str, worker_id: str) -> bool:
        """Mark a task as started."""
        async with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return False
            
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.utcnow()
            task.assigned_worker = worker_id
            
            self._pending_tasks.discard(task_id)
            self._running_tasks.add(task_id)
            
            logger.info(f"Task {task_id} started by worker {worker_id}")
            return True
    
    async def complete_task(
        self,
        task_id: str,
        result: Dict[str, Any]
    ) -> bool:
        """Mark a task as completed."""
        async with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return False
            
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            task.result = result
            task.progress = 1.0
            
            self._running_tasks.discard(task_id)
            
            # Update plan progress
            plan = self._get_plan_for_task(task_id)
            if plan:
                plan.completed_tasks += 1
                if plan.completed_tasks == plan.total_tasks:
                    plan.status = "completed"
                    plan.completed_at = datetime.utcnow()
            
            logger.info(f"Task {task_id} completed successfully")
            return True
    
    async def fail_task(
        self,
        task_id: str,
        error_message: str,
        should_retry: bool = True
    ) -> bool:
        """Mark a task as failed."""
        async with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return False
            
            task.error_message = error_message
            self._running_tasks.discard(task_id)
            
            if should_retry and task.retry_count < task.max_retries:
                task.retry_count += 1
                task.status = TaskStatus.RETRYING
                task.assigned_worker = None
                self._pending_tasks.add(task_id)
                logger.warning(f"Task {task_id} failed, retrying ({task.retry_count}/{task.max_retries})")
            else:
                task.status = TaskStatus.FAILED
                logger.error(f"Task {task_id} failed permanently: {error_message}")
                
                # Update plan
                plan = self._get_plan_for_task(task_id)
                if plan:
                    plan.failed_tasks += 1
            
            return True
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a task."""
        async with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return False
            
            task.status = TaskStatus.CANCELLED
            self._pending_tasks.discard(task_id)
            self._running_tasks.discard(task_id)
            
            logger.info(f"Task {task_id} cancelled")
            return True
    
    def _get_plan_for_task(self, task_id: str) -> Optional[ExecutionPlan]:
        """Find the execution plan containing a task."""
        for plan in self._execution_plans.values():
            if any(t.task_id == task_id for t in plan.tasks):
                return plan
        return None
    
    async def get_execution_plan(self, plan_id: str) -> Optional[ExecutionPlan]:
        """Get an execution plan by ID."""
        return self._execution_plans.get(plan_id)
    
    async def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID."""
        return self._tasks.get(task_id)
    
    async def get_project_progress(self, project_id: str) -> Dict[str, Any]:
        """Get progress summary for a project."""
        plans = [
            p for p in self._execution_plans.values()
            if p.project_id == project_id
        ]
        
        if not plans:
            return {"status": "no_plans", "progress": 0.0}
        
        total_tasks = sum(p.total_tasks for p in plans)
        completed_tasks = sum(p.completed_tasks for p in plans)
        failed_tasks = sum(p.failed_tasks for p in plans)
        
        return {
            "status": "running" if any(p.status == "running" for p in plans) else "completed",
            "plans_count": len(plans),
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "progress": completed_tasks / total_tasks if total_tasks > 0 else 0.0
        }
    
    async def shutdown(self) -> None:
        """Shutdown the orchestrator gracefully."""
        logger.info("Shutting down AI Orchestrator...")
        self._shutdown_event.set()
        
        # Cancel all pending tasks
        async with self._lock:
            for task_id in list(self._pending_tasks):
                await self.cancel_task(task_id)
            
            # Wait for running tasks to complete (with timeout)
            # In production, implement proper timeout handling
        
        self._initialized = False
        logger.info("AI Orchestrator shutdown complete")


# Global singleton instance
_orchestrator: Optional[Orchestrator] = None


def get_orchestrator() -> Orchestrator:
    """Get the global orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator()
    return _orchestrator


async def initialize_orchestrator() -> Orchestrator:
    """Initialize and return the global orchestrator."""
    orchestrator = get_orchestrator()
    await orchestrator.initialize()
    return orchestrator
