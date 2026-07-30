"""
AI Infrastructure API Routes

Endpoints for managing the AI execution platform:
- GPU status
- Workers
- Tasks
- Orchestrator
- Cache
- Events
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from app.gpu.manager import get_gpu_manager, GPUManager
from app.orchestrator.engine import get_orchestrator, Orchestrator, TaskStatus
from app.workers.base import WorkerRegistry, create_worker
from app.cache.manager import get_cache_manager, CacheManager
from app.events.bus import get_event_bus, EventBus, EventType
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/ai", tags=["AI Infrastructure"])


# GPU Endpoints
@router.get("/gpu/status")
async def get_gpu_status(gpu_manager: GPUManager = Depends(get_gpu_manager)):
    """Get current GPU system status."""
    return await gpu_manager.get_system_status()


@router.get("/gpu/reservations")
async def get_gpu_reservations(gpu_manager: GPUManager = Depends(get_gpu_manager)):
    """Get all active GPU reservations."""
    reservations = await gpu_manager.list_reservations()
    return {
        "count": len(reservations),
        "reservations": [
            {
                "reservation_id": r.reservation_id,
                "gpu_id": r.gpu_id,
                "task_id": r.task_id,
                "model_name": r.model_name,
                "memory_mb": r.memory_mb,
                "created_at": r.created_at.isoformat()
            }
            for r in reservations
        ]
    }


# Worker Endpoints
@router.get("/workers")
async def list_workers():
    """List all registered workers."""
    return {
        "workers": WorkerRegistry.list_workers(),
        "count": len(WorkerRegistry._workers)
    }


@router.post("/workers/{worker_type}")
async def create_new_worker(worker_type: str):
    """Create a new worker of specified type."""
    worker = create_worker(worker_type)
    if not worker:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown worker type: {worker_type}"
        )
    
    WorkerRegistry.register(worker)
    return {
        "worker_id": worker.worker_id,
        "worker_type": worker.worker_type,
        "status": worker.status
    }


# Task Endpoints
@router.get("/tasks/{task_id}")
async def get_task(
    task_id: str,
    orchestrator: Orchestrator = Depends(get_orchestrator)
):
    """Get details of a specific task."""
    task = await orchestrator.get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )
    return task.to_dict()


@router.post("/tasks/{task_id}/cancel")
async def cancel_task(
    task_id: str,
    orchestrator: Orchestrator = Depends(get_orchestrator)
):
    """Cancel a running or pending task."""
    success = await orchestrator.cancel_task(task_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to cancel task {task_id}"
        )
    return {"status": "cancelled", "task_id": task_id}


# Execution Plan Endpoints
@router.get("/plans/{plan_id}")
async def get_execution_plan(
    plan_id: str,
    orchestrator: Orchestrator = Depends(get_orchestrator)
):
    """Get details of an execution plan."""
    plan = await orchestrator.get_execution_plan(plan_id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan {plan_id} not found"
        )
    return plan.to_dict()


@router.get("/projects/{project_id}/progress")
async def get_project_progress(
    project_id: str,
    orchestrator: Orchestrator = Depends(get_orchestrator)
):
    """Get progress summary for a project."""
    return await orchestrator.get_project_progress(project_id)


# Cache Endpoints
@router.get("/cache/stats")
async def get_cache_stats(cache_manager: CacheManager = Depends(get_cache_manager)):
    """Get cache statistics."""
    return await cache_manager.get_stats()


@router.get("/cache/keys")
async def list_cache_keys(
    namespace: Optional[str] = None,
    cache_manager: CacheManager = Depends(get_cache_manager)
):
    """List cache keys, optionally filtered by namespace."""
    keys = await cache_manager.get_keys(namespace)
    return {"namespace": namespace, "keys": keys, "count": len(keys)}


@router.delete("/cache/{namespace}")
async def clear_cache_namespace(
    namespace: str,
    cache_manager: CacheManager = Depends(get_cache_manager)
):
    """Clear all keys in a cache namespace."""
    count = await cache_manager.clear_namespace(namespace)
    return {"deleted_count": count, "namespace": namespace}


@router.post("/cache/cleanup")
async def cleanup_expired_cache(
    cache_manager: CacheManager = Depends(get_cache_manager)
):
    """Clean up expired cache entries."""
    count = await cache_manager.cleanup_expired()
    return {"cleaned_count": count}


# Event Endpoints
@router.get("/events")
async def get_recent_events(
    event_type: Optional[str] = None,
    limit: int = 100,
    event_bus: EventBus = Depends(get_event_bus)
):
    """Get recent events from the event bus."""
    if event_type:
        try:
            et = EventType(event_type)
            events = await event_bus.get_history(et, limit)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid event type: {event_type}"
            )
    else:
        events = await event_bus.get_history(None, limit)
    
    return {
        "events": [e.to_dict() for e in events],
        "count": len(events)
    }


# System Health Endpoint
@router.get("/health")
async def get_system_health(
    gpu_manager: GPUManager = Depends(get_gpu_manager),
    cache_manager: CacheManager = Depends(get_cache_manager)
):
    """Get overall system health status."""
    gpu_status = await gpu_manager.get_system_status()
    cache_stats = await cache_manager.get_stats()
    
    # Determine overall health
    health_status = "healthy"
    issues = []
    
    if gpu_status.get("gpu_count", 0) == 0:
        issues.append("No GPUs detected")
        health_status = "degraded"
    
    if cache_stats.get("hit_rate_percent", 0) < 50:
        issues.append("Low cache hit rate")
    
    return {
        "status": health_status,
        "issues": issues,
        "components": {
            "gpu": gpu_status,
            "cache": cache_stats,
            "workers": {
                "total": len(WorkerRegistry._workers),
                "by_type": {}
            }
        }
    }
