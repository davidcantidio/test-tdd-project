"""
🧪 Redis Cache System Tests

Comprehensive test suite for the Redis caching layer:
- RedisCacheManager functionality
- CachedDatabaseManager integration
- Performance metrics tracking
- Cache invalidation strategies
- Fallback behavior when Redis unavailable
- Thread safety and concurrent operations
- Security and key generation
"""

import sys
import time
import json
import pytest
import threading
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, Optional

# Add parent directories to path for imports
sys.path.append(str(Path(__file__).parent.parent))

try:
    from streamlit_extension.utils.redis_cache import (
        RedisCacheManager, CacheStrategy, CacheMetrics,
        get_cache_manager, cached, invalidate_cache,
        get_cache_stats, flush_cache
    )
    REDIS_CACHE_AVAILABLE = True
except ImportError:
    REDIS_CACHE_AVAILABLE = False

try:
    from streamlit_extension.utils.cached_database import CachedDatabaseManager
    CACHED_DB_AVAILABLE = True
except ImportError:
    CACHED_DB_AVAILABLE = False


@pytest.mark.skipif(not REDIS_CACHE_AVAILABLE, reason="Redis cache not available")
class TestCacheStrategy:
    """Test cache strategy configurations."""
    
    def test_ttl_mappings(self):
        """Test TTL mapping for different operation types."""
        assert CacheStrategy.get_ttl("quick") == 300
        assert CacheStrategy.get_ttl("medium") == 900
        assert CacheStrategy.get_ttl("heavy") == 1800
        assert CacheStrategy.get_ttl("static") == 3600
        assert CacheStrategy.get_ttl("unknown") == 900  # Default
    
    def test_cache_prefixes(self):
        """Test cache prefix constants."""
        assert CacheStrategy.PREFIX_CLIENT == "client"
        assert CacheStrategy.PREFIX_PROJECT == "project"
        assert CacheStrategy.PREFIX_EPIC == "epic"
        assert CacheStrategy.PREFIX_TASK == "task"
        assert CacheStrategy.PREFIX_ANALYTICS == "analytics"


@pytest.mark.skipif(not REDIS_CACHE_AVAILABLE, reason="Redis cache not available")
class TestCacheMetrics:
    """Test cache metrics tracking."""
    
    def setUp(self):
        """Setup for each test."""
        self.metrics = CacheMetrics()
    
    def test_initial_stats(self):
        """Test initial statistics."""
        self.setUp()
        stats = self.metrics.get_stats()
        
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["errors"] == 0
        assert stats["total_requests"] == 0
        assert stats["avg_response_time"] == 0.0
        assert stats["hit_rate_percent"] == 0.0
    
    def test_record_hit(self):
        """Test recording cache hits."""
        self.setUp()
        
        self.metrics.record_hit(0.1)
        self.metrics.record_hit(0.2)
        
        stats = self.metrics.get_stats()
        assert stats["hits"] == 2
        assert stats["total_requests"] == 2
        assert stats["hit_rate_percent"] == 100.0
        assert 0.1 <= stats["avg_response_time"] <= 0.2
    
    def test_record_miss(self):
        """Test recording cache misses."""
        self.setUp()
        
        self.metrics.record_miss(0.3)
        self.metrics.record_miss(0.4)
        
        stats = self.metrics.get_stats()
        assert stats["misses"] == 2
        assert stats["total_requests"] == 2
        assert stats["hit_rate_percent"] == 0.0
        assert 0.3 <= stats["avg_response_time"] <= 0.4
    
    def test_mixed_operations(self):
        """Test mixed cache operations."""
        self.setUp()
        
        self.metrics.record_hit(0.1)
        self.metrics.record_miss(0.3)
        self.metrics.record_hit(0.2)
        self.metrics.record_error()
        
        stats = self.metrics.get_stats()
        assert stats["hits"] == 2
        assert stats["misses"] == 1
        assert stats["errors"] == 1
        assert stats["total_requests"] == 4
        assert stats["hit_rate_percent"] == 66.66666666666667  # 2 hits out of 3 cache ops
    
    def test_reset_stats(self):
        """Test statistics reset."""
        self.setUp()
        
        # Record some operations
        self.metrics.record_hit(0.1)
        self.metrics.record_miss(0.2)
        
        # Reset
        self.metrics.reset_stats()
        
        stats = self.metrics.get_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["total_requests"] == 0


@pytest.mark.skipif(not REDIS_CACHE_AVAILABLE, reason="Redis cache not available")
class TestRedisCacheManager:
    """Test Redis cache manager."""
    
    def setUp(self):
        """Setup for each test."""
        # Use test configuration
        self.cache_manager = RedisCacheManager(
            host="localhost",
            port=6379,
            db=15,  # Use test DB
            socket_timeout=1.0,
            socket_connect_timeout=1.0
        )
    
    @patch('streamlit_extension.utils.redis_cache.redis')
    def test_initialization_without_redis(self, mock_redis):
        """Test initialization when Redis is not available."""
        mock_redis.Redis.side_effect = ConnectionError("Redis not available")
        
        cache_manager = RedisCacheManager()
        assert not cache_manager.is_available
        assert cache_manager.client is None
    
    def test_key_generation(self):
        """Test secure cache key generation."""
        self.setUp()
        
        # Test simple key
        key1 = self.cache_manager._generate_cache_key("client", 123)
        assert key1.startswith("tdd_cache:client:")
        assert len(key1.split(":")) == 3
        
        # Test complex key with kwargs
        key2 = self.cache_manager._generate_cache_key(
            "client", 123, status="active", include_inactive=True
        )
        assert key2.startswith("tdd_cache:client:")
        assert key1 != key2  # Different parameters should generate different keys
        
        # Test same parameters should generate same key
        key3 = self.cache_manager._generate_cache_key(
            "client", 123, status="active", include_inactive=True
        )
        assert key2 == key3
    
    def test_serialization(self):
        """Test data serialization/deserialization."""
        self.setUp()
        
        test_data = {
            "id": 123,
            "name": "Test Client",
            "status": "active",
            "metadata": {"created": "2024-01-01", "tags": ["important"]}
        }
        
        # Test serialization
        serialized = self.cache_manager._serialize_data(test_data)
        assert isinstance(serialized, str)
        
        # Test deserialization
        deserialized = self.cache_manager._deserialize_data(serialized)
        assert deserialized == test_data
    
    @patch('streamlit_extension.utils.redis_cache.redis')
    def test_cache_operations_mock(self, mock_redis):
        """Test cache operations with mocked Redis."""
        # Setup mock Redis client
        mock_client = Mock()
        mock_redis.Redis.return_value = mock_client
        mock_client.ping.return_value = True
        
        cache_manager = RedisCacheManager()
        cache_manager.client = mock_client
        cache_manager.is_available = True
        
        # Test set operation
        mock_client.setex.return_value = True
        result = cache_manager.set("test_key", {"data": "test"}, 300)
        assert result is True
        mock_client.setex.assert_called_once()
        
        # Test get operation
        mock_client.get.return_value = json.dumps({"data": "test"}).encode('utf-8')
        result = cache_manager.get("test_key")
        assert result == {"data": "test"}
        mock_client.get.assert_called_once()
        
        # Test delete operation
        mock_client.delete.return_value = 1
        result = cache_manager.delete("test_key")
        assert result is True
        mock_client.delete.assert_called_once()
    
    def test_health_check_throttling(self):
        """Test health check throttling."""
        self.setUp()
        
        # Set short health check interval for testing
        self.cache_manager.health_check_interval = 0.1
        
        # First call should perform actual health check
        initial_time = self.cache_manager._last_health_check
        health1 = self.cache_manager._check_health()
        
        # Immediate second call should be throttled
        health2 = self.cache_manager._check_health()
        assert self.cache_manager._last_health_check == initial_time or abs(self.cache_manager._last_health_check - initial_time) < 0.1
        
        # Wait for throttle period to pass
        time.sleep(0.2)
        health3 = self.cache_manager._check_health()
        assert self.cache_manager._last_health_check > initial_time + 0.1


@pytest.mark.skipif(not REDIS_CACHE_AVAILABLE, reason="Redis cache not available")
class TestCacheDecorator:
    """Test the @cached decorator."""
    
    def setUp(self):
        """Setup for each test."""
        # Clear any existing cache
        try:
            flush_cache()
        except:
            pass
    
    def test_cached_decorator(self):
        """Test cached decorator functionality."""
        self.setUp()
        
        call_count = 0
        
        @cached("test", ttl=300)
        def expensive_function(param1, param2=None):
            nonlocal call_count
            call_count += 1
            return {"result": f"{param1}_{param2}", "call_count": call_count}
        
        # First call should execute function
        result1 = expensive_function("value1", param2="value2")
        assert result1["call_count"] == 1
        
        # Second call with same parameters should use cache
        result2 = expensive_function("value1", param2="value2")
        assert result2["call_count"] == 1  # Same call count from cache
        assert result1 == result2
        
        # Call with different parameters should execute function again
        result3 = expensive_function("value3", param2="value4")
        assert result3["call_count"] == 2
    
    def test_cache_invalidation(self):
        """Test cache invalidation."""
        self.setUp()
        
        call_count = 0
        
        @cached("test_invalidation", ttl=300)
        def cached_function(param):
            nonlocal call_count
            call_count += 1
            return {"result": param, "call_count": call_count}
        
        # First call
        result1 = cached_function("test")
        assert result1["call_count"] == 1
        
        # Second call should use cache
        result2 = cached_function("test")
        assert result2["call_count"] == 1
        
        # Invalidate cache
        invalidate_cache("test_invalidation", cached_function.__name__, "test")
        
        # Third call should execute function again
        result3 = cached_function("test")
        assert result3["call_count"] == 2


@pytest.mark.skipif(not CACHED_DB_AVAILABLE, reason="Cached database not available")
class TestCachedDatabaseManager:
    """Test cached database manager integration."""
    
    def setUp(self):
        """Setup for each test."""
        # Mock the underlying database manager
        self.mock_db_manager = Mock()
        
        # Create cached database manager
        with patch('streamlit_extension.utils.cached_database.DatabaseManager') as mock_db_class:
            mock_db_class.return_value = self.mock_db_manager
            self.cached_db = CachedDatabaseManager(
                framework_db_path="test.db",
                enable_cache=True
            )
    
    def test_initialization(self):
        """Test cached database manager initialization."""
        assert self.cached_db.db_manager == self.mock_db_manager
        assert self.cached_db.enable_cache is True
        assert "total_operations" in self.cached_db.performance_stats
    
    def test_cache_invalidation_strategy(self):
        """Test cache invalidation on data modifications."""
        # Test client creation
        self.mock_db_manager.create_client.return_value = 123
        
        with patch.object(self.cached_db, '_invalidate_related_cache') as mock_invalidate:
            result = self.cached_db.create_client(name="Test Client")
            assert result == 123
            mock_invalidate.assert_called_once_with("client")
        
        # Test client update
        self.mock_db_manager.update_client.return_value = True
        
        with patch.object(self.cached_db, '_invalidate_related_cache') as mock_invalidate:
            result = self.cached_db.update_client(123, name="Updated Client")
            assert result is True
            mock_invalidate.assert_called_once_with("client", 123)
    
    def test_performance_stats_tracking(self):
        """Test performance statistics tracking."""
        initial_stats = self.cached_db.get_performance_stats()
        assert initial_stats["total_operations"] == 0
        
        # Mock a database operation
        self.mock_db_manager.get_clients.return_value = {"data": []}
        
        # Perform operation
        self.cached_db.get_clients()
        
        # Check stats updated
        updated_stats = self.cached_db.get_performance_stats()
        assert updated_stats["total_operations"] >= 1
    
    def test_passthrough_methods(self):
        """Test passthrough for methods not explicitly cached."""
        # Test method that should pass through
        self.mock_db_manager.check_database_health.return_value = {"status": "healthy"}
        
        result = self.cached_db.check_database_health()
        assert result == {"status": "healthy"}
        self.mock_db_manager.check_database_health.assert_called_once()


@pytest.mark.skipif(not REDIS_CACHE_AVAILABLE, reason="Redis cache not available")
class TestConcurrency:
    """Test thread safety and concurrent operations."""
    
    def setUp(self):
        """Setup for each test."""
        self.cache_manager = RedisCacheManager(db=15)  # Use test DB
    
    def test_concurrent_metrics_updates(self):
        """Test concurrent metrics updates are thread-safe."""
        self.setUp()
        
        metrics = CacheMetrics()
        num_threads = 10
        operations_per_thread = 100
        
        def update_metrics():
            for _ in range(operations_per_thread):
                metrics.record_hit(0.1)
                metrics.record_miss(0.2)
        
        # Start multiple threads
        threads = []
        for _ in range(num_threads):
            thread = threading.Thread(target=update_metrics)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify final counts
        stats = metrics.get_stats()
        expected_total = num_threads * operations_per_thread * 2  # hits + misses
        assert stats["total_requests"] == expected_total
        assert stats["hits"] == num_threads * operations_per_thread
        assert stats["misses"] == num_threads * operations_per_thread
    
    def test_concurrent_cache_operations(self):
        """Test concurrent cache operations."""
        self.setUp()
        
        num_threads = 5
        operations_per_thread = 20
        results = []
        results_lock = threading.Lock()
        
        def cache_operations(thread_id):
            thread_results = []
            for i in range(operations_per_thread):
                key = f"thread_{thread_id}_key_{i}"
                value = {"thread": thread_id, "operation": i}
                
                # Set value
                set_result = self.cache_manager.set(key, value, 60)
                thread_results.append(("set", set_result))
                
                # Get value
                get_result = self.cache_manager.get(key)
                thread_results.append(("get", get_result == value))
            
            with results_lock:
                results.extend(thread_results)
        
        # Start multiple threads
        threads = []
        for i in range(num_threads):
            thread = threading.Thread(target=cache_operations, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify results (if Redis is available)
        if self.cache_manager.is_available:
            set_operations = [r for r in results if r[0] == "set"]
            get_operations = [r for r in results if r[0] == "get"]
            
            # Most operations should succeed
            successful_sets = sum(1 for _, success in set_operations if success)
            successful_gets = sum(1 for _, success in get_operations if success)
            
            assert successful_sets > 0
            assert successful_gets > 0


@pytest.mark.skipif(not REDIS_CACHE_AVAILABLE, reason="Redis cache not available")
class TestFallbackBehavior:
    """Test fallback behavior when Redis is unavailable."""
    
    def test_graceful_degradation(self):
        """Test graceful degradation when Redis is unavailable."""
        # Create cache manager with invalid connection
        cache_manager = RedisCacheManager(
            host="invalid_host",
            port=9999,
            socket_connect_timeout=0.1
        )
        
        # Operations should not raise exceptions
        assert cache_manager.get("test_key") is None
        assert cache_manager.set("test_key", "test_value") is False
        assert cache_manager.delete("test_key") is False
        
        # Cache info should indicate unavailability
        info = cache_manager.get_cache_info()
        assert info["available"] is False
    
    def test_cached_decorator_fallback(self):
        """Test cached decorator works without Redis."""
        call_count = 0
        
        # Temporarily disable Redis
        with patch('streamlit_extension.utils.redis_cache.REDIS_AVAILABLE', False):
            @cached("test_fallback", ttl=300)
            def test_function(param):
                nonlocal call_count
                call_count += 1
                return f"result_{param}_{call_count}"
            
            # Function should execute normally without caching
            result1 = test_function("test")
            result2 = test_function("test")
            
            # Without cache, function should be called each time
            assert call_count == 2
            assert result1 != result2


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])