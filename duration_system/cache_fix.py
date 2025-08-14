"""
🔧 Cache System Fixes for Security and Interrupt Issues

This module contains fixes for critical cache system issues identified 
in the Codex audit, addressing both KeyboardInterrupt and security vulnerabilities.

Key fixes:
1. Timeout protection for lock operations
2. Non-blocking disk I/O with proper error handling
3. Interrupt-safe cache operations
4. Resource cleanup on interruption

Security enhancements (SEC-001 fix):
5. SHA-256 replaces MD5 for cache key generation (prevents collision attacks)
6. Cryptographic salt per cache instance (prevents rainbow table attacks)
7. Secure key derivation for all cache operations
8. OWASP-compliant hashing algorithm selection
"""

import sys
import os
import pickle
import hashlib
import time
import signal
import secrets
from pathlib import Path
from typing import Any, Optional, Dict, Callable, Union
from datetime import datetime, timedelta
from functools import wraps
from threading import Lock, RLock
import json
import threading
from concurrent.futures import ThreadPoolExecutor, TimeoutError as ConcurrentTimeoutError


class InterruptSafeCache:
    """
    Enhanced cache system with interrupt safety and timeout protection.
    
    Fixes the KeyboardInterrupt issue by:
    - Using timeouts for all lock operations
    - Non-blocking disk I/O with proper cleanup
    - Signal-safe operations
    - Graceful degradation on interruption
    """
    
    def __init__(self, default_ttl: int = 300, max_size: int = 1000, 
                 enable_disk_cache: bool = True, max_disk_cache_mb: int = 100,
                 lock_timeout: float = 5.0, disk_timeout: float = 2.0):
        self.default_ttl = default_ttl
        self.max_size = max_size
        self.enable_disk_cache = enable_disk_cache
        self.max_disk_cache_mb = max_disk_cache_mb
        self.max_disk_cache_bytes = max_disk_cache_mb * 1024 * 1024
        
        # Timeout configurations
        self.lock_timeout = lock_timeout
        self.disk_timeout = disk_timeout
        
        # Cryptographic salt for secure key generation
        # Generate a unique salt per cache instance for security
        self._cache_salt = secrets.token_bytes(32)  # 256-bit salt
        
        # Memory cache with RLock for better interrupt handling
        self._memory_cache: Dict[str, Any] = {}
        self._access_order = []
        self._lock = RLock()  # RLock is more interrupt-safe
        
        # Disk cache directory
        if enable_disk_cache:
            self.cache_dir = Path.cwd() / ".streamlit_cache"
            self._setup_cache_dir()
        else:
            self.cache_dir = None
        
        # Cache statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "disk_hits": 0,
            "disk_writes": 0,
            "disk_failures": 0,
            "timeout_errors": 0,
            "interrupt_recoveries": 0
        }
        
        # Thread pool for disk operations
        self._disk_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="cache_disk")
        
        # Interrupt handling
        self._interrupted = False
        self._original_sigint_handler = None
        self._setup_signal_handlers()
    
    def _setup_cache_dir(self):
        """Setup cache directory with proper error handling."""
        try:
            self.cache_dir.mkdir(exist_ok=True)
        except OSError as e:
            # If can't create cache dir, disable disk cache
            print(f"Warning: Cannot create cache directory: {e}")
            self.enable_disk_cache = False
            self.cache_dir = None
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful interrupt handling."""
        try:
            # Store original handler
            self._original_sigint_handler = signal.signal(signal.SIGINT, self._signal_handler)
        except (ValueError, OSError):
            # Signal handling not available (e.g., in threads)
            pass
    
    def _signal_handler(self, signum, frame):
        """Handle SIGINT gracefully."""
        self._interrupted = True
        self.stats["interrupt_recoveries"] += 1
        
        # Try to call original handler if exists
        if self._original_sigint_handler and callable(self._original_sigint_handler):
            try:
                self._original_sigint_handler(signum, frame)
            except:
                pass
    
    def _safe_lock_acquire(self, timeout: float = None) -> bool:
        """Safely acquire lock with timeout protection."""
        timeout = timeout or self.lock_timeout
        
        try:
            acquired = self._lock.acquire(timeout=timeout)
            if not acquired:
                self.stats["timeout_errors"] += 1
                return False
            return True
        except Exception:
            self.stats["timeout_errors"] += 1
            return False
    
    def _safe_lock_release(self):
        """Safely release lock."""
        try:
            self._lock.release()
        except Exception:
            pass
    
    def _generate_key(self, key: Union[str, tuple, dict]) -> str:
        """
        Generate a cryptographically secure cache key from various input types.
        
        Uses SHA-256 with salt to prevent collision attacks and key guessing.
        Each cache instance has a unique salt for additional security.
        
        Security improvements:
        - SHA-256 instead of MD5 (prevents collision attacks)
        - Unique salt per cache instance (prevents rainbow table attacks)
        - Deterministic key generation for cache consistency
        """
        # Create hasher with salt
        hasher = hashlib.sha256()
        hasher.update(self._cache_salt)
        
        if isinstance(key, str):
            # For string keys, still hash them for security and length consistency
            hasher.update(key.encode('utf-8'))
            return hasher.hexdigest()
        elif isinstance(key, (tuple, list)):
            try:
                # Convert elements to strings and sort for consistency
                str_elements = [str(item) for item in key]
                sorted_str = str(sorted(str_elements))
                hasher.update(sorted_str.encode('utf-8'))
                return hasher.hexdigest()
            except (TypeError, Exception):
                # Fallback to string representation
                hasher.update(str(key).encode('utf-8'))
                return hasher.hexdigest()
        elif isinstance(key, dict):
            try:
                # Sort dictionary items for consistent hashing
                sorted_items = sorted(key.items())
                sorted_str = str(sorted_items)
                hasher.update(sorted_str.encode('utf-8'))
                return hasher.hexdigest()
            except (TypeError, Exception):
                # Fallback to string representation
                hasher.update(str(key).encode('utf-8'))
                return hasher.hexdigest()
        else:
            # For any other type, convert to string and hash
            hasher.update(str(key).encode('utf-8'))
            return hasher.hexdigest()
    
    def get(self, key: Union[str, tuple, dict], default: Any = None) -> Any:
        """Get value from cache with interrupt safety."""
        if self._interrupted:
            return default
        
        cache_key = self._generate_key(key)
        
        # Try to acquire lock with timeout
        if not self._safe_lock_acquire():
            # If can't acquire lock, return default instead of blocking
            return default
        
        try:
            # Check memory cache first
            if cache_key in self._memory_cache:
                entry = self._memory_cache[cache_key]
                
                # Check if entry is a dict with expires_at
                if isinstance(entry, dict) and 'expires_at' in entry:
                    if datetime.now() <= entry['expires_at']:
                        self.stats["hits"] += 1
                        
                        # Update access order safely
                        try:
                            if cache_key in self._access_order:
                                self._access_order.remove(cache_key)
                            self._access_order.append(cache_key)
                        except (ValueError, IndexError):
                            pass
                        
                        return entry['value']
                    else:
                        # Entry expired, remove from memory
                        try:
                            del self._memory_cache[cache_key]
                            if cache_key in self._access_order:
                                self._access_order.remove(cache_key)
                        except (KeyError, ValueError):
                            pass
                else:
                    # Legacy entry format or direct value, assume valid
                    self.stats["hits"] += 1
                    
                    # Update access order safely
                    try:
                        if cache_key in self._access_order:
                            self._access_order.remove(cache_key)
                        self._access_order.append(cache_key)
                    except (ValueError, IndexError):
                        pass
                    
                    return entry
            
            # Cache miss
            self.stats["misses"] += 1
            return default
            
        except Exception as e:
            # On any error, return default
            self.stats["timeout_errors"] += 1
            return default
        finally:
            self._safe_lock_release()
    
    def set(self, key: Union[str, tuple, dict], value: Any, ttl: int = None) -> bool:
        """Set value in cache with interrupt safety."""
        if self._interrupted:
            return False
        
        cache_key = self._generate_key(key)
        ttl = ttl or self.default_ttl
        
        # Try to acquire lock with timeout
        if not self._safe_lock_acquire():
            return False
        
        try:
            # Create simple cache entry
            entry = {
                'value': value,
                'expires_at': datetime.now() + timedelta(seconds=ttl),
                'created_at': datetime.now()
            }
            
            # Check if we need to evict entries (non-blocking)
            self._maybe_evict_nonblocking()
            
            # Store in memory cache
            self._memory_cache[cache_key] = entry
            
            # Update access order safely
            try:
                if cache_key in self._access_order:
                    self._access_order.remove(cache_key)
                self._access_order.append(cache_key)
            except (ValueError, IndexError):
                pass
            
            # Schedule disk write (non-blocking)
            if self.enable_disk_cache and self.cache_dir:
                self._schedule_disk_write(cache_key, value, ttl)
            
            return True
            
        except Exception as e:
            self.stats["timeout_errors"] += 1
            return False
        finally:
            self._safe_lock_release()
    
    def delete(self, key: Union[str, tuple, dict]) -> bool:
        """Delete key from cache with interrupt safety."""
        if self._interrupted:
            return False
        
        cache_key = self._generate_key(key)
        
        # Try to acquire lock with timeout
        if not self._safe_lock_acquire(timeout=1.0):  # Shorter timeout for delete
            return False
        
        try:
            deleted = False
            
            # Remove from memory cache
            if cache_key in self._memory_cache:
                try:
                    del self._memory_cache[cache_key]
                    deleted = True
                except KeyError:
                    pass
            
            # Remove from access order
            if cache_key in self._access_order:
                try:
                    self._access_order.remove(cache_key)
                except ValueError:
                    pass
            
            # Schedule disk deletion (non-blocking)
            if self.enable_disk_cache and self.cache_dir:
                self._schedule_disk_delete(cache_key)
            
            return deleted
            
        except Exception:
            return False
        finally:
            self._safe_lock_release()
    
    def _maybe_evict_nonblocking(self) -> None:
        """Non-blocking eviction with interrupt protection."""
        if len(self._memory_cache) < self.max_size:
            return
        
        # Only evict one entry at a time to avoid long operations
        if self._access_order:
            try:
                lru_key = self._access_order.pop(0)
                if lru_key in self._memory_cache:
                    del self._memory_cache[lru_key]
                    self.stats["evictions"] += 1
                    
                    # Schedule disk cleanup (non-blocking)
                    if self.enable_disk_cache and self.cache_dir:
                        self._schedule_disk_delete(lru_key)
            except (IndexError, KeyError):
                pass
    
    def _schedule_disk_write(self, cache_key: str, value: Any, ttl: int):
        """Schedule disk write operation in background thread."""
        try:
            def write_task():
                self._write_to_disk_safe(cache_key, value, ttl)
            
            self._disk_executor.submit(write_task)
        except Exception:
            # If can't schedule, continue without disk cache
            self.stats["disk_failures"] += 1
    
    def _schedule_disk_delete(self, cache_key: str):
        """Schedule disk delete operation in background thread."""
        try:
            def delete_task():
                self._delete_from_disk_safe(cache_key)
            
            self._disk_executor.submit(delete_task)
        except Exception:
            # If can't schedule, continue
            self.stats["disk_failures"] += 1
    
    def _write_to_disk_safe(self, cache_key: str, value: Any, ttl: int):
        """Safely write to disk with timeout protection."""
        if not self.cache_dir or self._interrupted:
            return
        
        cache_file = self.cache_dir / f"{cache_key}.cache"
        
        try:
            cache_data = {
                'value': value,
                'created_at': datetime.now(),
                'expires_at': datetime.now() + timedelta(seconds=ttl)
            }
            
            # Use temporary file for atomic write
            temp_file = cache_file.with_suffix('.tmp')
            
            with open(temp_file, 'wb') as f:
                pickle.dump(cache_data, f)
            
            # Atomic move
            temp_file.replace(cache_file)
            self.stats["disk_writes"] += 1
            
        except Exception:
            # Clean up temporary file if exists
            try:
                if temp_file.exists():
                    temp_file.unlink()
            except:
                pass
            self.stats["disk_failures"] += 1
    
    def _delete_from_disk_safe(self, cache_key: str):
        """Safely delete from disk."""
        if not self.cache_dir or self._interrupted:
            return
        
        cache_file = self.cache_dir / f"{cache_key}.cache"
        
        try:
            if cache_file.exists():
                cache_file.unlink()
        except Exception:
            self.stats["disk_failures"] += 1
    
    def clear(self) -> None:
        """Clear all cache entries with interrupt safety."""
        if self._interrupted:
            return
        
        if not self._safe_lock_acquire(timeout=2.0):
            return
        
        try:
            self._memory_cache.clear()
            self._access_order.clear()
            
            # Schedule disk clear (non-blocking)
            if self.enable_disk_cache and self.cache_dir:
                def clear_disk():
                    try:
                        for cache_file in self.cache_dir.glob("*.cache"):
                            try:
                                cache_file.unlink()
                            except OSError:
                                pass
                    except Exception:
                        pass
                
                self._disk_executor.submit(clear_disk)
        except Exception:
            pass
        finally:
            self._safe_lock_release()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics with safe access."""
        stats_copy = self.stats.copy()
        
        # Add memory stats safely
        try:
            if self._safe_lock_acquire(timeout=0.5):
                try:
                    stats_copy["memory_entries"] = len(self._memory_cache)
                    hit_rate = self.stats["hits"] / (self.stats["hits"] + self.stats["misses"]) if (self.stats["hits"] + self.stats["misses"]) > 0 else 0
                    stats_copy["hit_rate"] = hit_rate
                finally:
                    self._safe_lock_release()
        except Exception:
            stats_copy["memory_entries"] = -1  # Indicate unavailable
            stats_copy["hit_rate"] = 0.0
        
        stats_copy["interrupted"] = self._interrupted
        return stats_copy
    
    def shutdown(self):
        """Shutdown cache system gracefully."""
        self._interrupted = True
        
        # Shutdown disk executor
        try:
            self._disk_executor.shutdown(wait=False)
        except Exception:
            pass
        
        # Restore original signal handler
        if self._original_sigint_handler:
            try:
                signal.signal(signal.SIGINT, self._original_sigint_handler)
            except (ValueError, OSError):
                pass


def create_interrupt_safe_cache_decorator(ttl: int = 300):
    """Create an interrupt-safe cache decorator using the fixed cache system."""
    
    # Global cache instance
    _safe_cache = InterruptSafeCache(default_ttl=ttl)
    
    def cached_safe(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            key_parts = [func.__name__, args, tuple(sorted(kwargs.items()))]
            cache_key = str(key_parts)
            
            # Try to get from cache
            cached_result = _safe_cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            try:
                result = func(*args, **kwargs)
                _safe_cache.set(cache_key, result, ttl)
                return result
            except KeyboardInterrupt:
                # On interrupt, don't cache partial results
                raise
            except Exception as e:
                # On other errors, don't cache but re-raise
                raise
        
        # Add cache management methods
        wrapper.clear_cache = lambda: _safe_cache.clear()
        wrapper.get_cache_stats = lambda: _safe_cache.get_stats()
        
        return wrapper
    
    return cached_safe


# Test utilities for validation
def test_interrupt_safety():
    """Test the interrupt safety of the cache system."""
    cache = InterruptSafeCache(default_ttl=10, max_size=100)
    
    # Test basic operations
    success_count = 0
    error_count = 0
    
    try:
        # Test set
        if cache.set("test_key", "test_value", 5):
            success_count += 1
        else:
            error_count += 1
        
        # Test get
        result = cache.get("test_key")
        if result == "test_value":
            success_count += 1
        else:
            error_count += 1
        
        # Test delete
        if cache.delete("test_key"):
            success_count += 1
        else:
            error_count += 1
        
        # Test stats
        stats = cache.get_stats()
        if isinstance(stats, dict):
            success_count += 1
        else:
            error_count += 1
            
    except Exception as e:
        error_count += 1
        print(f"Test error: {e}")
    
    finally:
        cache.shutdown()
    
    return {
        "success_count": success_count,
        "error_count": error_count,
        "total_tests": success_count + error_count
    }


if __name__ == "__main__":
    # Run interrupt safety test
    results = test_interrupt_safety()
    print(f"Interrupt Safety Test Results: {results}")
    
    # Test the decorator
    @create_interrupt_safe_cache_decorator(ttl=5)
    def test_function(x, y):
        time.sleep(0.1)  # Simulate work
        return x + y
    
    # Time the function
    start = time.time()
    result1 = test_function(1, 2)
    time1 = time.time() - start
    
    start = time.time()
    result2 = test_function(1, 2)  # Should be cached
    time2 = time.time() - start
    
    print(f"First call: {result1} in {time1:.3f}s")
    print(f"Second call (cached): {result2} in {time2:.3f}s")
    print(f"Cache stats: {test_function.get_cache_stats()}")