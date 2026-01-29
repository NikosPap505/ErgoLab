"""
Performance Monitoring for ErgoLab
Provides metrics collection, query logging, and performance tracking
"""
import time
import logging
from typing import Callable, Optional
from functools import wraps
from contextlib import contextmanager
from datetime import datetime
from collections import defaultdict
import threading

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class PerformanceMetrics:
    """Thread-safe metrics collection for application performance"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._lock = threading.Lock()
        self._request_count = defaultdict(int)
        self._request_duration = defaultdict(list)
        self._error_count = defaultdict(int)
        self._slow_queries = []
        self._cache_hits = 0
        self._cache_misses = 0
        self._start_time = datetime.now()
        self._initialized = True
    
    def record_request(self, method: str, path: str, duration: float, status_code: int):
        """Record an API request"""
        key = f"{method}:{path}"
        with self._lock:
            self._request_count[key] += 1
            self._request_duration[key].append(duration)
            
            # Keep only last 1000 durations per endpoint
            if len(self._request_duration[key]) > 1000:
                self._request_duration[key] = self._request_duration[key][-1000:]
            
            if status_code >= 400:
                self._error_count[key] += 1
    
    def record_slow_query(self, query: str, duration: float):
        """Record a slow database query"""
        with self._lock:
            self._slow_queries.append({
                'query': query[:500],  # Truncate long queries
                'duration': duration,
                'timestamp': datetime.now().isoformat()
            })
            # Keep only last 100 slow queries
            if len(self._slow_queries) > 100:
                self._slow_queries = self._slow_queries[-100:]
    
    def record_cache_hit(self):
        """Record a cache hit"""
        with self._lock:
            self._cache_hits += 1
    
    def record_cache_miss(self):
        """Record a cache miss"""
        with self._lock:
            self._cache_misses += 1
    
    def get_stats(self) -> dict:
        """Get current performance statistics"""
        with self._lock:
            uptime = (datetime.now() - self._start_time).total_seconds()
            
            # Calculate per-endpoint stats
            endpoint_stats = {}
            for key, count in self._request_count.items():
                durations = self._request_duration.get(key, [])
                if durations:
                    endpoint_stats[key] = {
                        'count': count,
                        'avg_duration_ms': round(sum(durations) / len(durations) * 1000, 2),
                        'min_duration_ms': round(min(durations) * 1000, 2),
                        'max_duration_ms': round(max(durations) * 1000, 2),
                        'errors': self._error_count.get(key, 0)
                    }
            
            # Calculate cache hit rate
            total_cache_ops = self._cache_hits + self._cache_misses
            cache_hit_rate = (self._cache_hits / total_cache_ops * 100) if total_cache_ops > 0 else 0
            
            return {
                'uptime_seconds': round(uptime, 2),
                'total_requests': sum(self._request_count.values()),
                'total_errors': sum(self._error_count.values()),
                'cache_hit_rate': round(cache_hit_rate, 2),
                'cache_hits': self._cache_hits,
                'cache_misses': self._cache_misses,
                'slow_queries_count': len(self._slow_queries),
                'endpoints': endpoint_stats,
                'recent_slow_queries': self._slow_queries[-10:]
            }
    
    def reset(self):
        """Reset all metrics"""
        with self._lock:
            self._request_count.clear()
            self._request_duration.clear()
            self._error_count.clear()
            self._slow_queries.clear()
            self._cache_hits = 0
            self._cache_misses = 0
            self._start_time = datetime.now()


# Global metrics instance
metrics = PerformanceMetrics()


class MetricsMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for automatic request metrics collection"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        response = await call_next(request)
        
        duration = time.time() - start_time
        
        # Normalize path (remove IDs for grouping)
        path = request.url.path
        # Simple normalization: replace numeric segments with {id}
        import re
        path = re.sub(r'/\d+', '/{id}', path)
        
        metrics.record_request(
            method=request.method,
            path=path,
            duration=duration,
            status_code=response.status_code
        )
        
        # Log slow requests
        if duration > 1.0:
            logger.warning(
                f"Slow request: {request.method} {request.url.path} "
                f"took {duration:.3f}s"
            )
        
        # Add timing header
        response.headers['X-Response-Time'] = f"{duration:.3f}s"
        
        return response


@contextmanager
def track_query_time(query_description: str = "query"):
    """Context manager for tracking database query time"""
    start = time.time()
    try:
        yield
    finally:
        duration = time.time() - start
        if duration > 0.1:  # Log queries > 100ms
            logger.warning(f"Slow {query_description}: {duration:.3f}s")
            metrics.record_slow_query(query_description, duration)


def timed(name: Optional[str] = None):
    """Decorator to time function execution"""
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.time()
            try:
                return await func(*args, **kwargs)
            finally:
                duration = time.time() - start
                logger.debug(f"{name or func.__name__} took {duration:.3f}s")
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = time.time()
            try:
                return func(*args, **kwargs)
            finally:
                duration = time.time() - start
                logger.debug(f"{name or func.__name__} took {duration:.3f}s")
        
        if asyncio_iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    return decorator


def asyncio_iscoroutinefunction(func):
    """Check if function is a coroutine"""
    import asyncio
    return asyncio.iscoroutinefunction(func)


# SQLAlchemy query logging
def setup_query_logging(engine):
    """
    Set up SQLAlchemy event listeners for query performance logging
    
    Usage:
        from app.core.metrics import setup_query_logging
        setup_query_logging(engine)
    """
    from sqlalchemy import event
    
    @event.listens_for(engine, "before_cursor_execute")
    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        conn.info.setdefault('query_start_time', []).append(time.time())
    
    @event.listens_for(engine, "after_cursor_execute")
    def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        start_times = conn.info.get('query_start_time', [])
        if start_times:
            total = time.time() - start_times.pop(-1)
            if total > 0.1:  # Log queries > 100ms
                # Clean up statement for logging
                clean_statement = ' '.join(statement.split())[:200]
                logger.warning(f"Slow query ({total:.3f}s): {clean_statement}")
                metrics.record_slow_query(clean_statement, total)


# Health check data
def get_health_status() -> dict:
    """Get application health status for monitoring"""
    import os
    import psutil
    
    process = psutil.Process(os.getpid())
    
    return {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'system': {
            'cpu_percent': process.cpu_percent(),
            'memory_mb': round(process.memory_info().rss / 1024 / 1024, 2),
            'memory_percent': round(process.memory_percent(), 2),
            'threads': process.num_threads()
        },
        'performance': metrics.get_stats()
    }
