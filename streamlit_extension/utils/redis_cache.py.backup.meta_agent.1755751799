"""
🚀 Redis Caching Layer - Enterprise Performance Enhancement

Advanced caching system designed to resolve performance bottlenecks identified in report.md:
- Heavy SQL queries without pagination
- Expensive joins beyond per-function decorators  
- Streamlit reruns on every interaction
- Large dataset operations causing UI lag

Features:
- Thread-safe Redis operations
- Graceful fallback when Redis unavailable
- Configurable TTL per operation type
- Cache invalidation strategies
- Performance metrics tracking
- Security-aware key generation
- Integration with existing DatabaseManager
"""

import sys
import json
import time
import hashlib
import logging
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable, Union, Tuple
from datetime import datetime, timedelta
from contextlib import contextmanager
from functools import wraps

# Add duration_system to path for security module
sys.path.append(str(Path(__file__).parent.parent.parent / "duration_system"))

try:
    import redis
    from redis.connection import ConnectionPool
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

try:
    from log_sanitization import create_secure_logger, sanitize_log_message
    LOG_SANITIZATION_AVAILABLE = True
except ImportError:
    LOG_SANITIZATION_AVAILABLE = False

    def create_secure_logger(name: str) -> logging.Logger:
        logger = logging.getLogger(name)
        if not logger.handlers:
            handler = logging.StreamHandler()
            logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger

    def sanitize_log_message(msg: str) -> str:
        return msg

try:
    from .security import sanitize_display
    SECURITY_AVAILABLE = True
except ImportError:
    SECURITY_AVAILABLE = False
    sanitize_display = lambda x, **kwargs: str(x)


class CacheStrategy:
    """Cache strategy definitions for different operation types."""
    
    # Query cache TTLs (in seconds)
    QUICK_QUERIES = 300      # 5 minutes - client/project lists
    MEDIUM_QUERIES = 900     # 15 minutes - epic/task data  
    HEAVY_QUERIES = 1800     # 30 minutes - analytics/aggregations
    STATIC_DATA = 3600       # 1 hour - settings/configs
    
    # Cache key prefixes
    PREFIX_CLIENT = "client"
    PREFIX_PROJECT = "project" 
    PREFIX_EPIC = "epic"
    PREFIX_TASK = "task"
    PREFIX_ANALYTICS = "analytics"
    PREFIX_AGGREGATION = "agg"
    PREFIX_SETTINGS = "settings"
    
    @classmethod
    def get_ttl(cls, operation_type: str) -> int:
        """Get TTL for operation type."""
        ttl_mapping = {
            "quick": cls.QUICK_QUERIES,
            "medium": cls.MEDIUM_QUERIES, 
            "heavy": cls.HEAVY_QUERIES,
            "static": cls.STATIC_DATA
        }
        return ttl_mapping.get(operation_type, cls.MEDIUM_QUERIES)


class CacheMetrics:
    """Cache performance metrics tracking."""
    
    def __init__(self):
        self.stats = {
            "hits": 0,
            "misses": 0,
            "errors": 0,
            "total_requests": 0,
            "avg_response_time": 0.0,
            "last_reset": time.time()
        }
        self._lock = threading.Lock()
    
    def record_hit(self, response_time: float):
        """Record cache hit."""
        with self._lock:
            self.stats["hits"] += 1
            self.stats["total_requests"] += 1
            self._update_avg_response_time(response_time)
    
    def record_miss(self, response_time: float):
        """Record cache miss."""
        with self._lock:
            self.stats["misses"] += 1
            self.stats["total_requests"] += 1
            self._update_avg_response_time(response_time)
    
    def record_error(self):
        """Record cache error."""
        with self._lock:
            self.stats["errors"] += 1
            self.stats["total_requests"] += 1
    
    def _update_avg_response_time(self, response_time: float):
        """Update average response time."""
        current_avg = self.stats["avg_response_time"]
        total_requests = self.stats["total_requests"]
        
        # Calculate new average using incremental formula
        self.stats["avg_response_time"] = (
            (current_avg * (total_requests - 1) + response_time) / total_requests
        )
    
    def get_hit_rate(self) -> float:
        """Calculate cache hit rate percentage."""
        total_cache_requests = self.stats["hits"] + self.stats["misses"]
        if total_cache_requests == 0:
            return 0.0
        return (self.stats["hits"] / total_cache_requests) * 100
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics."""
        with self._lock:
            stats = self.stats.copy()
            stats["hit_rate_percent"] = self.get_hit_rate()
            return stats
    
    def reset_stats(self):
        """Reset all statistics."""
        with self._lock:
            self.stats = {
                "hits": 0,
                "misses": 0,
                "errors": 0,
                "total_requests": 0,
                "avg_response_time": 0.0,
                "last_reset": time.time()
            }


class RedisCache:
    """Thin wrapper with key hashing, TTL and graceful fallback."""

    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0,
                 prefix: str = "tdd", ttl: int = 300) -> None:
        self.host = host
        self.port = port
        self.db = db
        self.prefix = prefix
        self.ttl = ttl
        self.logger = create_secure_logger(__name__)
        self.is_available = False
        self._client = None
        if REDIS_AVAILABLE:
            try:
                pool = ConnectionPool(host=host, port=port, db=db, socket_timeout=1.5)
                self._client = redis.Redis(connection_pool=pool)
                self._client.ping()
                self.is_available = True
                self.logger.info("Redis cache initialized on %s:%s", host, port)
            except Exception as e:
                self.logger.warning("Redis unavailable: %s", sanitize_log_message(str(e)))

    def _hkey(self, key: str) -> str:
        digest = hashlib.sha256(key.encode()).hexdigest()
        return f"{self.prefix}:{digest}"

    def get(self, key: str) -> Optional[str]:
        if not self.is_available:
            return None
        try:
            val = self._client.get(self._hkey(key))
            return val.decode() if isinstance(val, (bytes, bytearray)) else val
        except Exception as e:
            self.logger.warning("Redis get error: %s", sanitize_log_message(str(e)))
            return None

    def set(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        if not self.is_available:
            return False
        try:
            self._client.set(self._hkey(key), value, ex=ttl or self.ttl)
            return True
        except Exception as e:
            self.logger.warning("Redis set error: %s", sanitize_log_message(str(e)))
            return False


class RedisCacheManager:
    """Enterprise Redis caching manager with fallback support."""
    
    def __init__(self, 
                 host: str = "localhost",
                 port: int = 6379,
                 db: int = 0,
                 password: Optional[str] = None,
                 max_connections: int = 10,
                 socket_timeout: float = 5.0,
                 socket_connect_timeout: float = 5.0,
                 retry_on_timeout: bool = True,
                 health_check_interval: int = 30):
        """
        Initialize Redis cache manager.
        
        Args:
            host: Redis server host
            port: Redis server port
            db: Redis database number
            password: Redis password (if required)
            max_connections: Maximum connection pool size
            socket_timeout: Socket timeout in seconds
            socket_connect_timeout: Socket connect timeout in seconds
            retry_on_timeout: Whether to retry on timeout
            health_check_interval: Health check interval in seconds
        """
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.max_connections = max_connections
        self.socket_timeout = socket_timeout
        self.socket_connect_timeout = socket_connect_timeout
        self.retry_on_timeout = retry_on_timeout
        self.health_check_interval = health_check_interval
        
        # Initialize connection pool and client
        self.pool = None
        self.client = None
        self.is_available = False
        
        # Metrics and logging
        self.metrics = CacheMetrics()
        self._setup_logging()
        
        # Thread safety
        self._lock = threading.Lock()
        self._last_health_check = 0
        
        # Initialize connection
        self._initialize_connection()
    
    def _setup_logging(self):
        """Setup secure logging."""
        if LOG_SANITIZATION_AVAILABLE:
            self.logger = create_secure_logger('redis_cache')
        else:
            self.logger = logging.getLogger('redis_cache')
            self.logger.setLevel(logging.INFO)
            
            if not self.logger.handlers:
                handler = logging.StreamHandler()
                formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
                handler.setFormatter(formatter)
                self.logger.addHandler(handler)
    
    def _initialize_connection(self):
        """Initialize Redis connection with error handling."""
        if not REDIS_AVAILABLE:
            self.logger.warning("Redis library not available. Cache will use fallback mode.")
            return
        
        try:
            # Create connection pool
            self.pool = ConnectionPool(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                max_connections=self.max_connections,
                socket_timeout=self.socket_timeout,
                socket_connect_timeout=self.socket_connect_timeout,
                retry_on_timeout=self.retry_on_timeout
            )
            
            # Create Redis client
            self.client = redis.Redis(connection_pool=self.pool)
            
            # Test connection
            self.client.ping()
            self.is_available = True
            
            self.logger.info(f"Redis cache initialized successfully on {self.host}:{self.port}")
            
        except Exception as e:
            self.logger.warning(f"Redis connection failed: {e}. Using fallback mode.")
            self.is_available = False
            self.client = None
            self.pool = None
    
    def _check_health(self) -> bool:
        """Check Redis health with throttling."""
        current_time = time.time()
        
        # Throttle health checks
        if current_time - self._last_health_check < self.health_check_interval:
            return self.is_available
        
        self._last_health_check = current_time
        
        if not self.client:
            return False
        
        try:
            self.client.ping()
            if not self.is_available:
                self.logger.info("Redis connection restored")
                self.is_available = True
            return True
            
        except Exception as e:
            if self.is_available:
                self.logger.warning(f"Redis health check failed: {e}")
                self.is_available = False
            return False
    
    def _generate_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """
        Generate secure cache key with SHA-256 hashing.
        
        Args:
            prefix: Cache key prefix (e.g., 'client', 'project')
            *args: Positional arguments for key generation
            **kwargs: Keyword arguments for key generation
            
        Returns:
            Secure cache key string
        """
        # Create base key from arguments
        key_parts = [str(prefix)]
        
        # Add positional arguments
        for arg in args:
            if isinstance(arg, (str, int, float, bool)):
                key_parts.append(str(arg))
            elif arg is None:
                key_parts.append("none")
            else:
                # Hash complex objects
                key_parts.append(hashlib.sha256(str(arg).encode()).hexdigest()[:8])
        
        # Add keyword arguments (sorted for consistency)
        for key, value in sorted(kwargs.items()):
            if isinstance(value, (str, int, float, bool)):
                key_parts.append(f"{key}:{value}")
            elif value is None:
                key_parts.append(f"{key}:none")
            else:
                # Hash complex values
                value_hash = hashlib.sha256(str(value).encode()).hexdigest()[:8]
                key_parts.append(f"{key}:{value_hash}")
        
        # Create final key with separator
        base_key = ":".join(key_parts)
        
        # Hash the final key to ensure consistent length and security
        key_hash = hashlib.sha256(base_key.encode()).hexdigest()
        
        # Return prefixed hash (limited length for Redis efficiency)
        return f"tdd_cache:{prefix}:{key_hash[:16]}"
    
    def _serialize_data(self, data: Any) -> str:
        """Serialize data for Redis storage."""
        try:
            return json.dumps(data, default=str, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Serialization error: {e}")
            raise ValueError(f"Cannot serialize data: {e}")
    
    def _deserialize_data(self, data: str) -> Any:
        """Deserialize data from Redis."""
        try:
            return json.loads(data)
        except Exception as e:
            self.logger.error(f"Deserialization error: {e}")
            raise ValueError(f"Cannot deserialize data: {e}")
    
    @contextmanager
    def _measure_time(self):
        """Context manager to measure operation time."""
        start_time = time.time()
        try:
            yield
        finally:
            end_time = time.time()
            self.response_time = end_time - start_time
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/error
        """
        if not self._check_health():
            return None
        
        try:
            with self._measure_time():
                data = self.client.get(key)
                
            if data is None:
                self.metrics.record_miss(self.response_time)
                return None
            
            result = self._deserialize_data(data.decode('utf-8'))
            self.metrics.record_hit(self.response_time)
            
            self.logger.debug(f"Cache hit for key: {key[:20]}...")
            return result
            
        except Exception as e:
            self.metrics.record_error()
            self.logger.error(f"Cache get error for key {key[:20]}...: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = 900) -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            
        Returns:
            True if successful, False otherwise
        """
        if not self._check_health():
            return False
        
        try:
            serialized_data = self._serialize_data(value)
            
            with self._measure_time():
                result = self.client.setex(key, ttl, serialized_data)
            
            self.logger.debug(f"Cache set for key: {key[:20]}... (TTL: {ttl}s)")
            return bool(result)
            
        except Exception as e:
            self.metrics.record_error()
            self.logger.error(f"Cache set error for key {key[:20]}...: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete key from cache.
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if successful, False otherwise
        """
        if not self._check_health():
            return False
        
        try:
            with self._measure_time():
                result = self.client.delete(key)
            
            self.logger.debug(f"Cache delete for key: {key[:20]}...")
            return bool(result)
            
        except Exception as e:
            self.metrics.record_error()
            self.logger.error(f"Cache delete error for key {key[:20]}...: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """
        Delete keys matching pattern.
        
        Args:
            pattern: Key pattern (e.g., 'client:*')
            
        Returns:
            Number of keys deleted
        """
        if not self._check_health():
            return 0
        
        try:
            keys = self.client.keys(pattern)
            if not keys:
                return 0
            
            with self._measure_time():
                result = self.client.delete(*keys)
            
            self.logger.info(f"Deleted {result} keys matching pattern: {pattern}")
            return result
            
        except Exception as e:
            self.metrics.record_error()
            self.logger.error(f"Cache pattern delete error for {pattern}: {e}")
            return 0
    
    def flush_all(self) -> bool:
        """
        Flush all cache data.
        
        Returns:
            True if successful, False otherwise
        """
        if not self._check_health():
            return False
        
        try:
            with self._measure_time():
                result = self.client.flushdb()
            
            self.logger.warning("Cache flushed - all data cleared")
            return bool(result)
            
        except Exception as e:
            self.metrics.record_error()
            self.logger.error(f"Cache flush error: {e}")
            return False
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get cache information and statistics."""
        info = {
            "available": self.is_available,
            "host": self.host,
            "port": self.port,
            "db": self.db,
            "max_connections": self.max_connections,
            "metrics": self.metrics.get_stats()
        }
        
        if self.is_available and self.client:
            try:
                redis_info = self.client.info()
                info["redis_info"] = {
                    "version": redis_info.get("redis_version"),
                    "memory_used": redis_info.get("used_memory_human"),
                    "connected_clients": redis_info.get("connected_clients"),
                    "total_connections_received": redis_info.get("total_connections_received"),
                    "keyspace_hits": redis_info.get("keyspace_hits", 0),
                    "keyspace_misses": redis_info.get("keyspace_misses", 0)
                }
            except Exception as e:
                self.logger.error(f"Error getting Redis info: {e}")
        
        return info


# Global cache manager instance
_cache_manager = None
_cache_lock = threading.Lock()


def get_cache_manager(**kwargs) -> RedisCacheManager:
    """
    Get global cache manager instance (singleton pattern).
    
    Args:
        **kwargs: Configuration parameters for first initialization
        
    Returns:
        RedisCacheManager instance
    """
    global _cache_manager
    
    if _cache_manager is None:
        with _cache_lock:
            if _cache_manager is None:
                _cache_manager = RedisCacheManager(**kwargs)
    
    return _cache_manager


def cached(prefix: str, ttl: int = 900, operation_type: str = "medium"):
    """
    Decorator for caching function results.
    
    Args:
        prefix: Cache key prefix
        ttl: Time to live (default uses operation_type mapping)
        operation_type: Operation type for TTL mapping
        
    Usage:
        @cached("client", operation_type="quick")
        def get_client_data(client_id):
            return expensive_database_operation(client_id)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = get_cache_manager()
            
            # Generate cache key
            cache_key = cache._generate_cache_key(prefix, func.__name__, *args, **kwargs)
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Cache result
            actual_ttl = ttl if ttl != 900 else CacheStrategy.get_ttl(operation_type)
            cache.set(cache_key, result, actual_ttl)
            
            return result
        
        return wrapper
    return decorator


def invalidate_cache(prefix: str, *args, **kwargs):
    """
    Invalidate cache for specific key or pattern.
    
    Args:
        prefix: Cache key prefix
        *args: Arguments for key generation
        **kwargs: Keyword arguments for key generation
    """
    cache = get_cache_manager()
    
    if args or kwargs:
        # Invalidate specific key
        cache_key = cache._generate_cache_key(prefix, *args, **kwargs)
        cache.delete(cache_key)
    else:
        # Invalidate all keys with prefix
        pattern = f"tdd_cache:{prefix}:*"
        cache.delete_pattern(pattern)


def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics and information."""
    cache = get_cache_manager()
    return cache.get_cache_info()


def flush_cache() -> bool:
    """Flush all cache data."""
    cache = get_cache_manager()
    return cache.flush_all()


# Export main components
__all__ = [
    "RedisCacheManager",
    "CacheStrategy", 
    "CacheMetrics",
    "get_cache_manager",
    "cached",
    "invalidate_cache",
    "get_cache_stats",
    "flush_cache"
]