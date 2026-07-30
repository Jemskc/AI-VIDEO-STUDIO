"""
Event Bus - Internal event system for loose coupling between components.

Provides publish/subscribe functionality for system-wide events.
"""

import asyncio
import logging
from typing import Dict, List, Callable, Any, Optional
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
import uuid
import json

logger = logging.getLogger(__name__)


class EventType(Enum):
    """System event types."""
    # Task Events
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_CANCELLED = "task_cancelled"
    TASK_PROGRESS = "task_progress"
    
    # Worker Events
    WORKER_ONLINE = "worker_online"
    WORKER_OFFLINE = "worker_offline"
    WORKER_BUSY = "worker_busy"
    WORKER_IDLE = "worker_idle"
    
    # Model Events
    MODEL_LOADED = "model_loaded"
    MODEL_UNLOADED = "model_unloaded"
    MODEL_ERROR = "model_error"
    
    # Render Events
    RENDER_STARTED = "render_started"
    RENDER_PROGRESS = "render_progress"
    RENDER_COMPLETED = "render_completed"
    RENDER_FAILED = "render_failed"
    
    # Project Events
    PROJECT_CREATED = "project_created"
    PROJECT_UPDATED = "project_updated"
    PROJECT_COMPLETED = "project_completed"
    
    # System Events
    SYSTEM_STARTUP = "system_startup"
    SYSTEM_SHUTDOWN = "system_shutdown"
    GPU_WARNING = "gpu_warning"
    STORAGE_WARNING = "storage_warning"


@dataclass
class Event:
    """Represents a system event."""
    event_id: str
    event_type: EventType
    payload: Dict[str, Any]
    timestamp: datetime
    source: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "payload": self.payload,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict())


class EventBus:
    """
    Central event bus for system-wide communication.
    
    Features:
    - Publish/subscribe pattern
    - Async event handling
    - Event filtering by type
    - Event history (configurable)
    """
    
    def __init__(self, max_history: int = 1000):
        self._subscribers: Dict[EventType, List[Callable]] = {}
        self._history: List[Event] = []
        self._max_history = max_history
        self._lock = asyncio.Lock()
    
    async def subscribe(
        self,
        event_type: EventType,
        callback: Callable[[Event], Any]
    ) -> None:
        """
        Subscribe to an event type.
        
        Args:
            event_type: Type of event to subscribe to
            callback: Async function to call when event occurs
        """
        async with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            self._subscribers[event_type].append(callback)
            logger.debug(f"Subscriber added for {event_type.value}")
    
    async def unsubscribe(
        self,
        event_type: EventType,
        callback: Callable[[Event], Any]
    ) -> bool:
        """Remove a subscription."""
        async with self._lock:
            if event_type in self._subscribers:
                try:
                    self._subscribers[event_type].remove(callback)
                    return True
                except ValueError:
                    return False
        return False
    
    async def publish(
        self,
        event_type: EventType,
        payload: Dict[str, Any],
        source: str = "system"
    ) -> Event:
        """
        Publish an event to all subscribers.
        
        Args:
            event_type: Type of event
            payload: Event data
            source: Component that published the event
            
        Returns:
            The published event
        """
        event = Event(
            event_id=f"evt_{uuid.uuid4().hex[:12]}",
            event_type=event_type,
            payload=payload,
            timestamp=datetime.utcnow(),
            source=source
        )
        
        # Add to history
        async with self._lock:
            self._history.append(event)
            if len(self._history) > self._max_history:
                self._history = self._history[-self._max_history:]
        
        # Notify subscribers
        await self._notify_subscribers(event)
        
        logger.debug(f"Event published: {event_type.value} ({event.event_id})")
        return event
    
    async def _notify_subscribers(self, event: Event) -> None:
        """Notify all subscribers of an event."""
        callbacks = self._subscribers.get(event.event_type, [])
        
        if not callbacks:
            return
        
        # Fire all callbacks concurrently
        tasks = []
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    tasks.append(callback(event))
                else:
                    tasks.append(asyncio.create_task(
                        asyncio.get_event_loop().run_in_executor(None, callback, event)
                    ))
            except Exception as e:
                logger.error(f"Error preparing callback: {e}")
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Callback {i} failed: {result}")
    
    async def get_history(
        self,
        event_type: Optional[EventType] = None,
        limit: int = 100
    ) -> List[Event]:
        """Get event history, optionally filtered by type."""
        async with self._lock:
            if event_type:
                filtered = [e for e in self._history if e.event_type == event_type]
                return filtered[-limit:]
            return self._history[-limit:]
    
    async def clear_history(self) -> None:
        """Clear event history."""
        async with self._lock:
            self._history.clear()
            logger.info("Event history cleared")


# Global singleton instance
_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Get the global event bus instance."""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


async def publish_event(
    event_type: EventType,
    payload: Dict[str, Any],
    source: str = "system"
) -> Event:
    """Convenience function to publish an event."""
    bus = get_event_bus()
    return await bus.publish(event_type, payload, source)
