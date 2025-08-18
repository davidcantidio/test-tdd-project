#!/usr/bin/env python3
"""
🚀 Performance Utilities - Optimization Tools for Large Datasets
Patch: stable cache keys, correct hit rate, safer git ops, better perf metrics

This module provides performance optimization utilities for TDD template scripts,
including caching, parallel processing, and efficient data handling.

Features:
- Intelligent caching with TTL
- Parallel processing for I/O operations  
- Memory-efficient data streaming
- Optimized Git operations
- Performance profiling and monitoring
"""

import hashlib
import json
import time
import functools
import threading
import multiprocessing
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable, Iterator, Tuple
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import subprocess
import sqlite3
import msgpack
from dataclasses import dataclass
import logging

# Import standardized error handling
from .error_handler import get_error_handler, handle_error, log_info, ErrorSeverity


@dataclass
class PerformanceMetrics:
    """Performance metrics for operations."""
    operation: str
    duration_seconds: float
    memory_mb: float
    items_processed: int
    cache_hit_rate: float = 0.0
    parallel_workers: int = 1


class LRUCache:
    """Thread-safe LRU cache with TTL support."""
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, Tuple[Any, float]] = {}
        self.access_order: List[str] = []
        self._lock = threading.RLock()
        self._requests = 0
        self._hits = 0
    
    def _is_expired(self, timestamp: float) -> bool:
        """Check if cache entry has expired."""
        return time.time() - timestamp > self.ttl_seconds
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        with self._lock:
            self._requests += 1
            if key in self.cache:
                value, timestamp = self.cache[key]

                if self._is_expired(timestamp):
                    # Remove expired entry
                    del self.cache[key]
                    if key in self.access_order:
                        self.access_order.remove(key)
                    return None

                # Update access order
                if key in self.access_order:
                    self.access_order.remove(key)
                self.access_order.append(key)
                self._hits += 1
                return value
            return None
    
    def set(self, key: str, value: Any) -> None:
        """Set value in cache."""
        with self._lock:
            current_time = time.time()
            
            # Remove oldest entries if at capacity
            while len(self.cache) >= self.max_size and self.access_order:
                oldest_key = self.access_order.pop(0)
                if oldest_key in self.cache:
                    del self.cache[oldest_key]
            
            # Add new entry
            self.cache[key] = (value, current_time)
            if key in self.access_order:
                self.access_order.remove(key)
            self.access_order.append(key)
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self.cache.clear()
            self.access_order.clear()
    
    def size(self) -> int:
        """Get current cache size."""
        return len(self.cache)
    
    def hit_rate(self, total_requests: int) -> float:
        """Calculate cache hit rate."""
        with self._lock:
            req = self._requests if total_requests == 0 else total_requests
            if req == 0:
                return 0.0
            return self._hits / req


class PersistentCache:
    """SQLite-based persistent cache for expensive operations."""
    
    def __init__(self, cache_file: Path = Path("performance_cache.db")):
        self.cache_file = cache_file
        self.cache_file.parent.mkdir(exist_ok=True)
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize cache database."""
        with sqlite3.connect(self.cache_file) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache_entries (
                    key TEXT PRIMARY KEY,
                    value BLOB,
                    timestamp REAL,
                    ttl_seconds INTEGER
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON cache_entries(timestamp)
            """)
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from persistent cache."""
        try:
            key_hash = hashlib.sha256(key.encode()).hexdigest()
            
            with sqlite3.connect(self.cache_file) as conn:
                cursor = conn.execute(
                    "SELECT value, timestamp, ttl_seconds FROM cache_entries WHERE key = ?",
                    (key_hash,)
                )
                result = cursor.fetchone()
                
                if not result:
                    return None
                
                value_blob, timestamp, ttl_seconds = result
                
                # Check if expired
                if time.time() - timestamp > ttl_seconds:
                    conn.execute("DELETE FROM cache_entries WHERE key = ?", (key_hash,))
                    return None
                
                return msgpack.unpackb(value_blob, raw=False)
                
        except Exception as e:
            handle_error(e, severity=ErrorSeverity.DEBUG)
            return None
    
    def set(self, key: str, value: Any, ttl_seconds: int = 3600) -> None:
        """Set value in persistent cache."""
        try:
            key_hash = hashlib.sha256(key.encode()).hexdigest()
            value_blob = msgpack.packb(value, use_bin_type=True)
            timestamp = time.time()
            
            with sqlite3.connect(self.cache_file) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO cache_entries (key, value, timestamp, ttl_seconds) VALUES (?, ?, ?, ?)",
                    (key_hash, value_blob, timestamp, ttl_seconds)
                )
                
        except Exception as e:
            handle_error(e, severity=ErrorSeverity.DEBUG)
    
    def cleanup_expired(self) -> int:
        """Remove expired entries and return count of removed entries."""
        try:
            current_time = time.time()
            with sqlite3.connect(self.cache_file) as conn:
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM cache_entries WHERE timestamp + ttl_seconds < ?",
                    (current_time,)
                )
                count = cursor.fetchone()[0]
                
                conn.execute(
                    "DELETE FROM cache_entries WHERE timestamp + ttl_seconds < ?",
                    (current_time,)
                )
                
                return count
                
        except Exception as e:
            handle_error(e, severity=ErrorSeverity.DEBUG)
            return 0


class OptimizedGitOperations:
    """Optimized Git operations for large repositories."""
    
    def __init__(self, cache: Optional[LRUCache] = None):
        self.cache = cache or LRUCache(max_size=10000, ttl_seconds=1800)  # 30 minutes
        self.batch_size = 1000
    
    def get_commits_batch(self, since_date: str = "2025-01-01", pattern: str = "\\[EPIC-") -> List[str]:
        """Get commits in batches with caching."""
        cache_key = f"commits_batch_{since_date}_{pattern}"
        
        # Try cache first
        cached_result = self.cache.get(cache_key)
        if cached_result is not None:
            return cached_result
        
        try:
            # Use more efficient git command
            cmd = [
                'git', 'log', '--oneline', '--no-merges',
                f'--grep={pattern}', f'--since={since_date}',
                '--pretty=format:%H|%ad|%s', '--date=iso'
            ]
            
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=True, timeout=60
            )
            
            commits = [line for line in result.stdout.split('\n') if line.strip()]
            
            # Cache result
            self.cache.set(cache_key, commits)
            
            log_info(f"Retrieved {len(commits)} commits", {"since": since_date, "pattern": pattern})
            
            return commits
            
        except subprocess.TimeoutExpired:
            handle_error(
                Exception(f"Git command timed out after 60 seconds"),
                user_action="Check repository size and network connection"
            )
            return []
        except subprocess.CalledProcessError as e:
            handle_error(
                e,
                user_action="Check Git repository status and permissions"
            )
            return []
    
    def get_commit_details_parallel(self, commit_hashes: List[str], max_workers: int = 4) -> Dict[str, Dict]:
        """Get commit details in parallel with optimized batch processing."""
        if not commit_hashes:
            return {}
        
        results = {}
        
        # Split into smaller chunks for parallel processing
        chunk_size = max(1, len(commit_hashes) // max_workers)
        chunks = [commit_hashes[i:i + chunk_size] for i in range(0, len(commit_hashes), chunk_size)]
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_chunk = {
                executor.submit(self._process_commit_chunk, chunk): chunk 
                for chunk in chunks
            }
            
            for future in as_completed(future_to_chunk):
                chunk_results = future.result()
                results.update(chunk_results)
        
        return results
    
    def _process_commit_chunk(self, commit_hashes: List[str]) -> Dict[str, Dict]:
        """Process a chunk of commits efficiently."""
        results = {}
        
        # Batch git commands for efficiency
        if not commit_hashes:
            return results
        
        try:
            # Use git show -s for exact commits to avoid traversal quirks
            cmd = ['git', 'show', '-s', '--pretty=format:%H|%ad|%s|%B---COMMIT-SEPARATOR---', '--date=iso'] + commit_hashes
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=30)
            
            commit_blocks = result.stdout.split('---COMMIT-SEPARATOR---')
            
            for block in commit_blocks:
                if not block.strip():
                    continue
                
                lines = block.strip().split('\n')
                if not lines:
                    continue
                
                # Parse first line: hash|date|subject
                header_parts = lines[0].split('|', 2)
                if len(header_parts) < 3:
                    continue
                
                commit_hash, date_str, subject = header_parts
                body = '\n'.join(lines[1:]) if len(lines) > 1 else ""
                
                results[commit_hash] = {
                    'hash': commit_hash,
                    'date': date_str,
                    'subject': subject,
                    'body': body
                }
                
        except Exception as e:
            handle_error(e, severity=ErrorSeverity.DEBUG)
        
        return results


class DataStreamProcessor:
    """Memory-efficient processing of large datasets."""
    
    @staticmethod
    def process_json_files_streaming(
        file_paths: List[Path], 
        processor_func: Callable[[Dict], Any],
        batch_size: int = 100
    ) -> Iterator[List[Any]]:
        """Process JSON files in streaming fashion to handle large datasets."""
        current_batch = []
        
        for file_path in file_paths:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    processed = processor_func(data)
                    current_batch.append(processed)
                
                # Yield batch when full
                if len(current_batch) >= batch_size:
                    yield current_batch
                    current_batch = []
                    
            except Exception as e:
                handle_error(
                    e, 
                    context={"file": str(file_path)},
                    severity=ErrorSeverity.WARNING
                )
                continue
        
        # Yield remaining items
        if current_batch:
            yield current_batch
    
    @staticmethod
    def parallel_file_processor(
        file_paths: List[Path],
        processor_func: Callable[[Path], Any],
        max_workers: int = None
    ) -> List[Any]:
        """Process files in parallel for better performance."""
        if not file_paths:
            return []
        
        max_workers = max_workers or min(len(file_paths), multiprocessing.cpu_count())
        results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_file = {
                executor.submit(processor_func, file_path): file_path 
                for file_path in file_paths
            }
            
            for future in as_completed(future_to_file):
                try:
                    result = future.result()
                    if result is not None:
                        results.append(result)
                except Exception as e:
                    file_path = future_to_file[future]
                    handle_error(
                        e,
                        context={"file": str(file_path)},
                        severity=ErrorSeverity.WARNING
                    )
        
        return results


class PerformanceMonitor:
    """Performance monitoring and profiling utilities."""
    
    def __init__(self):
        self.metrics: List[PerformanceMetrics] = []
        self.cache_requests = 0
        self.cache_hits = 0
    
    def time_operation(self, operation_name: str):
        """Decorator to time operations and collect metrics."""
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                start_memory = self._get_memory_usage()
                
                try:
                    result = func(*args, **kwargs)
                    
                    # Calculate metrics
                    duration = time.time() - start_time
                    end_memory = self._get_memory_usage()
                    memory_delta = max(0, end_memory - start_memory)
                    
                    # Determine items processed
                    items_processed = 1
                    # Prefer explicit 'count' in dicts
                    if isinstance(result, dict) and 'count' in result:
                        items_processed = result['count']
                    elif hasattr(result, '__len__'):
                        try:
                            items_processed = len(result)  # may fail for generators
                        except Exception:
                            items_processed = 1
                    
                    # Record metrics
                    metrics = PerformanceMetrics(
                        operation=operation_name,
                        duration_seconds=duration,
                        memory_mb=memory_delta,
                        items_processed=items_processed,
                        cache_hit_rate=self.get_cache_hit_rate()
                    )
                    self.metrics.append(metrics)
                    
                    log_info(
                        f"Performance: {operation_name}",
                        {
                            "duration_seconds": round(duration, 3),
                            "memory_mb": round(memory_delta, 2),
                            "items_processed": items_processed,
                            "rate_per_second": round(items_processed / max(duration, 0.001), 2)
                        }
                    )
                    
                    return result
                    
                except Exception as e:
                    # Still record metrics for failed operations
                    duration = time.time() - start_time
                    metrics = PerformanceMetrics(
                        operation=f"{operation_name}_FAILED",
                        duration_seconds=duration,
                        memory_mb=0,
                        items_processed=0
                    )
                    self.metrics.append(metrics)
                    raise
            
            return wrapper
        return decorator
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            return 0.0
    
    def record_cache_request(self, hit: bool = False) -> None:
        """Record cache request for hit rate calculation."""
        self.cache_requests += 1
        if hit:
            self.cache_hits += 1
    
    def get_cache_hit_rate(self) -> float:
        """Get current cache hit rate."""
        if self.cache_requests == 0:
            return 0.0
        return self.cache_hits / self.cache_requests
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        if not self.metrics:
            return {"message": "No performance metrics recorded"}
        
        # Aggregate metrics by operation
        operation_stats = {}
        for metric in self.metrics:
            if metric.operation not in operation_stats:
                operation_stats[metric.operation] = {
                    'count': 0,
                    'total_duration': 0.0,
                    'total_memory': 0.0,
                    'total_items': 0,
                    'min_duration': float('inf'),
                    'max_duration': 0.0
                }
            
            stats = operation_stats[metric.operation]
            stats['count'] += 1
            stats['total_duration'] += metric.duration_seconds
            stats['total_memory'] += metric.memory_mb
            stats['total_items'] += metric.items_processed
            stats['min_duration'] = min(stats['min_duration'], metric.duration_seconds)
            stats['max_duration'] = max(stats['max_duration'], metric.duration_seconds)
        
        # Calculate averages
        for operation, stats in operation_stats.items():
            count = stats['count']
            stats['avg_duration'] = stats['total_duration'] / count
            stats['avg_memory'] = stats['total_memory'] / count
            stats['avg_items_per_second'] = stats['total_items'] / max(stats['total_duration'], 0.001)
        
        return {
            "summary": {
                "total_operations": len(self.metrics),
                "cache_hit_rate": self.get_cache_hit_rate(),
                "total_duration": sum(m.duration_seconds for m in self.metrics),
                "total_memory_mb": sum(m.memory_mb for m in self.metrics)
            },
            "by_operation": operation_stats,
            "recent_operations": [
                {
                    "operation": m.operation,
                    "duration_seconds": m.duration_seconds,
                    "memory_mb": m.memory_mb,
                    "items_processed": m.items_processed
                }
                for m in self.metrics[-10:]  # Last 10 operations
            ]
        }
    
    def export_performance_data(self, output_file: Path) -> None:
        """Export performance data to JSON file."""
        report = self.get_performance_report()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        log_info(f"Performance report exported to {output_file}")


# Global instances
_performance_monitor = PerformanceMonitor()
_global_cache = LRUCache(max_size=5000, ttl_seconds=3600)
_persistent_cache = PersistentCache()


def get_performance_monitor() -> PerformanceMonitor:
    """Get global performance monitor instance."""
    return _performance_monitor


def get_global_cache() -> LRUCache:
    """Get global cache instance."""
    return _global_cache


def get_persistent_cache() -> PersistentCache:
    """Get persistent cache instance.""" 
    return _persistent_cache


def cached(ttl_seconds: int = 3600, use_persistent: bool = False):
    """Decorator for caching function results."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            try:
                # Stable, order-insensitive kwargs + best-effort repr for args
                key_payload = {
                    "fn": func.__name__,
                    "args": [repr(a) for a in args],
                    "kwargs": {k: repr(v) for k, v in sorted(kwargs.items())},
                }
                cache_key = hashlib.sha256(json.dumps(key_payload, sort_keys=True).encode("utf-8")).hexdigest()
            except Exception:
                # Fallback
                cache_key = f"{func.__name__}_{hashlib.sha256(repr((args, kwargs)).encode()).hexdigest()}"
            
            cache = _persistent_cache if use_persistent else _global_cache
            monitor = get_performance_monitor()
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                monitor.record_cache_request(hit=True)
                return cached_result
            
            # Execute function and cache result
            monitor.record_cache_request(hit=False)
            result = func(*args, **kwargs)
            
            # Cache the result
            if use_persistent:
                cache.set(cache_key, result, ttl_seconds)
            else:
                cache.set(cache_key, result)
            
            return result
        return wrapper
    return decorator


def performance_critical(operation_name: str):
    """Decorator to mark and monitor performance-critical operations."""
    def decorator(func):
        return get_performance_monitor().time_operation(operation_name)(func)
    return decorator
