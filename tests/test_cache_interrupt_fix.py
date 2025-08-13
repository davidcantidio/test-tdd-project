"""
🧪 Test Suite for Cache Interrupt Fix

Tests to validate that the cache system fixes the KeyboardInterrupt issue
identified in the Codex audit at streamlit_extension/utils/cache.py:187.

Target: 100% interrupt-safe cache operations
"""

import pytest
import time
import threading
import signal
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the duration_system to the path for imports
sys.path.append(str(Path(__file__).parent.parent))

from duration_system.cache_fix import (
    InterruptSafeCache, 
    create_interrupt_safe_cache_decorator,
    test_interrupt_safety
)


class TestCacheInterruptFix:
    """Test suite for cache interrupt safety fixes."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.cache = InterruptSafeCache(
            default_ttl=10, 
            max_size=100, 
            enable_disk_cache=False,  # Disable disk for faster tests
            lock_timeout=1.0,
            disk_timeout=0.5
        )
    
    def teardown_method(self):
        """Cleanup after each test."""
        try:
            self.cache.shutdown()
        except:
            pass
    
    def test_basic_cache_operations_work(self):
        """Test that basic cache operations work correctly."""
        # Test set
        assert self.cache.set("test_key", "test_value", 5) is True
        
        # Test get
        result = self.cache.get("test_key")
        assert result == "test_value"
        
        # Test stats
        stats = self.cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 0
        
        # Test delete
        assert self.cache.delete("test_key") is True
        
        # Verify deletion
        result = self.cache.get("test_key")
        assert result is None
    
    def test_lock_timeout_protection(self):
        """Test that lock operations have timeout protection."""
        # Mock the lock to simulate a hang
        original_lock = self.cache._lock
        
        # Create a mock lock that times out
        mock_lock = MagicMock()
        mock_lock.acquire.return_value = False  # Simulate timeout
        
        self.cache._lock = mock_lock
        
        # Operations should fail gracefully, not hang
        assert self.cache.set("key", "value") is False
        assert self.cache.get("key") is None
        assert self.cache.delete("key") is False
        
        # Restore original lock
        self.cache._lock = original_lock
    
    def test_interrupt_flag_stops_operations(self):
        """Test that setting interrupt flag stops cache operations."""
        # Set interrupt flag
        self.cache._interrupted = True
        
        # All operations should fail gracefully
        assert self.cache.set("key", "value") is False
        assert self.cache.get("key") is None
        assert self.cache.delete("key") is False
        
        # Stats should still work
        stats = self.cache.get_stats()
        assert stats["interrupted"] is True
    
    def test_concurrent_access_safety(self):
        """Test that concurrent access doesn't cause deadlocks."""
        results = []
        errors = []
        
        def cache_worker(worker_id):
            """Worker function for concurrent access test."""
            try:
                for i in range(10):
                    key = f"worker_{worker_id}_key_{i}"
                    value = f"worker_{worker_id}_value_{i}"
                    
                    # Set, get, delete cycle
                    if self.cache.set(key, value):
                        retrieved = self.cache.get(key)
                        if retrieved == value:
                            self.cache.delete(key)
                            results.append(f"worker_{worker_id}_success_{i}")
                        else:
                            errors.append(f"worker_{worker_id}_mismatch_{i}")
                    else:
                        errors.append(f"worker_{worker_id}_set_failed_{i}")
                        
            except Exception as e:
                errors.append(f"worker_{worker_id}_exception: {e}")
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=cache_worker, args=(i,))
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for completion with timeout
        for thread in threads:
            thread.join(timeout=5.0)
            # Force terminate if still alive
            if thread.is_alive():
                errors.append("Thread timeout - possible deadlock")
        
        # Verify results
        assert len(errors) == 0, f"Concurrent access errors: {errors}"
        assert len(results) >= 25, f"Expected >=25 successes, got {len(results)}"  # 5 workers * 10 ops, allow some failures due to timeouts
    
    def test_exception_recovery(self):
        """Test that cache recovers from internal exceptions."""
        # Test with invalid data that might cause pickle errors
        problematic_data = [
            lambda x: x,  # Function (not picklable)
            type("TestClass", (), {}),  # Class (not picklable)
        ]
        
        for data in problematic_data:
            # Operations should not crash, just fail gracefully
            result = self.cache.set("problem_key", data)
            # Result can be True or False, shouldn't raise exception
            assert isinstance(result, bool)
            
            # Get should not crash
            retrieved = self.cache.get("problem_key")
            # Should return None or the data, shouldn't raise exception
            assert retrieved is None or retrieved == data
    
    def test_memory_cache_without_disk(self):
        """Test memory-only cache operations."""
        # Disable disk cache
        cache = InterruptSafeCache(enable_disk_cache=False, default_ttl=5)
        
        try:
            # Test basic operations
            assert cache.set("mem_key", "mem_value") is True
            assert cache.get("mem_key") == "mem_value"
            
            # Wait for expiration
            time.sleep(6)
            
            # Should be expired
            assert cache.get("mem_key") is None
            
            stats = cache.get_stats()
            assert stats["disk_writes"] == 0  # No disk operations
            
        finally:
            cache.shutdown()
    
    def test_lru_eviction_safety(self):
        """Test that LRU eviction doesn't cause issues."""
        # Create small cache to trigger eviction
        small_cache = InterruptSafeCache(max_size=3, enable_disk_cache=False)
        
        try:
            # Fill cache beyond capacity
            for i in range(5):
                small_cache.set(f"key_{i}", f"value_{i}")
            
            # Cache should have evicted older entries
            stats = small_cache.get_stats()
            assert stats["evictions"] >= 2
            assert stats["memory_entries"] <= 3
            
            # Recent entries should still be accessible
            assert small_cache.get("key_4") == "value_4"
            
        finally:
            small_cache.shutdown()
    
    @pytest.mark.parametrize("timeout_value", [0.1, 0.5, 1.0])
    def test_different_timeout_values(self, timeout_value):
        """Test cache with different timeout configurations."""
        cache = InterruptSafeCache(
            lock_timeout=timeout_value,
            disk_timeout=timeout_value,
            enable_disk_cache=False
        )
        
        try:
            # Basic operations should work with any reasonable timeout
            assert cache.set("timeout_key", "timeout_value") is True
            assert cache.get("timeout_key") == "timeout_value"
            
        finally:
            cache.shutdown()


class TestCacheDecoratorFix:
    """Test suite for the interrupt-safe cache decorator."""
    
    def test_decorator_basic_functionality(self):
        """Test that the decorator works correctly."""
        call_count = 0
        
        @create_interrupt_safe_cache_decorator(ttl=5)
        def expensive_function(x, y):
            nonlocal call_count
            call_count += 1
            time.sleep(0.01)  # Simulate work
            return x + y
        
        # First call should execute function
        result1 = expensive_function(1, 2)
        assert result1 == 3
        assert call_count == 1
        
        # Second call should use cache
        result2 = expensive_function(1, 2)
        assert result2 == 3
        assert call_count == 1  # Function not called again
        
        # Different parameters should execute function
        result3 = expensive_function(2, 3)
        assert result3 == 5
        assert call_count == 2
    
    def test_decorator_with_exceptions(self):
        """Test decorator behavior with exceptions."""
        call_count = 0
        
        @create_interrupt_safe_cache_decorator(ttl=5)
        def failing_function(should_fail):
            nonlocal call_count
            call_count += 1
            if should_fail:
                raise ValueError("Test error")
            return "success"
        
        # Successful call should be cached
        result = failing_function(False)
        assert result == "success"
        assert call_count == 1
        
        # Second successful call should use cache
        result = failing_function(False)
        assert result == "success"
        assert call_count == 1
        
        # Failing call should not be cached
        with pytest.raises(ValueError):
            failing_function(True)
        assert call_count == 2
        
        # Another failing call should execute again (not cached)
        with pytest.raises(ValueError):
            failing_function(True)
        assert call_count == 3
    
    def test_decorator_cache_management(self):
        """Test decorator cache management methods."""
        @create_interrupt_safe_cache_decorator(ttl=5)
        def test_function(x):
            return x * 2
        
        # Execute function
        result = test_function(5)
        assert result == 10
        
        # Check stats
        stats = test_function.get_cache_stats()
        assert isinstance(stats, dict)
        assert "hits" in stats
        
        # Clear cache
        test_function.clear_cache()
        
        # Stats should be reset/updated
        stats_after_clear = test_function.get_cache_stats()
        assert isinstance(stats_after_clear, dict)


class TestInterruptSafetyIntegration:
    """Integration tests for interrupt safety."""
    
    def test_interrupt_safety_function(self):
        """Test the built-in interrupt safety test function."""
        results = test_interrupt_safety()
        
        assert isinstance(results, dict)
        assert "success_count" in results
        assert "error_count" in results
        assert "total_tests" in results
        
        # Should have some successful operations
        assert results["success_count"] > 0
        
        # Total should be sum of success and errors
        assert results["total_tests"] == results["success_count"] + results["error_count"]
    
    def test_signal_handler_setup(self):
        """Test that signal handlers are set up correctly."""
        cache = InterruptSafeCache()
        
        try:
            # Should have original handler stored
            assert hasattr(cache, '_original_sigint_handler')
            
            # Should have signal handler method
            assert hasattr(cache, '_signal_handler')
            assert callable(cache._signal_handler)
            
        finally:
            cache.shutdown()
    
    def test_graceful_shutdown(self):
        """Test that cache shuts down gracefully."""
        cache = InterruptSafeCache(enable_disk_cache=True)
        
        # Add some data
        cache.set("shutdown_test", "data")
        
        # Shutdown should not raise exceptions
        cache.shutdown()
        
        # Cache should be marked as interrupted
        assert cache._interrupted is True
        
        # Operations after shutdown should fail gracefully
        assert cache.set("after_shutdown", "data") is False
        assert cache.get("after_shutdown") is None


@pytest.mark.performance
class TestCachePerformance:
    """Performance tests to ensure the fixes don't degrade performance."""
    
    def test_cache_performance_baseline(self):
        """Test that cache operations meet performance requirements."""
        cache = InterruptSafeCache(enable_disk_cache=False)
        
        try:
            # Test set performance
            start_time = time.time()
            for i in range(100):
                cache.set(f"perf_key_{i}", f"perf_value_{i}")
            set_time = time.time() - start_time
            
            # Should complete 100 sets in reasonable time (< 100ms)
            assert set_time < 0.1, f"Set operations too slow: {set_time:.3f}s"
            
            # Test get performance
            start_time = time.time()
            for i in range(100):
                cache.get(f"perf_key_{i}")
            get_time = time.time() - start_time
            
            # Should complete 100 gets in reasonable time (< 50ms)
            assert get_time < 0.05, f"Get operations too slow: {get_time:.3f}s"
            
            print(f"Performance: 100 sets in {set_time:.3f}s, 100 gets in {get_time:.3f}s")
            
        finally:
            cache.shutdown()
    
    def test_lock_contention_performance(self):
        """Test performance under lock contention."""
        cache = InterruptSafeCache(enable_disk_cache=False)
        results = []
        
        def contention_worker():
            start = time.time()
            for i in range(10):
                cache.set(f"contention_{threading.current_thread().ident}_{i}", i)
                cache.get(f"contention_{threading.current_thread().ident}_{i}")
            elapsed = time.time() - start
            results.append(elapsed)
        
        try:
            # Create contention with multiple threads
            threads = [threading.Thread(target=contention_worker) for _ in range(5)]
            
            start_time = time.time()
            for thread in threads:
                thread.start()
            
            for thread in threads:
                thread.join(timeout=2.0)
            
            total_time = time.time() - start_time
            
            # Should complete within reasonable time even with contention
            assert total_time < 1.0, f"Lock contention caused slowdown: {total_time:.3f}s"
            
            # All threads should complete
            assert len(results) == 5, f"Not all threads completed: {len(results)}/5"
            
        finally:
            cache.shutdown()


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v", "--tb=short"])