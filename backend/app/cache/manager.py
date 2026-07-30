"""
Cache Manager - Caching layer for frequently accessed data.

Provides caching for blueprints, prompts, assets, and model metadata.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, TypeVar
from datetime import datetime, timedelta
from dataclasses import dataclass
import hashlib
import json

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class CacheEntry:
    """Represents a cached item."""
    key: str
    value: Any
    created_at: datetime
    expires_at: Optional[datetime]
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at
    
    def touch(self) -> None:
        self.access_count += 1
        self.last_accessed = datetime.utcnow()


class CacheManager:
    """
    Central cache manager for the AI Movie Studio.
    
    Features:
    - TTL-based expiration
    - LRU eviction
    - Namespace support
    - Statistics tracking
    """
    
    def __init__(
        self,
        max_size: int = 1000,
        default_ttl_seconds: int = 3600
    ):
        self._cache: Dict[str, CacheEntry] = {}
        self._max_size = max_size
        self._default_ttl = timedelta(seconds=default_ttl_seconds)
        self._lock = asyncio.Lock()
        self._hits = 0
        self._misses = 0
    
    def _make_key(self, namespace: str, key: str) -> str:
        """Create a namespaced cache key."""
        return f"{namespace}:{key}"
    
    async def get(
        self,
        key: str,
        namespace: str = "default",
        default: Optional[T] = None
    ) -> Optional[T]:
        """
        Get a value from cache.
        
        Args:
            key: Cache key
            namespace: Namespace for the key
            default: Default value if not found
            
        Returns:
            Cached value or default
        """
        full_key = self._make_key(namespace, key)
        
        async with self._lock:
            entry = self._cache.get(full_key)
            
            if entry is None:
                self._misses += 1
                logger.debug(f"Cache miss: {full_key}")
                return default
            
            if entry.is_expired():
                await self._delete(full_key)
                self._misses += 1
                logger.debug(f"Cache expired: {full_key}")
                return default
            
            entry.touch()
            self._hits += 1
            logger.debug(f"Cache hit: {full_key}")
            return entry.value
    
    async def set(
        self,
        key: str,
        value: Any,
        namespace: str = "default",
        ttl_seconds: Optional[int] = None
    ) -> None:
        """
        Set a value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            namespace: Namespace for the key
            ttl_seconds: Time-to-live in seconds (optional)
        """
        full_key = self._make_key(namespace, key)
        
        async with self._lock:
            # Evict if at capacity
            if len(self._cache) >= self._max_size:
                await self._evict_lru()
            
            expires_at = None
            if ttl_seconds is not None:
                expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)
            else:
                expires_at = datetime.utcnow() + self._default_ttl
            
            entry = CacheEntry(
                key=full_key,
                value=value,
                created_at=datetime.utcnow(),
                expires_at=expires_at
            )
            
            self._cache[full_key] = entry
            logger.debug(f"Cache set: {full_key}")
    
    async def delete(
        self,
        key: str,
        namespace: str = "default"
    ) -> bool:
        """Delete a key from cache."""
        full_key = self._make_key(namespace, key)
        
        async with self._lock:
            return await self._delete(full_key)
    
    async def _delete(self, full_key: str) -> bool:
        """Internal delete without lock."""
        if full_key in self._cache:
            del self._cache[full_key]
            logger.debug(f"Cache deleted: {full_key}")
            return True
        return False
    
    async def clear_namespace(self, namespace: str) -> int:
        """Clear all keys in a namespace. Returns count of deleted keys."""
        async with self._lock:
            prefix = f"{namespace}:"
            keys_to_delete = [k for k in self._cache.keys() if k.startswith(prefix)]
            
            for key in keys_to_delete:
                await self._delete(key)
            
            logger.info(f"Cleared {len(keys_to_delete)} keys from namespace {namespace}")
            return len(keys_to_delete)
    
    async def clear_all(self) -> None:
        """Clear all cached data."""
        async with self._lock:
            self._cache.clear()
            logger.info("Cache cleared completely")
    
    async def _evict_lru(self) -> None:
        """Evict the least recently used entry."""
        if not self._cache:
            return
        
        # Find entry with oldest last_accessed time
        lru_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k].last_accessed or self._cache[k].created_at
        )
        
        await self._delete(lru_key)
        logger.debug(f"Evicted LRU entry: {lru_key}")
    
    async def cleanup_expired(self) -> int:
        """Remove all expired entries. Returns count of cleaned entries."""
        async with self._lock:
            expired_keys = [
                k for k, v in self._cache.items()
                if v.is_expired()
            ]
            
            for key in expired_keys:
                await self._delete(key)
            
            if expired_keys:
                logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
            
            return len(expired_keys)
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        async with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0
            
            return {
                "size": len(self._cache),
                "max_size": self._max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate_percent": round(hit_rate, 2),
                "default_ttl_seconds": self._default_ttl.total_seconds(),
                "namespaces": list(set(
                    k.split(":")[0] for k in self._cache.keys()
                ))
            }
    
    async def get_keys(self, namespace: Optional[str] = None) -> List[str]:
        """List all cache keys, optionally filtered by namespace."""
        async with self._lock:
            if namespace:
                prefix = f"{namespace}:"
                return [k[len(prefix):] for k in self._cache.keys() if k.startswith(prefix)]
            return [k.split(":")[1] if ":" in k else k for k in self._cache.keys()]


# Specialized cache namespaces
class BlueprintCache:
    """Cache for movie production blueprints."""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
        self.namespace = "blueprints"
    
    async def get_blueprint(self, blueprint_id: str) -> Optional[Dict[str, Any]]:
        return await self.cache.get(blueprint_id, namespace=self.namespace)
    
    async def set_blueprint(
        self,
        blueprint_id: str,
        blueprint: Dict[str, Any],
        ttl_seconds: int = 7200  # 2 hours
    ) -> None:
        await self.cache.set(blueprint_id, blueprint, namespace=self.namespace, ttl_seconds=ttl_seconds)


class PromptCache:
    """Cache for generated prompts."""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
        self.namespace = "prompts"
    
    async def get_prompt(self, prompt_hash: str) -> Optional[str]:
        return await self.cache.get(prompt_hash, namespace=self.namespace)
    
    async def set_prompt(
        self,
        prompt: str,
        result: str,
        ttl_seconds: int = 86400  # 24 hours
    ) -> None:
        # Create hash of prompt for key
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:12]
        await self.cache.set(prompt_hash, result, namespace=self.namespace, ttl_seconds=ttl_seconds)


class ModelCache:
    """Cache for model metadata and status."""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
        self.namespace = "models"
    
    async def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        return await self.cache.get(model_name, namespace=self.namespace)
    
    async def set_model_info(
        self,
        model_name: str,
        info: Dict[str, Any],
        ttl_seconds: int = 300  # 5 minutes
    ) -> None:
        await self.cache.set(model_name, info, namespace=self.namespace, ttl_seconds=ttl_seconds)


# Global singleton instance
_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """Get the global cache manager instance."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


async def initialize_cache_manager(
    max_size: int = 1000,
    default_ttl_seconds: int = 3600
) -> CacheManager:
    """Initialize and return the global cache manager."""
    global _cache_manager
    _cache_manager = CacheManager(
        max_size=max_size,
        default_ttl_seconds=default_ttl_seconds
    )
    logger.info(f"Cache manager initialized (max_size={max_size}, default_ttl={default_ttl_seconds}s)")
    return _cache_manager
