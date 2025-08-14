"""
🔄 Advanced Caching System for Streamlit Extension

Intelligent caching with TTL, invalidation, and performance optimization:
- Multi-level caching (memory + disk)
- TTL-based expiration
- Smart cache invalidation
- Database query caching
- Session-aware caching
"""

import sys
import os
import msgpack
import hashlib
import time
from pathlib import Path
from typing import Any, Optional, Dict, Callable, Union
from datetime import datetime, timedelta
from functools import wraps
from threading import Lock
import json
import logging

# Graceful imports
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False
    st = None


def get_config():
    """Safely retrieve extension configuration."""
    from ..config import get_config as _get_config
    return _get_config()


class CacheEntry:
    """Represents a single cache entry with metadata."""
    
    def __init__(self, value: Any, ttl_seconds: int = 300):
        self.value = value
        self.created_at = datetime.now()
        self.expires_at = self.created_at + timedelta(seconds=ttl_seconds)
        self.access_count = 0
        self.last_accessed = self.created_at
    
    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        return datetime.now() > self.expires_at
    
    def is_valid(self) -> bool:
        """Check if cache entry is valid (not expired)."""
        return not self.is_expired()
    
    def access(self) -> Any:
        """Access the cached value and update metadata."""
        self.access_count += 1
        self.last_accessed = datetime.now()
        return self.value
    
    def refresh(self, ttl_seconds: int = None):
        """Refresh the expiration time."""
        if ttl_seconds:
            self.expires_at = datetime.now() + timedelta(seconds=ttl_seconds)
        else:
            # Extend by original TTL
            original_ttl = (self.expires_at - self.created_at).seconds
            self.expires_at = datetime.now() + timedelta(seconds=original_ttl)


class AdvancedCache:
    """Advanced caching system with multiple levels and smart invalidation."""
    
    def __init__(self, default_ttl: int = 300, max_size: int = 1000, enable_disk_cache: bool = True, 
                 max_disk_cache_mb: int = 100):
        self.default_ttl = default_ttl
        self.max_size = max_size
        self.enable_disk_cache = enable_disk_cache
        self.max_disk_cache_mb = max_disk_cache_mb
        self.max_disk_cache_bytes = max_disk_cache_mb * 1024 * 1024  # Convert MB to bytes

        # Memory cache
        self._memory_cache: Dict[str, CacheEntry] = {}
        self._access_order = []  # For LRU eviction
        self._lock = Lock()

        # Mapping of hashed cache keys to their original representations
        # Used for pattern-based invalidation after enforcing hashed keys for security
        self._key_map: Dict[str, str] = {}
        
        # Disk cache directory
        if enable_disk_cache:
            self.cache_dir = Path.cwd() / ".streamlit_cache"
            self.cache_dir.mkdir(exist_ok=True)
        else:
            self.cache_dir = None
        
        # Cache statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "disk_hits": 0,
            "disk_writes": 0,
            "disk_evictions": 0
        }
        
        # Invalidation tracking
        self._invalidation_patterns = set()
        self._invalidation_callbacks = {}
    
    def _generate_key(self, key: Union[str, tuple, dict]) -> str:
        """Generate a consistent cache key from various input types."""
        # SECURITY FIX: Always hash keys to prevent path traversal attacks
        # Never return raw strings that could contain ../../../ or other path traversal sequences
        
        # Check for path traversal attempts and log security violations
        key_str = str(key)
        path_traversal_patterns = [
            '../', '..\\', '%2e%2e', '..%2f', '..%5c',  # Basic traversal
            '%252e%252e', '\u002e\u002e', '\\\\',       # Encoded variants
            '/etc/passwd', '\\windows\\system32'         # Common targets
        ]
        
        for pattern in path_traversal_patterns:
            if pattern.lower() in key_str.lower():
                # Log security violation
                security_logger = logging.getLogger('security.cache')
                security_logger.error(
                    f"SECURITY VIOLATION: Path traversal attempt detected in cache key: {key_str[:100]}..."
                )
                # Continue with hashing to prevent the attack but log it
                break
        
        # Always hash all inputs for consistent, safe cache keys
        if isinstance(key, str):
            # CRITICAL FIX: Always hash string keys - never return raw strings
            return hashlib.sha256(key.encode('utf-8')).hexdigest()
        elif isinstance(key, (tuple, list)):
            # Convert all elements to strings before sorting for consistent comparison
            try:
                str_elements = [str(item) for item in key]
                return hashlib.sha256(str(sorted(str_elements)).encode('utf-8')).hexdigest()
            except TypeError:
                # If sorting fails, just use the original order
                return hashlib.sha256(str(key).encode('utf-8')).hexdigest()
        elif isinstance(key, dict):
            sorted_items = sorted(key.items())
            return hashlib.sha256(str(sorted_items).encode('utf-8')).hexdigest()
        else:
            return hashlib.sha256(str(key).encode('utf-8')).hexdigest()
    
    def _validate_cache_key_for_filesystem(self, cache_key: str) -> bool:
        """
        Validate that cache key is safe for filesystem usage.
        
        Args:
            cache_key: The cache key to validate
            
        Returns:
            True if safe, False if potentially dangerous
        """
        # Cache keys should be SHA-256 hashes (64 hexadecimal characters)
        # This is additional validation since _generate_key now always hashes
        
        if not cache_key:
            return False
            
        # Should be exactly 64 characters (SHA-256 hex)
        if len(cache_key) != 64:
            return False
            
        # Should only contain hexadecimal characters (0-9, a-f)
        if not all(c in '0123456789abcdef' for c in cache_key.lower()):
            return False
            
        # Additional checks for dangerous patterns (defense in depth)
        dangerous_patterns = [
            '..', '/', '\\', ':', '*', '?', '"', '<', '>', '|',
            'CON', 'PRN', 'AUX', 'NUL',  # Windows reserved names
            'com1', 'com2', 'com3', 'com4', 'com5', 'com6', 'com7', 'com8', 'com9',
            'lpt1', 'lpt2', 'lpt3', 'lpt4', 'lpt5', 'lpt6', 'lpt7', 'lpt8', 'lpt9'
        ]
        
        cache_key_lower = cache_key.lower()
        for pattern in dangerous_patterns:
            if pattern.lower() in cache_key_lower:
                return False
                
        return True
    
    def get(self, key: Union[str, tuple, dict], default: Any = None) -> Any:
        """Get value from cache with fallback chain: memory -> disk -> default."""
        cache_key = self._generate_key(key)
        
        with self._lock:
            # Check memory cache first
            if cache_key in self._memory_cache:
                entry = self._memory_cache[cache_key]
                
                if entry.is_valid():
                    self.stats["hits"] += 1
                    # Update access order for LRU
                    if cache_key in self._access_order:
                        self._access_order.remove(cache_key)
                    self._access_order.append(cache_key)
                    
                    return entry.access()
                else:
                    # Entry expired, remove from memory
                    del self._memory_cache[cache_key]
                    if cache_key in self._access_order:
                        self._access_order.remove(cache_key)
            
            # Try disk cache if enabled
            if self.enable_disk_cache:
                disk_value = self._get_from_disk(cache_key)
                if disk_value is not None:
                    self.stats["disk_hits"] += 1
                    # Store in memory cache for faster access
                    self._memory_cache[cache_key] = CacheEntry(disk_value, self.default_ttl)
                    self._access_order.append(cache_key)
                    return disk_value
            
            # Cache miss
            self.stats["misses"] += 1
            return default
    
    def set(self, key: Union[str, tuple, dict], value: Any, ttl: int = None) -> None:
        """Set value in cache with optional TTL."""
        cache_key = self._generate_key(key)
        if ttl is None:
            ttl = self.default_ttl
        
        with self._lock:
            # Create cache entry
            entry = CacheEntry(value, ttl)
            
            # Check if we need to evict entries
            self._maybe_evict()
            
            # Store in memory cache
            self._memory_cache[cache_key] = entry
            self._key_map[cache_key] = str(key)
            
            # Update access order
            if cache_key in self._access_order:
                self._access_order.remove(cache_key)
            self._access_order.append(cache_key)
            
            # Store in disk cache if enabled
            if self.enable_disk_cache:
                self._set_to_disk(cache_key, value, ttl)
    
    def delete(self, key: Union[str, tuple, dict]) -> bool:
        """Delete key from cache."""
        if isinstance(key, str) and self._validate_cache_key_for_filesystem(key):
            cache_key = key
        else:
            cache_key = self._generate_key(key)
        
        with self._lock:
            deleted = False
            
            # Remove from memory cache and key mapping
            if cache_key in self._memory_cache:
                del self._memory_cache[cache_key]
                deleted = True
            if cache_key in self._key_map:
                del self._key_map[cache_key]
            
            # Remove from access order
            if cache_key in self._access_order:
                self._access_order.remove(cache_key)
            
            # Remove from disk cache
            if self.enable_disk_cache:
                disk_deleted = self._delete_from_disk(cache_key)
                deleted = deleted or disk_deleted
            
            return deleted
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._memory_cache.clear()
            self._access_order.clear()
            self._key_map.clear()
            
            if self.enable_disk_cache and self.cache_dir:
                # Clear disk cache
                for cache_file in self.cache_dir.glob("*.cache"):
                    try:
                        cache_file.unlink()
                    except OSError:
                        pass
    
    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all cache entries matching a pattern."""
        count = 0

        with self._lock:
            keys_to_remove = [
                original_key
                for original_key in self._key_map.values()
                if pattern in original_key
            ]

        for original_key in keys_to_remove:
            if self.delete(original_key):
                count += 1

        return count
    
    def cleanup_disk_cache_manual(self) -> Dict[str, int]:
        """Manually trigger disk cache cleanup and return statistics."""
        if not self.enable_disk_cache or not self.cache_dir:
            return {"files_removed": 0, "bytes_freed": 0, "error": "Disk cache not enabled"}
        
        initial_size = self._get_disk_cache_size()
        initial_evictions = self.stats["disk_evictions"]
        
        self._cleanup_disk_cache()
        
        final_size = self._get_disk_cache_size()
        final_evictions = self.stats["disk_evictions"]
        
        return {
            "files_removed": final_evictions - initial_evictions,
            "bytes_freed": initial_size - final_size,
            "size_before_mb": round(initial_size / (1024 * 1024), 2),
            "size_after_mb": round(final_size / (1024 * 1024), 2)
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            hit_rate = self.stats["hits"] / (self.stats["hits"] + self.stats["misses"]) if (self.stats["hits"] + self.stats["misses"]) > 0 else 0
            
            # Get disk cache stats
            disk_size_bytes = self._get_disk_cache_size()
            disk_size_mb = disk_size_bytes / (1024 * 1024)
            disk_usage_percent = (disk_size_bytes / self.max_disk_cache_bytes * 100) if self.max_disk_cache_bytes > 0 else 0
            
            disk_files_count = 0
            if self.cache_dir and self.cache_dir.exists():
                try:
                    disk_files_count = len(list(self.cache_dir.glob("*.cache")))
                except OSError:
                    pass
            
            return {
                **self.stats.copy(),
                "hit_rate": hit_rate,
                "memory_entries": len(self._memory_cache),
                "memory_size_kb": sys.getsizeof(self._memory_cache) // 1024,
                "disk_cache_enabled": self.enable_disk_cache,
                "disk_files_count": disk_files_count,
                "disk_size_mb": round(disk_size_mb, 2),
                "disk_usage_percent": round(disk_usage_percent, 1),
                "max_disk_cache_mb": self.max_disk_cache_mb,
                "max_size": self.max_size
            }
    
    def _maybe_evict(self) -> None:
        """Evict entries if cache is full (LRU eviction)."""
        while len(self._memory_cache) >= self.max_size:
            if not self._access_order:
                break
            
            # Remove least recently used entry
            lru_key = self._access_order.pop(0)
            if lru_key in self._memory_cache:
                del self._memory_cache[lru_key]
                
                # CRITICAL FIX: Also remove corresponding disk cache file
                if self.enable_disk_cache and self.cache_dir:
                    cache_file = self.cache_dir / f"{lru_key}.cache"
                    try:
                        if cache_file.exists():
                            cache_file.unlink()
                            self.stats["disk_evictions"] += 1
                    except OSError:
                        # File might have been deleted already, continue
                        pass
                
                self.stats["evictions"] += 1
    
    def _get_from_disk(self, cache_key: str) -> Optional[Any]:
        """Get value from disk cache."""
        if not self.cache_dir:
            return None
        
        # SECURITY VALIDATION: Ensure cache_key is safe for filesystem
        if not self._validate_cache_key_for_filesystem(cache_key):
            security_logger = logging.getLogger('security.cache')
            security_logger.error(f"SECURITY VIOLATION: Invalid cache key for filesystem: {cache_key}")
            return None
        
        cache_file = self.cache_dir / f"{cache_key}.cache"
        
        # Additional safety check: Ensure the resolved path is within cache directory
        try:
            resolved_cache_file = cache_file.resolve()
            resolved_cache_dir = self.cache_dir.resolve()
            
            if not str(resolved_cache_file).startswith(str(resolved_cache_dir)):
                security_logger = logging.getLogger('security.cache')
                security_logger.error(f"SECURITY VIOLATION: Path traversal detected in resolved path: {resolved_cache_file}")
                return None
        except (OSError, ValueError) as e:
            security_logger = logging.getLogger('security.cache')
            security_logger.error(f"SECURITY ERROR: Path resolution failed: {e}")
            return None
        
        try:
            if cache_file.exists():
                with open(cache_file, 'rb') as f:
                    cache_data = msgpack.unpackb(f.read(), raw=False)
                
                # Convert ISO format string back to datetime for expiration check
                expires_at_str = cache_data['expires_at']
                expires_at = datetime.fromisoformat(expires_at_str)
                
                # Check expiration
                if datetime.now() <= expires_at:
                    return cache_data['value']
                else:
                    # Expired, remove file
                    cache_file.unlink()
                    
        except (msgpack.exceptions.ExtraData, msgpack.exceptions.UnpackException, 
                KeyError, OSError, ValueError):
            # Corrupted cache file or invalid datetime format, remove it
            try:
                cache_file.unlink()
            except OSError:
                pass
        
        return None
    
    def _set_to_disk(self, cache_key: str, value: Any, ttl: int) -> None:
        """Set value to disk cache."""
        if not self.cache_dir:
            return
        
        # SECURITY VALIDATION: Ensure cache_key is safe for filesystem
        if not self._validate_cache_key_for_filesystem(cache_key):
            security_logger = logging.getLogger('security.cache')
            security_logger.error(f"SECURITY VIOLATION: Invalid cache key for filesystem: {cache_key}")
            return
        
        cache_file = self.cache_dir / f"{cache_key}.cache"
        
        # Additional safety check: Ensure the resolved path is within cache directory
        try:
            resolved_cache_file = cache_file.resolve()
            resolved_cache_dir = self.cache_dir.resolve()
            
            if not str(resolved_cache_file).startswith(str(resolved_cache_dir)):
                security_logger = logging.getLogger('security.cache')
                security_logger.error(f"SECURITY VIOLATION: Path traversal detected in resolved path: {resolved_cache_file}")
                return
        except (OSError, ValueError) as e:
            security_logger = logging.getLogger('security.cache') 
            security_logger.error(f"SECURITY ERROR: Path resolution failed: {e}")
            return
        
        try:
            # Convert datetime objects to ISO format strings for msgpack compatibility
            now = datetime.now()
            expires_at = now + timedelta(seconds=ttl)
            
            cache_data = {
                'value': value,
                'created_at': now.isoformat(),
                'expires_at': expires_at.isoformat()
            }
            
            with open(cache_file, 'wb') as f:
                f.write(msgpack.packb(cache_data, use_bin_type=True))
            
            self.stats["disk_writes"] += 1
            
            # Check if disk cache needs cleanup after writing
            self._cleanup_disk_cache()
            
        except (msgpack.exceptions.PackException, OSError):
            # Failed to write to disk, continue without disk cache
            pass
    
    def _delete_from_disk(self, cache_key: str) -> bool:
        """Delete value from disk cache."""
        if not self.cache_dir:
            return False
        
        # SECURITY VALIDATION: Ensure cache_key is safe for filesystem
        if not self._validate_cache_key_for_filesystem(cache_key):
            security_logger = logging.getLogger('security.cache')
            security_logger.error(f"SECURITY VIOLATION: Invalid cache key for filesystem: {cache_key}")
            return False
        
        cache_file = self.cache_dir / f"{cache_key}.cache"
        
        # Additional safety check: Ensure the resolved path is within cache directory
        try:
            resolved_cache_file = cache_file.resolve()
            resolved_cache_dir = self.cache_dir.resolve()
            
            if not str(resolved_cache_file).startswith(str(resolved_cache_dir)):
                security_logger = logging.getLogger('security.cache')
                security_logger.error(f"SECURITY VIOLATION: Path traversal detected in resolved path: {resolved_cache_file}")
                return False
        except (OSError, ValueError) as e:
            security_logger = logging.getLogger('security.cache')
            security_logger.error(f"SECURITY ERROR: Path resolution failed: {e}")
            return False
        
        try:
            if cache_file.exists():
                cache_file.unlink()
                return True
        except OSError:
            pass
        
        return False
    
    def _get_disk_cache_size(self) -> int:
        """Get total size of disk cache in bytes."""
        if not self.cache_dir or not self.cache_dir.exists():
            return 0
        
        total_size = 0
        try:
            for cache_file in self.cache_dir.glob("*.cache"):
                try:
                    total_size += cache_file.stat().st_size
                except OSError:
                    # File might have been deleted, skip it
                    continue
        except OSError:
            # Directory might not be accessible
            pass
        
        return total_size
    
    def _get_disk_cache_files_by_age(self) -> list:
        """Get disk cache files sorted by last access time (oldest first)."""
        if not self.cache_dir or not self.cache_dir.exists():
            return []
        
        files = []
        try:
            for cache_file in self.cache_dir.glob("*.cache"):
                try:
                    stat = cache_file.stat()
                    files.append((cache_file, stat.st_atime))
                except OSError:
                    continue
        except OSError:
            return []
        
        # Sort by access time (oldest first)
        files.sort(key=lambda x: x[1])
        return [f[0] for f in files]
    
    def _cleanup_disk_cache(self) -> None:
        """Clean up disk cache if it exceeds size limit."""
        if not self.enable_disk_cache or not self.cache_dir:
            return
        
        current_size = self._get_disk_cache_size()
        
        if current_size <= self.max_disk_cache_bytes:
            return
        
        # Remove oldest files until we're under the limit
        files_by_age = self._get_disk_cache_files_by_age()
        
        for cache_file in files_by_age:
            if current_size <= self.max_disk_cache_bytes * 0.8:  # Leave 20% buffer
                break
            
            try:
                file_size = cache_file.stat().st_size
                cache_file.unlink()
                current_size -= file_size
                self.stats["disk_evictions"] += 1
            except OSError:
                # File might have been deleted already
                continue
    
    def cleanup_orphaned_cache_files(self) -> int:
        """
        Remove orphaned cache files that don't have corresponding memory entries.
        
        Returns:
            int: Number of orphaned files removed
        """
        if not self.enable_disk_cache or not self.cache_dir:
            return 0
        
        removed_count = 0
        
        try:
            for cache_file in self.cache_dir.glob("*.cache"):
                # Extract key from filename
                cache_key = cache_file.stem
                
                # If key not in memory cache, it's orphaned
                if cache_key not in self._memory_cache:
                    try:
                        cache_file.unlink()
                        removed_count += 1
                        self.stats["disk_evictions"] += 1
                    except OSError:
                        # File might have been deleted already
                        continue
        
        except Exception as e:
            # If directory doesn't exist or other error, log and return 0
            import logging
            logging.getLogger(__name__).debug(f"Cache directory cleanup failed: {e}")
            # Return 0 as no files were removed due to the error
        
        return removed_count


# Global cache instance
_global_cache = None
_cache_lock = Lock()


def get_cache() -> AdvancedCache:
    """Get global cache instance (singleton)."""
    global _global_cache
    
    with _cache_lock:
        # Get configuration from config if available
        try:
            config = get_config()
            ttl = config.cache_ttl_seconds
            disk_cache_mb = getattr(config, 'max_disk_cache_mb', 100)
        except Exception:
            ttl = 300  # Default 5 minutes
            disk_cache_mb = 100  # Default 100 MB

        if _global_cache is None:
            _global_cache = AdvancedCache(
                default_ttl=ttl,
                max_size=1000,
                max_disk_cache_mb=disk_cache_mb
            )
        else:
            _global_cache.default_ttl = ttl
            _global_cache.max_disk_cache_mb = disk_cache_mb

    return _global_cache


def cached(ttl: int = None, key_func: Callable = None, invalidate_on: list = None):
    """
    Decorator for caching function results.
    
    Args:
        ttl: Time to live in seconds
        key_func: Function to generate cache key from args/kwargs
        invalidate_on: List of patterns that should invalidate this cache
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = get_cache()
            
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default key generation
                key_parts = [func.__name__, args, tuple(sorted(kwargs.items()))]
                cache_key = cache._generate_key(tuple(key_parts))
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl or cache.default_ttl)
            
            return result
        
        # Store metadata for cache management
        wrapper._cache_ttl = ttl
        wrapper._cache_key_func = key_func
        wrapper._cache_invalidate_on = invalidate_on or []
        
        return wrapper
    
    return decorator


def streamlit_cached(ttl: int = 300, key: str = None, show_spinner: bool = True):
    """
    Streamlit-optimized cache decorator that integrates with st.cache_data.
    """
    def decorator(func: Callable) -> Callable:
        if STREAMLIT_AVAILABLE:
            # Use Streamlit's native caching with our enhancements
            @st.cache_data(ttl=ttl, show_spinner=show_spinner)
            @wraps(func)
            def streamlit_wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            
            return streamlit_wrapper
        else:
            # Fallback to our custom caching
            return cached(ttl=ttl)(func)
    
    return decorator


def cache_database_query(query_name: str, ttl: int = 600):
    """
    Special decorator for database queries with intelligent invalidation.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = get_cache()
            
            # Create cache key with query name and parameters
            cache_key = f"db_query:{query_name}:{cache._generate_key((args, kwargs))}"
            
            # Check cache first
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute query and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            
            return result
        
        # Add method to invalidate this query's cache
        wrapper.invalidate_cache = lambda: get_cache().invalidate_pattern(f"db_query:{query_name}:")
        
        return wrapper
    
    return decorator


def invalidate_cache_on_change(*patterns: str):
    """
    Decorator to invalidate cache patterns when a function is called.
    Useful for functions that modify data.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Execute the function first
            result = func(*args, **kwargs)
            
            # Then invalidate related cache entries
            cache = get_cache()
            for pattern in patterns:
                cache.invalidate_pattern(pattern)
            
            return result
        
        return wrapper
    
    return decorator


# Session-aware caching for Streamlit
def get_session_cache() -> Dict[str, Any]:
    """Get session-specific cache storage."""
    if STREAMLIT_AVAILABLE and hasattr(st, 'session_state'):
        if '_streamlit_cache' not in st.session_state:
            st.session_state._streamlit_cache = {}
        return st.session_state._streamlit_cache
    else:
        # Fallback to global dictionary
        if not hasattr(get_session_cache, '_fallback_cache'):
            get_session_cache._fallback_cache = {}
        return get_session_cache._fallback_cache


def session_cached(key: str, ttl: int = 300):
    """Cache data in Streamlit session state with TTL."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            session_cache = get_session_cache()
            cache_key = f"{key}:{func.__name__}"
            
            # Check if cached and not expired
            if cache_key in session_cache:
                cached_entry = session_cache[cache_key]
                if isinstance(cached_entry, dict) and 'expires_at' in cached_entry:
                    if datetime.now() <= cached_entry['expires_at']:
                        return cached_entry['value']
                    else:
                        # Expired, remove from cache
                        del session_cache[cache_key]
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            session_cache[cache_key] = {
                'value': result,
                'created_at': datetime.now(),
                'expires_at': datetime.now() + timedelta(seconds=ttl)
            }
            
            return result
        
        return wrapper
    
    return decorator


# Cache warming utilities
def warm_cache():
    """Pre-load frequently used data into cache."""
    pass  # Implementation would depend on specific use cases


def get_cache_statistics() -> Dict[str, Any]:
    """Get comprehensive cache statistics."""
    cache = get_cache()
    stats = cache.get_stats()
    
    # Add session cache stats if available
    session_cache = get_session_cache()
    stats['session_cache_entries'] = len(session_cache)
    
    return stats


# Cache management utilities
def clear_all_caches():
    """Clear all caches (memory, disk, session)."""
    # Clear global cache
    cache = get_cache()
    cache.clear()
    
    # Clear session cache
    session_cache = get_session_cache()
    session_cache.clear()
    
    # Clear Streamlit cache if available
    if STREAMLIT_AVAILABLE:
        try:
            st.cache_data.clear()
        except AttributeError:
            pass


def cleanup_expired_cache():
    """Remove expired entries from all caches."""
    cache = get_cache()

    with cache._lock:
        expired_keys = [
            key
            for key, entry in cache._memory_cache.items()
            if entry.is_expired() or entry.expires_at <= entry.created_at
        ]

    for key in expired_keys:
        cache.delete(key)
    
    # Clean session cache
    session_cache = get_session_cache()
    expired_session_keys = []
    
    for key, value in session_cache.items():
        if isinstance(value, dict) and 'expires_at' in value:
            if datetime.now() > value['expires_at']:
                expired_session_keys.append(key)
    
    for key in expired_session_keys:
        del session_cache[key]
    
    # Also trigger disk cache cleanup
    cache._cleanup_disk_cache()


# Example usage and testing
if __name__ == "__main__":
    # Test the caching system
    cache = AdvancedCache(default_ttl=10, max_size=100)
    
    # Test basic operations
    cache.set("test_key", "test_value", 5)
    print(f"Cache get: {cache.get('test_key')}")
    
    # Test decorator
    @cached(ttl=10)
    def expensive_function(x, y):
        time.sleep(0.1)  # Simulate expensive operation
        return x + y
    
    # First call - should be slow
    start = time.time()
    result1 = expensive_function(1, 2)
    time1 = time.time() - start
    
    # Second call - should be fast (cached)
    start = time.time()
    result2 = expensive_function(1, 2)
    time2 = time.time() - start
    
    print(f"First call: {result1} in {time1:.3f}s")
    print(f"Second call: {result2} in {time2:.3f}s")
    print(f"Cache stats: {cache.get_stats()}")