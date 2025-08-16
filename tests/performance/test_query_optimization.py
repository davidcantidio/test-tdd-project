"""
🧪 Query Optimization Performance Tests

Tests for query optimization features including performance monitoring,
caching, and optimization suggestions.
"""

import time
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from streamlit_extension.utils.performance import QueryOptimizer, CacheManager


class TestQueryOptimization:
    """Test query optimization and monitoring features."""

    def test_query_execution_time_monitoring(self):
        """Test query performance timing and monitoring."""
        optimizer = QueryOptimizer()
        
        # Simulate a query with some execution time
        with optimizer.measure_query("SELECT 1"):
            time.sleep(0.01)  # Simulate 10ms query
            
        stats = optimizer.get_query_statistics()
        
        assert stats["total_queries"] == 1
        assert stats["avg_execution_time"] > 0
        assert stats["avg_execution_time"] >= 10.0  # Should be at least 10ms
        assert stats["slow_query_count"] == 0  # 10ms is below 100ms threshold
        assert stats["cache_hit_rate"] == 0.0

    def test_slow_query_detection(self):
        """Test detection of slow queries."""
        optimizer = QueryOptimizer()
        optimizer.slow_query_threshold_ms = 5.0  # Lower threshold for testing
        
        # Simulate a slow query
        with optimizer.measure_query("SELECT * FROM large_table"):
            time.sleep(0.01)  # 10ms > 5ms threshold
            
        slow_queries = optimizer.get_slow_queries()
        stats = optimizer.get_query_statistics()
        
        assert len(slow_queries) == 1
        assert stats["slow_query_count"] == 1
        assert "large_table" in slow_queries[0].query

    def test_optimization_suggestions(self):
        """Test query optimization suggestions."""
        optimizer = QueryOptimizer()
        optimizer.slow_query_threshold_ms = 5.0
        
        # Add some slow queries
        with optimizer.measure_query("SELECT * FROM users WHERE email = ?"):
            time.sleep(0.01)
            
        with optimizer.measure_query("SELECT * FROM orders WHERE date > ?"):
            time.sleep(0.01)
            
        suggestions = optimizer.suggest_optimizations()
        
        assert len(suggestions) == 2
        assert all("Optimize query" in suggestion for suggestion in suggestions)

    def test_cache_performance_improvement(self):
        """Test caching system performance."""
        cache = CacheManager()
        
        # Test cache miss
        key = cache.cache_key("items", {"status": "active"}, "id", 1)
        result = cache.get_cached_result(key)
        
        assert result is None
        
        # Test cache set and hit
        test_data = [{"id": 1, "name": "test"}]
        cache.set_cached_result(key, test_data)
        cached_result = cache.get_cached_result(key)
        
        assert cached_result == test_data
        
        # Verify statistics
        stats = cache.get_cache_statistics()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 0.5

    def test_cache_expiration(self):
        """Test cache TTL and expiration."""
        cache = CacheManager(default_ttl=1)  # 1 second TTL
        
        key = cache.cache_key("items", {}, "id", 1)
        cache.set_cached_result(key, "test_data")
        
        # Should be cached immediately
        assert cache.get_cached_result(key) == "test_data"
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Should be expired now
        assert cache.get_cached_result(key) is None

    def test_cache_invalidation(self):
        """Test cache invalidation by table."""
        cache = CacheManager()
        
        # Add entries for different tables
        key1 = cache.cache_key("users", {}, "id", 1)
        key2 = cache.cache_key("orders", {}, "id", 1)
        
        cache.set_cached_result(key1, "users_data")
        cache.set_cached_result(key2, "orders_data")
        
        # Invalidate users table cache
        cache.invalidate_table_cache("users")
        
        # Users cache should be gone, orders should remain
        assert cache.get_cached_result(key1) is None
        assert cache.get_cached_result(key2) == "orders_data"

    def test_query_metrics_collection(self):
        """Test comprehensive query metrics collection."""
        optimizer = QueryOptimizer()
        
        # Log various metrics
        optimizer.log_query_metrics(
            "SELECT * FROM users", 
            execution_time_ms=15.5,
            rows_returned=100,
            rows_examined=100,
            cache_hit=False
        )
        
        optimizer.log_query_metrics(
            "SELECT * FROM users", 
            execution_time_ms=2.1,
            rows_returned=100,
            rows_examined=0,
            cache_hit=True
        )
        
        metrics = optimizer.query_metrics
        stats = optimizer.get_query_statistics()
        
        assert len(metrics) == 2
        assert metrics[0].execution_time_ms == 15.5
        assert metrics[0].cache_hit is False
        assert metrics[1].cache_hit is True
        assert stats["cache_hit_rate"] == 0.5