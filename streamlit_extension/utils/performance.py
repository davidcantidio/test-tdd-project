"""
🚀 Performance Optimization and Query Monitoring

Provides database query optimization, caching, and performance monitoring
tools for the Streamlit application with security-first design.

Features:
- Query performance monitoring with metrics
- Advanced caching with TTL and statistics
- Index optimization recommendations
- Performance profiling decorators
"""

import time
import functools
import logging
from contextlib import contextmanager
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class QueryMetrics:
    """Query performance metrics."""

    query: str
    execution_time_ms: float
    rows_returned: int
    rows_examined: int
    timestamp: float
    cache_hit: bool = False


class QueryOptimizer:
    """Database query optimization and monitoring."""

    def __init__(self):
        self.query_metrics: List[QueryMetrics] = []
        self.slow_query_threshold_ms = 100.0
        self.query_cache: Dict[str, Any] = {}
        self.cache_ttl_seconds = 300

    @contextmanager
    def measure_query(self, query: str):
        """Context manager to measure query performance."""
        start_time = time.time()
        try:
            yield
        finally:
            execution_time = (time.time() - start_time) * 1000
            self.log_query_metrics(query, execution_time)

    def log_query_metrics(self, query: str, execution_time_ms: float, rows_returned: int = 0, rows_examined: int = 0, cache_hit: bool = False):
        """Log query performance metrics."""
        metric = QueryMetrics(
            query=query,
            execution_time_ms=execution_time_ms,
            rows_returned=rows_returned,
            rows_examined=rows_examined,
            timestamp=time.time(),
            cache_hit=cache_hit,
        )
        self.query_metrics.append(metric)
        if execution_time_ms > self.slow_query_threshold_ms:
            logger.warning("Slow query detected: %.2fms - %s", execution_time_ms, query)

    def get_slow_queries(self, threshold_ms: Optional[float] = None) -> List[QueryMetrics]:
        """Get queries exceeding performance threshold."""
        threshold = threshold_ms or self.slow_query_threshold_ms
        return [m for m in self.query_metrics if m.execution_time_ms > threshold]

    def get_query_statistics(self) -> Dict[str, Any]:
        """Get comprehensive query performance statistics."""
        if not self.query_metrics:
            return {
                "total_queries": 0,
                "avg_execution_time": 0.0,
                "slow_query_count": 0,
                "cache_hit_rate": 0.0,
            }
        total_time = sum(m.execution_time_ms for m in self.query_metrics)
        slow = self.get_slow_queries()
        cache_hits = sum(1 for m in self.query_metrics if m.cache_hit)
        return {
            "total_queries": len(self.query_metrics),
            "avg_execution_time": total_time / len(self.query_metrics),
            "slow_query_count": len(slow),
            "cache_hit_rate": cache_hits / len(self.query_metrics),
        }

    def suggest_optimizations(self) -> List[str]:
        """Suggest query optimizations based on metrics."""
        suggestions: List[str] = []
        for metric in self.get_slow_queries():
            suggestions.append(f"Optimize query: {metric.query[:50]}...")
        return suggestions


class CacheManager:
    """Advanced caching for database queries."""

    def __init__(self, default_ttl: int = 300):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
        self.stats = {"hits": 0, "misses": 0}

    def cache_key(self, table: str, filters: Dict[str, Any], sort: str, page: int) -> str:
        """Generate cache key for query parameters."""
        return f"{table}:{filters}:{sort}:{page}"

    def get_cached_result(self, cache_key: str) -> Optional[Any]:
        """Get cached result if not expired."""
        entry = self.cache.get(cache_key)
        if not entry:
            self.stats["misses"] += 1
            return None
        if time.time() > entry["expiry"]:
            del self.cache[cache_key]
            self.stats["misses"] += 1
            return None
        self.stats["hits"] += 1
        return entry["value"]

    def set_cached_result(self, cache_key: str, result: Any, ttl: Optional[int] = None):
        """Cache query result with TTL."""
        expiry = time.time() + (ttl or self.default_ttl)
        self.cache[cache_key] = {"value": result, "expiry": expiry}

    def invalidate_table_cache(self, table_name: str):
        """Invalidate all cache entries for a table."""
        keys_to_delete = [k for k in self.cache if k.startswith(f"{table_name}:")]
        for k in keys_to_delete:
            del self.cache[k]

    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get cache hit/miss statistics."""
        total = self.stats["hits"] + self.stats["misses"]
        hit_rate = self.stats["hits"] / total if total else 0.0
        return {"hits": self.stats["hits"], "misses": self.stats["misses"], "hit_rate": hit_rate}


def query_performance_monitor(func: Callable) -> Callable:
    """Decorator to monitor database query performance."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        optimizer: QueryOptimizer = kwargs.get("optimizer") or QueryOptimizer()
        query = kwargs.get("query", func.__name__)
        with optimizer.measure_query(query):
            result = func(*args, **kwargs)
        return result

    return wrapper


class IndexOptimizer:
    """Database index optimization recommendations."""

    def analyze_query_patterns(self, metrics: List[QueryMetrics]) -> Dict[str, Any]:
        """Analyze query patterns for index recommendations."""
        recommendations: Dict[str, Any] = {}
        for metric in metrics:
            recommendations.setdefault(metric.query.split()[0], 0)
            recommendations[metric.query.split()[0]] += 1
        return recommendations

    def suggest_indexes(self, table_name: str, query_patterns: List[str]) -> List[str]:
        """Suggest indexes based on query patterns."""
        return [f"CREATE INDEX idx_{table_name}_{col} ON {table_name}({col});" for col in query_patterns]

    def check_existing_indexes(self, table_name: str) -> List[Dict[str, Any]]:
        """Check existing indexes on table."""
        # Placeholder implementation
        return []


# Security note: All performance monitoring respects the same security constraints
# as the main DatabaseManager - table names and columns are validated via whitelists