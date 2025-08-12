"""
🧪 Integration Tests for Advanced Cache System

Tests the cache system functionality, performance, and integration with other components:
- Multi-level caching (memory + disk)
- TTL and LRU eviction mechanisms  
- Cache invalidation and cleanup
- Database query caching integration
- Cache statistics and monitoring
- Disk cache size management
"""

import pytest
import time
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
import threading
import json

# Test imports
try:
    from streamlit_extension.utils.cache import (
        AdvancedCache, CacheEntry, get_cache, cached, 
        streamlit_cached, cache_database_query, 
        invalidate_cache_on_change, cleanup_expired_cache
    )
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False
    pytest.skip("Cache system not available", allow_module_level=True)


class TestCacheEntry:
    """Test CacheEntry functionality."""
    
    def test_cache_entry_creation(self):
        """Test cache entry creation with TTL."""
        entry = CacheEntry("test_value", ttl_seconds=60)
        
        assert entry.value == "test_value"
        assert not entry.is_expired()
        assert entry.is_valid()
        assert entry.access_count == 0
    
    def test_cache_entry_expiration(self):
        """Test cache entry expiration."""
        entry = CacheEntry("test_value", ttl_seconds=0)  # Immediate expiration
        time.sleep(0.1)  # Small delay
        
        assert entry.is_expired()
        assert not entry.is_valid()
    
    def test_cache_entry_access_tracking(self):
        """Test access count and timestamp tracking."""
        entry = CacheEntry("test_value")
        initial_time = entry.last_accessed
        
        # Access the entry
        value = entry.access()
        
        assert value == "test_value"
        assert entry.access_count == 1
        assert entry.last_accessed > initial_time
    
    def test_cache_entry_refresh(self):
        """Test cache entry TTL refresh."""
        entry = CacheEntry("test_value", ttl_seconds=1)
        initial_expires_at = entry.expires_at
        
        time.sleep(0.5)  # Wait half the TTL
        entry.refresh(ttl_seconds=2)  # Refresh with new TTL
        
        assert entry.expires_at > initial_expires_at


class TestAdvancedCache:
    """Test AdvancedCache functionality."""
    
    @pytest.fixture
    def temp_cache_dir(self):
        """Create temporary cache directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def cache(self, temp_cache_dir):
        """Create cache instance for testing."""
        cache = AdvancedCache(
            default_ttl=60,
            max_size=100,
            enable_disk_cache=True,
            max_disk_cache_mb=10
        )
        cache.cache_dir = temp_cache_dir / ".test_cache"
        cache.cache_dir.mkdir(exist_ok=True)
        return cache
    
    def test_cache_basic_operations(self, cache):
        """Test basic cache set/get operations."""
        # Set and get
        cache.set("test_key", "test_value")
        value = cache.get("test_key")
        
        assert value == "test_value"
        
        # Non-existent key
        value = cache.get("nonexistent", "default")
        assert value == "default"
    
    def test_cache_ttl_expiration(self, cache):
        """Test TTL-based cache expiration."""
        cache.set("expire_key", "expire_value", ttl=1)  # 1 second TTL
        
        # Should be available immediately
        assert cache.get("expire_key") == "expire_value"
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Should be expired
        assert cache.get("expire_key") is None
    
    def test_cache_lru_eviction(self, cache):
        """Test LRU eviction when cache is full."""
        cache.max_size = 3  # Small cache for testing
        
        # Fill cache
        cache.set("key1", "value1")
        cache.set("key2", "value2") 
        cache.set("key3", "value3")
        
        # Access key1 to make it recently used
        cache.get("key1")
        
        # Add another key, should evict key2 (least recently used)
        cache.set("key4", "value4")
        
        assert cache.get("key1") == "value1"  # Should still exist
        assert cache.get("key2") is None      # Should be evicted
        assert cache.get("key3") == "value3"  # Should still exist
        assert cache.get("key4") == "value4"  # Should exist
    
    def test_cache_delete_operation(self, cache):
        """Test cache deletion."""
        cache.set("delete_key", "delete_value")
        assert cache.get("delete_key") == "delete_value"
        
        # Delete and verify
        result = cache.delete("delete_key")
        assert result is True
        assert cache.get("delete_key") is None
    
    def test_cache_clear_operation(self, cache):
        """Test cache clearing."""
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        cache.clear()
        
        assert cache.get("key1") is None
        assert cache.get("key2") is None
    
    def test_cache_pattern_invalidation(self, cache):
        """Test pattern-based cache invalidation."""
        cache.set("user:123:profile", "profile_data")
        cache.set("user:123:settings", "settings_data")
        cache.set("user:456:profile", "other_profile")
        
        # Invalidate all user:123 keys
        count = cache.invalidate_pattern("user:123")
        
        assert count == 2
        assert cache.get("user:123:profile") is None
        assert cache.get("user:123:settings") is None
        assert cache.get("user:456:profile") == "other_profile"
    
    def test_cache_statistics(self, cache):
        """Test cache statistics tracking."""
        # Trigger hits and misses
        cache.set("stat_key", "stat_value")
        cache.get("stat_key")  # Hit
        cache.get("nonexistent")  # Miss
        
        stats = cache.get_stats()
        
        assert stats["hits"] >= 1
        assert stats["misses"] >= 1
        assert "hit_rate" in stats
        assert "memory_entries" in stats
    
    def test_disk_cache_operations(self, cache):
        """Test disk cache functionality."""
        # Set value that should persist to disk
        cache.set("disk_key", "disk_value")
        
        # Clear memory cache but not disk
        cache._memory_cache.clear()
        
        # Should retrieve from disk
        value = cache.get("disk_key")
        assert value == "disk_value"
        
        # Should have disk cache stats
        stats = cache.get_stats()
        assert stats["disk_cache_enabled"] is True
        assert stats["disk_size_mb"] >= 0
    
    def test_disk_cache_size_management(self, cache):
        """Test disk cache size limits and cleanup."""
        cache.max_disk_cache_mb = 1  # Very small limit for testing
        cache.max_disk_cache_bytes = 1024  # 1KB limit
        
        # Fill disk cache beyond limit
        large_value = "x" * 500  # 500 bytes
        for i in range(5):  # Total ~2.5KB
            cache.set(f"large_key_{i}", large_value)
        
        # Trigger cleanup
        cache._cleanup_disk_cache()
        
        # Should have cleaned up some entries
        stats = cache.get_stats()
        assert stats["disk_evictions"] > 0
    
    def test_cache_thread_safety(self, cache):
        """Test cache thread safety."""
        def worker(thread_id, iterations=50):
            for i in range(iterations):
                key = f"thread_{thread_id}_key_{i}"
                value = f"thread_{thread_id}_value_{i}"
                
                cache.set(key, value)
                retrieved = cache.get(key)
                assert retrieved == value
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Verify cache consistency
        stats = cache.get_stats()
        assert stats["hits"] > 0
        assert stats["memory_entries"] > 0


class TestCacheDecorators:
    """Test cache decorator functionality."""
    
    @pytest.fixture
    def mock_cache(self):
        """Create mock cache for testing decorators."""
        cache = Mock()
        cache.get.return_value = None  # Initially no cached value
        cache.set.return_value = None
        cache.default_ttl = 300
        cache._generate_key.return_value = "mock_key"
        
        with patch('streamlit_extension.utils.cache.get_cache', return_value=cache):
            yield cache
    
    def test_cached_decorator_basic(self, mock_cache):
        """Test basic cached decorator functionality."""
        call_count = 0
        
        @cached(ttl=60)
        def expensive_function(x, y):
            nonlocal call_count
            call_count += 1
            return x + y
        
        # First call should execute function
        result1 = expensive_function(1, 2)
        assert result1 == 3
        assert call_count == 1
        
        # Mock cache hit for second call
        mock_cache.get.return_value = 3
        result2 = expensive_function(1, 2)
        assert result2 == 3
        # Function shouldn't be called again due to cache hit
        assert call_count == 1
    
    def test_cache_database_query_decorator(self, mock_cache):
        """Test database query cache decorator."""
        query_count = 0
        
        @cache_database_query("test_query", ttl=600)
        def get_user_data(user_id):
            nonlocal query_count
            query_count += 1
            return {"id": user_id, "name": f"User {user_id}"}
        
        # First call
        result1 = get_user_data(123)
        assert result1["id"] == 123
        assert query_count == 1
        
        # Mock cache hit
        mock_cache.get.return_value = {"id": 123, "name": "User 123"}
        result2 = get_user_data(123)
        assert result2["id"] == 123
        # Query shouldn't be called again
        assert query_count == 1
        
        # Test cache invalidation method
        assert hasattr(get_user_data, 'invalidate_cache')
    
    def test_invalidate_cache_on_change_decorator(self, mock_cache):
        """Test cache invalidation decorator."""
        @invalidate_cache_on_change("user_data:", "user_profile:")
        def update_user(user_id, name):
            return {"id": user_id, "name": name, "updated": True}
        
        result = update_user(123, "New Name")
        assert result["updated"] is True
        
        # Should have called cache invalidation
        mock_cache.invalidate_pattern.assert_called()


class TestCacheIntegration:
    """Test cache integration with other components."""
    
    def test_cache_with_database_manager(self):
        """Test cache integration with database operations."""
        # This would test the actual database manager integration
        # For now, we'll test the structure is in place
        
        # Mock database manager
        mock_db = Mock()
        mock_db.get_epics.return_value = [{"id": 1, "name": "Test Epic"}]
        
        # Test that decorators can be applied
        decorated_method = cache_database_query("get_epics")(mock_db.get_epics)
        
        # Method should be callable
        result = decorated_method()
        assert len(result) == 1
        assert result[0]["name"] == "Test Epic"
    
    def test_cache_cleanup_integration(self):
        """Test cache cleanup integration."""
        # Create temporary cache
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = AdvancedCache(enable_disk_cache=True)
            cache.cache_dir = Path(temp_dir) / ".test_cache"
            cache.cache_dir.mkdir(exist_ok=True)
            
            # Add some expired entries
            cache.set("expired_key", "expired_value", ttl=0)
            time.sleep(0.1)
            
            # Mock global cache
            with patch('streamlit_extension.utils.cache.get_cache', return_value=cache):
                cleanup_expired_cache()
            
            # Expired entries should be cleaned
            assert cache.get("expired_key") is None
    
    def test_cache_configuration_integration(self):
        """Test cache configuration integration."""
        # Test that cache respects configuration
        with patch('streamlit_extension.utils.cache.get_config') as mock_config:
            mock_config.return_value = Mock(
                cache_ttl_seconds=1800,
                max_disk_cache_mb=200
            )
            
            # Get cache should use config values
            cache = get_cache()
            assert cache.default_ttl == 1800
            assert cache.max_disk_cache_mb == 200


class TestCachePerformance:
    """Test cache performance characteristics."""
    
    def test_cache_performance_scaling(self):
        """Test cache performance with increasing load."""
        cache = AdvancedCache(max_size=1000, enable_disk_cache=False)
        
        # Measure set operations
        start_time = time.time()
        for i in range(1000):
            cache.set(f"perf_key_{i}", f"perf_value_{i}")
        set_time = time.time() - start_time
        
        # Measure get operations
        start_time = time.time()
        for i in range(1000):
            cache.get(f"perf_key_{i}")
        get_time = time.time() - start_time
        
        # Performance should be reasonable (< 1 second for 1000 operations)
        assert set_time < 1.0
        assert get_time < 1.0
        
        # Get operations should be faster than set operations
        assert get_time < set_time
    
    def test_cache_memory_usage(self):
        """Test cache memory usage stays reasonable."""
        cache = AdvancedCache(max_size=100, enable_disk_cache=False)
        
        # Fill cache
        for i in range(100):
            cache.set(f"mem_key_{i}", "x" * 1000)  # 1KB values
        
        stats = cache.get_stats()
        
        # Memory usage should be tracked
        assert stats["memory_size_kb"] > 0
        # Should have evicted some entries to stay within limit
        assert stats["memory_entries"] <= 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])