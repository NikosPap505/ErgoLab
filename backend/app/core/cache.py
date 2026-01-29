"""
Redis Cache Service for ErgoLab
Provides caching functionality with decorators for API optimization
"""
from redis import Redis
from typing import Optional, Any, Callable
from functools import wraps
import json
import os
import hashlib
import logging

logger = logging.getLogger(__name__)


class CacheService:
    """Redis-based caching service with automatic serialization"""
    
    def __init__(self):
        self._redis: Optional[Redis] = None
        self._connected = False
    
    @property
    def redis(self) -> Optional[Redis]:
        """Lazy connection to Redis"""
        if self._redis is None:
            try:
                self._redis = Redis(
                    host=os.getenv('REDIS_HOST', 'redis'),
                    port=int(os.getenv('REDIS_PORT', 6379)),
                    db=0,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5
                )
                # Test connection
                self._redis.ping()
                self._connected = True
                logger.info("✓ Redis cache connected")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}. Running without cache.")
                self._connected = False
        return self._redis if self._connected else None
    
    def _generate_key(self, key: str) -> str:
        """Generate a safe cache key with namespace"""
        return f"ergolab:{key}"
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached value by key"""
        if not self.redis:
            return None
        try:
            value = self.redis.get(self._generate_key(key))
            if value:
                logger.debug(f"✓ Cache hit: {key}")
                return json.loads(value)
            logger.debug(f"✗ Cache miss: {key}")
            return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    def set(self, key: str, value: Any, expire: int = 300) -> bool:
        """Set cached value with expiration (default 5 minutes)"""
        if not self.redis:
            return False
        try:
            serialized = json.dumps(value, default=str)
            self.redis.setex(
                self._generate_key(key),
                expire,
                serialized
            )
            logger.debug(f"✓ Cache set: {key} (expires in {expire}s)")
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete a cached value"""
        if not self.redis:
            return False
        try:
            self.redis.delete(self._generate_key(key))
            logger.debug(f"✓ Cache deleted: {key}")
            return True
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern"""
        if not self.redis:
            return 0
        try:
            full_pattern = self._generate_key(pattern)
            keys = self.redis.keys(full_pattern)
            if keys:
                count = self.redis.delete(*keys)
                logger.info(f"✓ Cache cleared {count} keys matching: {pattern}")
                return count
            return 0
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return 0
    
    def flush_all(self) -> bool:
        """Clear all ErgoLab cache entries"""
        if not self.redis:
            return False
        try:
            return bool(self.clear_pattern("*"))
        except Exception as e:
            logger.error(f"Cache flush error: {e}")
            return False
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        if not self.redis:
            return {"connected": False}
        try:
            info = self.redis.info("stats")
            keys = len(self.redis.keys(self._generate_key("*")))
            return {
                "connected": True,
                "total_keys": keys,
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "hit_rate": round(
                    info.get("keyspace_hits", 0) / 
                    max(info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0), 1) * 100,
                    2
                )
            }
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {"connected": False, "error": str(e)}


# Global cache instance
cache = CacheService()


def cached(expire: int = 300, key_prefix: str = ""):
    """
    Decorator for caching function results
    
    Usage:
        @cached(expire=600, key_prefix="materials")
        async def get_materials():
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Skip certain kwargs from cache key (like db sessions)
            skip_kwargs = {'db', 'current_user', 'session'}
            filtered_kwargs = {k: v for k, v in kwargs.items() if k not in skip_kwargs}
            
            # Generate unique cache key
            key_parts = [
                key_prefix or func.__module__,
                func.__name__,
                hashlib.md5(
                    f"{str(args)}:{str(sorted(filtered_kwargs.items()))}".encode()
                ).hexdigest()[:12]
            ]
            cache_key = ":".join(key_parts)
            
            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Cache miss - execute function
            result = await func(*args, **kwargs)
            
            # Store in cache (convert Pydantic models to dict if needed)
            if hasattr(result, 'model_dump'):
                cache_value = result.model_dump()
            elif isinstance(result, list) and result and hasattr(result[0], 'model_dump'):
                cache_value = [item.model_dump() for item in result]
            else:
                cache_value = result
            
            cache.set(cache_key, cache_value, expire)
            
            return result
        return wrapper
    return decorator


def invalidate_cache(*patterns: str):
    """
    Decorator to invalidate cache after function execution
    
    Usage:
        @invalidate_cache("materials:*", "inventory:*")
        async def create_material():
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            
            # Invalidate specified cache patterns
            for pattern in patterns:
                cache.clear_pattern(pattern)
            
            return result
        return wrapper
    return decorator


# Cache key generators for consistent naming
class CacheKeys:
    """Centralized cache key generators"""
    
    @staticmethod
    def materials_list(page: int = 1, category: str = None) -> str:
        return f"materials:list:{page}:{category or 'all'}"
    
    @staticmethod
    def materials_detail(material_id: int) -> str:
        return f"materials:detail:{material_id}"
    
    @staticmethod
    def inventory_warehouse(warehouse_id: int) -> str:
        return f"inventory:warehouse:{warehouse_id}"
    
    @staticmethod
    def inventory_low_stock() -> str:
        return "inventory:low-stock"
    
    @staticmethod
    def projects_list() -> str:
        return "projects:list"
    
    @staticmethod
    def project_detail(project_id: int) -> str:
        return f"projects:detail:{project_id}"
    
    @staticmethod
    def warehouses_list() -> str:
        return "warehouses:list"
    
    @staticmethod
    def warehouse_detail(warehouse_id: int) -> str:
        return f"warehouses:detail:{warehouse_id}"
    
    @staticmethod
    def dashboard_stats() -> str:
        return "dashboard:stats"
    
    @staticmethod
    def reports(report_type: str) -> str:
        return f"reports:{report_type}"
