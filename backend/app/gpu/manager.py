"""
GPU Manager - Handles GPU detection, VRAM monitoring, and device allocation.

This module provides infrastructure for managing NVIDIA GPUs,
preparing the system for multi-GPU support in the future.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import threading

logger = logging.getLogger(__name__)


class GPUStatus(Enum):
    """GPU status states."""
    AVAILABLE = "available"
    IN_USE = "in_use"
    RESERVED = "reserved"
    UNHEALTHY = "unhealthy"
    OFFLINE = "offline"


@dataclass
class GPUInfo:
    """Information about a single GPU."""
    gpu_id: int
    name: str
    total_memory_mb: int
    free_memory_mb: int
    used_memory_mb: int
    utilization_percent: float
    temperature_celsius: float
    status: GPUStatus = GPUStatus.AVAILABLE
    reserved_by: Optional[str] = None  # Task ID or model name
    reserved_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "gpu_id": self.gpu_id,
            "name": self.name,
            "total_memory_mb": self.total_memory_mb,
            "free_memory_mb": self.free_memory_mb,
            "used_memory_mb": self.used_memory_mb,
            "utilization_percent": self.utilization_percent,
            "temperature_celsius": self.temperature_celsius,
            "status": self.status.value,
            "reserved_by": self.reserved_by,
            "reserved_at": self.reserved_at.isoformat() if self.reserved_at else None
        }


@dataclass
class MemoryReservation:
    """Tracks a memory reservation on a GPU."""
    reservation_id: str
    gpu_id: int
    task_id: str
    model_name: str
    memory_mb: int
    created_at: datetime
    expires_at: Optional[datetime] = None


class GPUMonitor:
    """
    Monitors GPU health and resource usage.
    
    In production, this uses pynvml (NVIDIA Management Library).
    For now, it provides a mock implementation that will be replaced
    when running on actual GPU hardware.
    """
    
    def __init__(self):
        self._nvml_initialized = False
        self._mock_mode = True
        self._gpus: Dict[int, GPUInfo] = {}
        self._lock = threading.Lock()
        
    def initialize(self) -> bool:
        """
        Initialize NVML library for GPU monitoring.
        
        Returns:
            True if initialization successful, False if running in mock mode
        """
        try:
            import pynvml
            pynvml.nvmlInit()
            device_count = pynvml.nvmlDeviceGetCount()
            
            for i in range(device_count):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                name = pynvml.nvmlDeviceGetName(handle)
                if isinstance(name, bytes):
                    name = name.decode('utf-8')
                
                memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
                temperature = pynvml.nvmlDeviceGetTemperature(handle, 0)  # GPU temp
                
                self._gpus[i] = GPUInfo(
                    gpu_id=i,
                    name=name,
                    total_memory_mb=memory_info.total // (1024 * 1024),
                    free_memory_mb=memory_info.free // (1024 * 1024),
                    used_memory_mb=memory_info.used // (1024 * 1024),
                    utilization_percent=utilization.gpu,
                    temperature_celsius=temperature
                )
            
            self._nvml_initialized = True
            self._mock_mode = False
            logger.info(f"NVML initialized with {device_count} GPU(s)")
            return True
            
        except ImportError:
            logger.warning("pynvml not installed, running in mock mode")
            self._setup_mock_gpus()
            return False
        except Exception as e:
            logger.warning(f"NVML initialization failed: {e}, running in mock mode")
            self._setup_mock_gpus()
            return False
    
    def _setup_mock_gpus(self):
        """Set up mock GPU for development/testing."""
        self._gpus = {
            0: GPUInfo(
                gpu_id=0,
                name="NVIDIA A100-SXM4-40GB (Mock)",
                total_memory_mb=40960,
                free_memory_mb=38000,
                used_memory_mb=2960,
                utilization_percent=5.0,
                temperature_celsius=35.0
            )
        }
        logger.info("Mock GPU configured: NVIDIA A100-SXM4-40GB")
    
    def refresh(self) -> None:
        """Refresh GPU information from hardware."""
        if self._mock_mode:
            # Simulate slight changes in mock mode
            for gpu in self._gpus.values():
                gpu.free_memory_mb = gpu.total_memory_mb - gpu.used_memory_mb
            return
        
        try:
            import pynvml
            for gpu_id, gpu_info in self._gpus.items():
                handle = pynvml.nvmlDeviceGetHandleByIndex(gpu_id)
                memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
                temperature = pynvml.nvmlDeviceGetTemperature(handle, 0)
                
                with self._lock:
                    gpu_info.free_memory_mb = memory_info.free // (1024 * 1024)
                    gpu_info.used_memory_mb = memory_info.used // (1024 * 1024)
                    gpu_info.utilization_percent = utilization.gpu
                    gpu_info.temperature_celsius = temperature
        except Exception as e:
            logger.error(f"Failed to refresh GPU info: {e}")
    
    def get_all_gpus(self) -> List[GPUInfo]:
        """Get information about all GPUs."""
        self.refresh()
        return list(self._gpus.values())
    
    def get_gpu(self, gpu_id: int) -> Optional[GPUInfo]:
        """Get information about a specific GPU."""
        self.refresh()
        return self._gpus.get(gpu_id)
    
    def get_best_gpu(self, required_memory_mb: int) -> Optional[GPUInfo]:
        """
        Find the best available GPU for a task.
        
        Args:
            required_memory_mb: Minimum required VRAM in MB
            
        Returns:
            GPUInfo of the best available GPU, or None
        """
        self.refresh()
        available_gpus = [
            gpu for gpu in self._gpus.values()
            if gpu.status == GPUStatus.AVAILABLE
            and gpu.free_memory_mb >= required_memory_mb
        ]
        
        if not available_gpus:
            return None
        
        # Select GPU with most free memory
        return max(available_gpus, key=lambda g: g.free_memory_mb)
    
    def shutdown(self) -> None:
        """Shutdown NVML library."""
        if not self._mock_mode:
            try:
                import pynvml
                pynvml.nvmlShutdown()
                logger.info("NVML shutdown complete")
            except Exception as e:
                logger.error(f"Error shutting down NVML: {e}")


class GPUManager:
    """
    Central manager for GPU resource allocation and scheduling.
    
    Handles:
    - GPU detection and monitoring
    - Memory reservation and release
    - Model loading coordination
    - Multi-GPU scheduling (future)
    """
    
    def __init__(self):
        self.monitor = GPUMonitor()
        self._reservations: Dict[str, MemoryReservation] = {}
        self._lock = asyncio.Lock()
        self._initialized = False
    
    async def initialize(self) -> bool:
        """Initialize the GPU manager."""
        success = self.monitor.initialize()
        self._initialized = True
        logger.info(f"GPU Manager initialized (mock_mode={self.monitor._mock_mode})")
        return success
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get overall GPU system status."""
        gpus = self.monitor.get_all_gpus()
        total_memory = sum(g.total_memory_mb for g in gpus)
        free_memory = sum(g.free_memory_mb for g in gpus)
        used_memory = sum(g.used_memory_mb for g in gpus)
        
        return {
            "initialized": self._initialized,
            "mock_mode": self.monitor._mock_mode,
            "gpu_count": len(gpus),
            "total_memory_mb": total_memory,
            "free_memory_mb": free_memory,
            "used_memory_mb": used_memory,
            "memory_utilization_percent": (used_memory / total_memory * 100) if total_memory > 0 else 0,
            "active_reservations": len(self._reservations),
            "gpus": [gpu.to_dict() for gpu in gpus]
        }
    
    async def reserve_gpu(
        self,
        task_id: str,
        model_name: str,
        required_memory_mb: int,
        gpu_id: Optional[int] = None
    ) -> Optional[MemoryReservation]:
        """
        Reserve a GPU for a task.
        
        Args:
            task_id: Unique task identifier
            model_name: Name of the model to load
            required_memory_mb: Required VRAM in MB
            gpu_id: Specific GPU ID (optional, auto-select if None)
            
        Returns:
            MemoryReservation if successful, None otherwise
        """
        async with self._lock:
            if gpu_id is not None:
                gpu = self.monitor.get_gpu(gpu_id)
                if not gpu or gpu.free_memory_mb < required_memory_mb:
                    logger.warning(f"GPU {gpu_id} unavailable or insufficient memory")
                    return None
            else:
                gpu = self.monitor.get_best_gpu(required_memory_mb)
                if not gpu:
                    logger.warning(f"No GPU available with {required_memory_mb}MB free")
                    return None
            
            reservation = MemoryReservation(
                reservation_id=f"res_{task_id}_{gpu.gpu_id}",
                gpu_id=gpu.gpu_id,
                task_id=task_id,
                model_name=model_name,
                memory_mb=required_memory_mb,
                created_at=datetime.utcnow()
            )
            
            # Update GPU status
            gpu.status = GPUStatus.RESERVED
            gpu.reserved_by = task_id
            gpu.reserved_at = datetime.utcnow()
            gpu.free_memory_mb -= required_memory_mb
            
            self._reservations[reservation.reservation_id] = reservation
            logger.info(f"Reserved GPU {gpu.gpu_id} for task {task_id} ({model_name})")
            
            return reservation
    
    async def release_reservation(self, reservation_id: str) -> bool:
        """
        Release a GPU reservation.
        
        Args:
            reservation_id: Reservation ID to release
            
        Returns:
            True if released successfully, False otherwise
        """
        async with self._lock:
            if reservation_id not in self._reservations:
                logger.warning(f"Reservation {reservation_id} not found")
                return False
            
            reservation = self._reservations.pop(reservation_id)
            gpu = self.monitor.get_gpu(reservation.gpu_id)
            
            if gpu:
                gpu.status = GPUStatus.AVAILABLE
                gpu.reserved_by = None
                gpu.reserved_at = None
                gpu.free_memory_mb += reservation.memory_mb
                logger.info(f"Released GPU {reservation.gpu_id} reservation {reservation_id}")
            
            return True
    
    async def get_reservation(self, task_id: str) -> Optional[MemoryReservation]:
        """Get reservation by task ID."""
        for res in self._reservations.values():
            if res.task_id == task_id:
                return res
        return None
    
    async def list_reservations(self) -> List[MemoryReservation]:
        """List all active reservations."""
        return list(self._reservations.values())
    
    async def cleanup_expired_reservations(self) -> int:
        """Clean up expired reservations. Returns count of cleaned reservations."""
        now = datetime.utcnow()
        expired = [
            res_id for res_id, res in self._reservations.items()
            if res.expires_at and res.expires_at < now
        ]
        
        cleaned = 0
        for res_id in expired:
            if await self.release_reservation(res_id):
                cleaned += 1
        
        return cleaned
    
    async def shutdown(self) -> None:
        """Shutdown GPU manager and release all reservations."""
        logger.info("Shutting down GPU Manager...")
        
        # Release all reservations
        reservation_ids = list(self._reservations.keys())
        for res_id in reservation_ids:
            await self.release_reservation(res_id)
        
        self.monitor.shutdown()
        self._initialized = False
        logger.info("GPU Manager shutdown complete")


# Global singleton instance
_gpu_manager: Optional[GPUManager] = None


def get_gpu_manager() -> GPUManager:
    """Get the global GPU manager instance."""
    global _gpu_manager
    if _gpu_manager is None:
        _gpu_manager = GPUManager()
    return _gpu_manager


async def initialize_gpu_manager() -> GPUManager:
    """Initialize and return the global GPU manager."""
    manager = get_gpu_manager()
    await manager.initialize()
    return manager
