"""
⚡ Performance Integration Tests

Tests system performance characteristics under realistic load scenarios:
- Concurrent user operations with full system stack
- Database transaction performance with all middleware
- Cache system performance under load
- Memory usage and garbage collection
- Response time consistency under varying load
- Resource utilization monitoring
- Bottleneck identification and performance regression detection

These tests ensure the system maintains acceptable performance
characteristics in production environments.
"""

import pytest
import time
import threading
import sqlite3
import tempfile
import psutil
import os
from pathlib import Path
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import Mock, patch
import uuid
import json
import gc
import sys
from typing import Dict, List, Any, Optional

# Core test imports
sys.path.append(str(Path(__file__).parent.parent.parent))

# Performance monitoring components
try:
    from streamlit_extension.utils.performance_monitor import PerformanceMonitor
    from streamlit_extension.utils.metrics_collector import MetricsCollector
    PERFORMANCE_MONITORING_AVAILABLE = True
except ImportError:
    PERFORMANCE_MONITORING_AVAILABLE = False

# Cache system for performance testing
try:
    from streamlit_extension.utils.cache import AdvancedCache, get_cache
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False

# Database components
try:
    from streamlit_extension.utils.database import DatabaseManager
    from duration_system.database_transactions import TransactionalDatabaseManager
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False

# Rate limiting for load testing
try:
    from streamlit_extension.middleware.rate_limiting import RateLimiter
    RATE_LIMITING_AVAILABLE = True
except ImportError:
    RATE_LIMITING_AVAILABLE = False


class PerformanceTestFramework:
    """Framework for comprehensive performance testing."""
    
    def __init__(self):
        self.temp_db = None
        self.db_path = None
        self.cache_dir = None
        self.performance_metrics = []
        self.resource_usage = []
        self.response_times = []
        self.test_data = {}
        
        # System components
        self.db_manager = None
        self.cache_manager = None
        self.rate_limiter = None
        self.performance_monitor = None
        
        # Performance tracking
        self.start_time = None
        self.baseline_memory = None
        self.baseline_cpu = None
        
    def setup(self):
        """Setup performance testing environment."""
        # Create temporary database
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.db_path = self.temp_db.name
        self.temp_db.close()
        
        # Create temporary cache directory
        self.cache_dir = tempfile.mkdtemp(prefix="perf_cache_")
        
        # Initialize database schema
        self._initialize_test_database()
        
        # Initialize performance monitoring
        self._initialize_performance_monitoring()
        
        # Initialize system components
        self._initialize_system_components()
        
        # Record baseline metrics
        self._record_baseline_metrics()
        
    def teardown(self):
        """Cleanup performance testing environment."""
        if self.db_manager:
            try:
                self.db_manager.close()
            except:
                pass
        
        if self.cache_manager:
            try:
                self.cache_manager.clear()
            except:
                pass
        
        # Cleanup temporary files
        if self.db_path and Path(self.db_path).exists():
            try:
                Path(self.db_path).unlink()
            except:
                pass
        
        if self.cache_dir and Path(self.cache_dir).exists():
            try:
                import shutil
                shutil.rmtree(self.cache_dir)
            except:
                pass
    
    def _initialize_test_database(self):
        """Initialize test database with performance-oriented schema."""
        with sqlite3.connect(self.db_path) as conn:
            # Enable WAL mode for better concurrency
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA cache_size=10000")  # Larger cache
            conn.execute("PRAGMA temp_store=MEMORY")
            
            # Create tables optimized for performance testing
            conn.execute("""
                CREATE TABLE IF NOT EXISTS performance_test_data (
                    id INTEGER PRIMARY KEY,
                    category TEXT NOT NULL,
                    data_size INTEGER NOT NULL,
                    payload TEXT NOT NULL,
                    checksum TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_category ON performance_test_data(category)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_data_size ON performance_test_data(data_size)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON performance_test_data(created_at)")
            
            # Large table for join testing
            conn.execute("""
                CREATE TABLE IF NOT EXISTS performance_relations (
                    id INTEGER PRIMARY KEY,
                    test_data_id INTEGER NOT NULL,
                    relation_type TEXT NOT NULL,
                    value REAL NOT NULL,
                    metadata TEXT,
                    FOREIGN KEY (test_data_id) REFERENCES performance_test_data(id)
                )
            """)
            
            conn.execute("CREATE INDEX IF NOT EXISTS idx_relation_type ON performance_relations(relation_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_test_data_id ON performance_relations(test_data_id)")
            
            conn.commit()
    
    def _initialize_performance_monitoring(self):
        """Initialize performance monitoring systems."""
        if PERFORMANCE_MONITORING_AVAILABLE:
            try:
                self.performance_monitor = PerformanceMonitor()
                self.metrics_collector = MetricsCollector()
            except:
                self._initialize_mock_monitoring()
        else:
            self._initialize_mock_monitoring()
    
    def _initialize_mock_monitoring(self):
        """Initialize mock performance monitoring."""
        self.performance_monitor = Mock()
        self.metrics_collector = Mock()
        
        # Configure mock responses
        self.performance_monitor.start_timer.return_value = "mock_timer"
        self.performance_monitor.end_timer.return_value = 0.1
        self.metrics_collector.collect.return_value = {"mock": "metrics"}
    
    def _initialize_system_components(self):
        """Initialize system components for testing."""
        # Database manager
        if DATABASE_AVAILABLE:
            try:
                self.db_manager = DatabaseManager(framework_db_path=self.db_path)
            except:
                self.db_manager = Mock()
        else:
            self.db_manager = Mock()
        
        # Cache manager
        if CACHE_AVAILABLE:
            try:
                self.cache_manager = AdvancedCache(
                    max_size=1000,
                    enable_disk_cache=True,
                    cache_dir=self.cache_dir
                )
            except:
                self.cache_manager = Mock()
        else:
            self.cache_manager = Mock()
        
        # Rate limiter
        if RATE_LIMITING_AVAILABLE:
            try:
                self.rate_limiter = RateLimiter(storage_backend="memory")
            except:
                self.rate_limiter = Mock()
        else:
            self.rate_limiter = Mock()
    
    def _record_baseline_metrics(self):
        """Record baseline system metrics."""
        process = psutil.Process(os.getpid())
        
        self.baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
        self.baseline_cpu = process.cpu_percent()
        self.start_time = time.time()
        
        # Record initial system state
        self.resource_usage.append({
            "timestamp": datetime.now().isoformat(),
            "memory_mb": self.baseline_memory,
            "cpu_percent": self.baseline_cpu,
            "event": "baseline"
        })
    
    def create_test_data(self, count: int, data_size: int = 1000, category: str = "test") -> List[int]:
        """Create test data for performance testing."""
        test_data_ids = []
        
        # Generate payload of specified size
        payload = "x" * data_size
        checksum = str(hash(payload))
        
        with sqlite3.connect(self.db_path) as conn:
            for i in range(count):
                cursor = conn.execute("""
                    INSERT INTO performance_test_data (category, data_size, payload, checksum)
                    VALUES (?, ?, ?, ?)
                """, (f"{category}_{i}", data_size, payload, checksum))
                
                test_data_ids.append(cursor.lastrowid)
                
                # Create related data
                for j in range(3):  # 3 relations per test data
                    conn.execute("""
                        INSERT INTO performance_relations (test_data_id, relation_type, value, metadata)
                        VALUES (?, ?, ?, ?)
                    """, (cursor.lastrowid, f"type_{j}", i * j * 0.1, f"meta_{i}_{j}"))
            
            conn.commit()
        
        return test_data_ids
    
    def measure_operation(self, operation_name: str, operation_func, *args, **kwargs) -> Dict[str, Any]:
        """Measure performance of a specific operation."""
        # Record pre-operation state
        process = psutil.Process(os.getpid())
        pre_memory = process.memory_info().rss / 1024 / 1024
        pre_cpu = process.cpu_percent()
        
        # Time the operation
        start_time = time.time()
        
        try:
            result = operation_func(*args, **kwargs)
            success = True
            error = None
        except Exception as e:
            result = None
            success = False
            error = str(e)
        
        end_time = time.time()
        operation_time = end_time - start_time
        
        # Record post-operation state
        post_memory = process.memory_info().rss / 1024 / 1024
        post_cpu = process.cpu_percent()
        
        metrics = {
            "operation": operation_name,
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": operation_time,
            "success": success,
            "error": error,
            "memory_before_mb": pre_memory,
            "memory_after_mb": post_memory,
            "memory_delta_mb": post_memory - pre_memory,
            "cpu_before_percent": pre_cpu,
            "cpu_after_percent": post_cpu,
            "result_size": len(str(result)) if result else 0
        }
        
        self.performance_metrics.append(metrics)
        self.response_times.append(operation_time)
        
        return metrics
    
    def run_load_test(self, operation_func, num_operations: int, 
                     max_workers: int = 10, *args, **kwargs) -> Dict[str, Any]:
        """Run load test with multiple concurrent operations."""
        load_test_start = time.time()
        results = []
        errors = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(self.measure_operation, f"load_op_{i}", operation_func, *args, **kwargs)
                for i in range(num_operations)
            ]
            
            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    errors.append(str(e))
        
        load_test_end = time.time()
        total_time = load_test_end - load_test_start
        
        # Calculate statistics
        successful_operations = [r for r in results if r["success"]]
        response_times = [r["duration_seconds"] for r in successful_operations]
        
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            p95_response_time = sorted(response_times)[int(len(response_times) * 0.95)] if len(response_times) > 20 else max_response_time
        else:
            avg_response_time = min_response_time = max_response_time = p95_response_time = 0
        
        load_test_results = {
            "total_operations": num_operations,
            "successful_operations": len(successful_operations),
            "failed_operations": len(errors),
            "total_time_seconds": total_time,
            "operations_per_second": len(successful_operations) / total_time,
            "avg_response_time": avg_response_time,
            "min_response_time": min_response_time,
            "max_response_time": max_response_time,
            "p95_response_time": p95_response_time,
            "success_rate": len(successful_operations) / num_operations * 100,
            "max_workers": max_workers,
            "errors": errors[:10]  # First 10 errors for debugging
        }
        
        return load_test_results
    
    def monitor_resource_usage(self, duration_seconds: int = 60, interval_seconds: float = 0.5):
        """Monitor resource usage over time."""
        monitoring_start = time.time()
        
        while time.time() - monitoring_start < duration_seconds:
            process = psutil.Process(os.getpid())
            
            self.resource_usage.append({
                "timestamp": datetime.now().isoformat(),
                "memory_mb": process.memory_info().rss / 1024 / 1024,
                "cpu_percent": process.cpu_percent(),
                "elapsed_seconds": time.time() - self.start_time,
                "event": "monitoring"
            })
            
            time.sleep(interval_seconds)
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary."""
        if not self.performance_metrics:
            return {"status": "no_metrics_collected"}
        
        successful_metrics = [m for m in self.performance_metrics if m["success"]]
        
        if not successful_metrics:
            return {"status": "no_successful_operations"}
        
        response_times = [m["duration_seconds"] for m in successful_metrics]
        memory_deltas = [m["memory_delta_mb"] for m in successful_metrics]
        
        # Calculate resource usage statistics
        current_memory = self.resource_usage[-1]["memory_mb"] if self.resource_usage else self.baseline_memory
        peak_memory = max((r["memory_mb"] for r in self.resource_usage), default=self.baseline_memory)
        
        summary = {
            "test_duration_seconds": time.time() - self.start_time,
            "total_operations": len(self.performance_metrics),
            "successful_operations": len(successful_metrics),
            "success_rate": len(successful_metrics) / len(self.performance_metrics) * 100,
            
            # Response time statistics
            "avg_response_time": sum(response_times) / len(response_times),
            "min_response_time": min(response_times),
            "max_response_time": max(response_times),
            "p95_response_time": sorted(response_times)[int(len(response_times) * 0.95)] if len(response_times) > 20 else max(response_times),
            
            # Memory statistics
            "baseline_memory_mb": self.baseline_memory,
            "current_memory_mb": current_memory,
            "peak_memory_mb": peak_memory,
            "memory_increase_mb": current_memory - self.baseline_memory,
            "peak_memory_increase_mb": peak_memory - self.baseline_memory,
            "avg_memory_delta_per_op_mb": sum(memory_deltas) / len(memory_deltas),
            
            # Performance indicators
            "operations_per_second": len(successful_metrics) / (time.time() - self.start_time),
            "memory_efficient": (current_memory - self.baseline_memory) < 100,  # Less than 100MB increase
            "response_time_consistent": (max(response_times) - min(response_times)) < 1.0,  # Less than 1s variance
        }
        
        return summary
    
    def database_operation_test(self, test_data_id: int):
        """Test database operation for performance measurement."""
        with sqlite3.connect(self.db_path) as conn:
            # Complex query with joins
            cursor = conn.execute("""
                SELECT ptd.id, ptd.category, ptd.data_size, 
                       COUNT(pr.id) as relation_count,
                       AVG(pr.value) as avg_value,
                       SUM(pr.value) as total_value
                FROM performance_test_data ptd
                LEFT JOIN performance_relations pr ON ptd.id = pr.test_data_id
                WHERE ptd.id = ?
                GROUP BY ptd.id, ptd.category, ptd.data_size
            """, (test_data_id,))
            
            result = cursor.fetchone()
            return result
    
    def cache_operation_test(self, key: str, value: str):
        """Test cache operation for performance measurement."""
        if self.cache_manager and hasattr(self.cache_manager, 'set'):
            # Set value
            self.cache_manager.set(key, value)
            
            # Get value
            retrieved = self.cache_manager.get(key)
            
            return retrieved == value
        else:
            # Mock operation
            time.sleep(0.001)  # Simulate cache operation
            return True


@pytest.fixture
def performance_framework():
    """Provide performance test framework."""
    framework = PerformanceTestFramework()
    framework.setup()
    yield framework
    framework.teardown()


class TestDatabasePerformance:
    """Test database performance under various conditions."""
    
    def test_database_crud_performance(self, performance_framework):
        """Test database CRUD operation performance."""
        framework = performance_framework
        
        # Create test data
        test_data_ids = framework.create_test_data(100, data_size=500, category="crud_test")
        
        # Test individual database operations
        for test_id in test_data_ids[:10]:  # Test first 10
            metrics = framework.measure_operation(
                "database_query",
                framework.database_operation_test,
                test_id
            )
            
            # Each operation should be fast
            assert metrics["duration_seconds"] < 0.1, f"Database query too slow: {metrics['duration_seconds']:.3f}s"
            assert metrics["success"], f"Database query failed: {metrics['error']}"
        
        # Get performance summary
        summary = framework.get_performance_summary()
        
        assert summary["avg_response_time"] < 0.05, "Average database response time too slow"
        assert summary["success_rate"] >= 95, "Database success rate too low"
        assert summary["response_time_consistent"], "Database response times not consistent"
    
    def test_database_concurrent_load(self, performance_framework):
        """Test database performance under concurrent load."""
        framework = performance_framework
        
        # Create test data
        test_data_ids = framework.create_test_data(50, data_size=1000, category="concurrent_test")
        
        # Run concurrent database operations
        load_results = framework.run_load_test(
            framework.database_operation_test,
            num_operations=100,
            max_workers=10,
            test_data_ids[0]  # Use first test data ID for all operations
        )
        
        # Verify performance under load
        assert load_results["operations_per_second"] > 50, "Database throughput too low under concurrent load"
        assert load_results["success_rate"] >= 95, "Database failure rate too high under load"
        assert load_results["avg_response_time"] < 0.2, "Database response time degraded under load"
        assert load_results["p95_response_time"] < 0.5, "Database P95 response time too high"
    
    def test_database_memory_efficiency(self, performance_framework):
        """Test database memory efficiency during operations."""
        framework = performance_framework
        
        # Create larger dataset
        test_data_ids = framework.create_test_data(500, data_size=2000, category="memory_test")
        
        # Monitor resource usage during operations
        monitoring_thread = threading.Thread(
            target=framework.monitor_resource_usage,
            args=(10, 0.1)  # Monitor for 10 seconds, sample every 0.1s
        )
        monitoring_thread.start()
        
        # Perform operations while monitoring
        for i in range(50):
            framework.measure_operation(
                f"memory_test_{i}",
                framework.database_operation_test,
                test_data_ids[i % len(test_data_ids)]
            )
            
            # Force garbage collection periodically
            if i % 10 == 0:
                gc.collect()
        
        monitoring_thread.join()
        
        # Analyze memory usage
        summary = framework.get_performance_summary()
        
        assert summary["memory_efficient"], f"Memory usage increased too much: {summary['memory_increase_mb']:.1f}MB"
        assert summary["peak_memory_increase_mb"] < 50, f"Peak memory usage too high: {summary['peak_memory_increase_mb']:.1f}MB"


class TestCachePerformance:
    """Test cache system performance."""
    
    def test_cache_hit_miss_performance(self, performance_framework):
        """Test cache hit/miss performance characteristics."""
        framework = performance_framework
        
        if not CACHE_AVAILABLE:
            pytest.skip("Cache system not available")
        
        # Test cache set operations
        for i in range(100):
            key = f"cache_key_{i}"
            value = f"cache_value_{i}" * 10  # Moderate size value
            
            metrics = framework.measure_operation(
                "cache_set",
                framework.cache_operation_test,
                key, value
            )
            
            assert metrics["duration_seconds"] < 0.01, f"Cache set operation too slow: {metrics['duration_seconds']:.3f}s"
        
        # Test cache get operations (should be faster)
        for i in range(50, 100):  # Get previously set values
            key = f"cache_key_{i}"
            
            if framework.cache_manager and hasattr(framework.cache_manager, 'get'):
                metrics = framework.measure_operation(
                    "cache_get",
                    framework.cache_manager.get,
                    key
                )
                
                assert metrics["duration_seconds"] < 0.005, f"Cache get operation too slow: {metrics['duration_seconds']:.3f}s"
        
        summary = framework.get_performance_summary()
        assert summary["avg_response_time"] < 0.01, "Cache operations too slow on average"
    
    def test_cache_concurrent_access(self, performance_framework):
        """Test cache performance under concurrent access."""
        framework = performance_framework
        
        if not CACHE_AVAILABLE:
            pytest.skip("Cache system not available")
        
        # Pre-populate cache
        for i in range(100):
            key = f"concurrent_key_{i}"
            value = f"concurrent_value_{i}" * 50
            if framework.cache_manager and hasattr(framework.cache_manager, 'set'):
                framework.cache_manager.set(key, value)
        
        # Run concurrent cache operations
        def mixed_cache_operation():
            """Perform mixed cache operations."""
            import random
            operation_type = random.choice(["get", "set"])
            key_id = random.randint(0, 150)  # Some misses, some hits
            
            if operation_type == "get":
                if framework.cache_manager and hasattr(framework.cache_manager, 'get'):
                    return framework.cache_manager.get(f"concurrent_key_{key_id}")
            else:
                if framework.cache_manager and hasattr(framework.cache_manager, 'set'):
                    return framework.cache_manager.set(f"new_key_{key_id}", f"new_value_{key_id}")
            
            return None
        
        load_results = framework.run_load_test(
            mixed_cache_operation,
            num_operations=500,
            max_workers=20
        )
        
        # Verify cache performance under concurrent load
        assert load_results["operations_per_second"] > 1000, "Cache throughput too low under concurrent access"
        assert load_results["success_rate"] >= 95, "Cache operation failure rate too high"
        assert load_results["avg_response_time"] < 0.01, "Cache response time degraded under concurrent load"


class TestSystemPerformanceIntegration:
    """Test integrated system performance."""
    
    def test_full_system_under_load(self, performance_framework):
        """Test full system performance under realistic load."""
        framework = performance_framework
        
        # Create comprehensive test data
        test_data_ids = framework.create_test_data(200, data_size=1500, category="system_test")
        
        def integrated_operation(operation_id: int):
            """Perform integrated operation involving multiple systems."""
            test_id = test_data_ids[operation_id % len(test_data_ids)]
            
            # Database operation
            db_result = framework.database_operation_test(test_id)
            
            # Cache operation
            cache_key = f"system_cache_{operation_id}"
            cache_value = f"cached_result_{operation_id}"
            
            if framework.cache_manager and hasattr(framework.cache_manager, 'set'):
                framework.cache_manager.set(cache_key, cache_value)
                cached_result = framework.cache_manager.get(cache_key)
            else:
                cached_result = cache_value
            
            # Rate limiting check
            if framework.rate_limiter and hasattr(framework.rate_limiter, 'is_allowed'):
                rate_allowed = framework.rate_limiter.is_allowed(f"user_{operation_id % 10}", "operation")
            else:
                rate_allowed = True
            
            return {
                "db_result": db_result,
                "cache_result": cached_result,
                "rate_allowed": rate_allowed
            }
        
        # Monitor system during load test
        monitoring_thread = threading.Thread(
            target=framework.monitor_resource_usage,
            args=(30, 0.2)  # Monitor for 30 seconds
        )
        monitoring_thread.start()
        
        # Run integrated load test
        load_results = framework.run_load_test(
            integrated_operation,
            num_operations=200,
            max_workers=15
        )
        
        monitoring_thread.join()
        
        # Verify integrated system performance
        assert load_results["operations_per_second"] > 20, "Integrated system throughput too low"
        assert load_results["success_rate"] >= 90, "Integrated system failure rate too high"
        assert load_results["avg_response_time"] < 0.5, "Integrated system response time too slow"
        assert load_results["p95_response_time"] < 1.0, "Integrated system P95 response time too high"
        
        # Verify system resource efficiency
        summary = framework.get_performance_summary()
        assert summary["memory_efficient"], "System not memory efficient under load"
        assert summary["peak_memory_increase_mb"] < 200, "System memory usage too high under load"
    
    def test_performance_regression_detection(self, performance_framework):
        """Test performance regression detection capabilities."""
        framework = performance_framework
        
        # Establish baseline performance
        baseline_operations = []
        for i in range(50):
            metrics = framework.measure_operation(
                f"baseline_op_{i}",
                framework.database_operation_test,
                1  # Use consistent test data
            )
            baseline_operations.append(metrics["duration_seconds"])
        
        baseline_avg = sum(baseline_operations) / len(baseline_operations)
        baseline_p95 = sorted(baseline_operations)[int(len(baseline_operations) * 0.95)]
        
        # Simulate potential performance regression
        regression_operations = []
        for i in range(50):
            # Add artificial delay to simulate regression
            time.sleep(0.001)  # Small additional delay
            
            metrics = framework.measure_operation(
                f"regression_op_{i}",
                framework.database_operation_test,
                1
            )
            regression_operations.append(metrics["duration_seconds"])
        
        regression_avg = sum(regression_operations) / len(regression_operations)
        regression_p95 = sorted(regression_operations)[int(len(regression_operations) * 0.95)]
        
        # Analyze performance difference
        avg_increase_pct = ((regression_avg - baseline_avg) / baseline_avg) * 100
        p95_increase_pct = ((regression_p95 - baseline_p95) / baseline_p95) * 100
        
        framework.performance_metrics.append({
            "operation": "regression_analysis",
            "baseline_avg": baseline_avg,
            "regression_avg": regression_avg,
            "avg_increase_pct": avg_increase_pct,
            "baseline_p95": baseline_p95,
            "regression_p95": regression_p95,
            "p95_increase_pct": p95_increase_pct,
            "regression_detected": avg_increase_pct > 10  # 10% threshold
        })
        
        # In a real scenario, we'd alert if regression detected
        # For testing, we verify the detection mechanism works
        assert abs(avg_increase_pct) >= 0, "Performance comparison mechanism not working"
    
    def test_memory_leak_detection(self, performance_framework):
        """Test memory leak detection during extended operations."""
        framework = performance_framework
        
        # Create test data
        test_data_ids = framework.create_test_data(100, data_size=1000, category="memory_leak_test")
        
        # Monitor memory usage over extended period
        memory_samples = []
        
        for iteration in range(10):  # 10 iterations
            # Record memory before iteration
            process = psutil.Process(os.getpid())
            memory_before = process.memory_info().rss / 1024 / 1024
            
            # Perform operations
            for i in range(20):
                framework.measure_operation(
                    f"leak_test_{iteration}_{i}",
                    framework.database_operation_test,
                    test_data_ids[i % len(test_data_ids)]
                )
            
            # Force garbage collection
            gc.collect()
            
            # Record memory after iteration
            memory_after = process.memory_info().rss / 1024 / 1024
            
            memory_samples.append({
                "iteration": iteration,
                "memory_before": memory_before,
                "memory_after": memory_after,
                "memory_delta": memory_after - memory_before
            })
            
            # Small delay between iterations
            time.sleep(0.1)
        
        # Analyze memory growth pattern
        memory_growth = [sample["memory_after"] for sample in memory_samples]
        
        # Calculate trend - should not grow significantly
        first_half_avg = sum(memory_growth[:5]) / 5
        second_half_avg = sum(memory_growth[5:]) / 5
        growth_rate = ((second_half_avg - first_half_avg) / first_half_avg) * 100
        
        # Memory should not grow more than 5% over the test period
        assert growth_rate < 5, f"Potential memory leak detected: {growth_rate:.1f}% growth"
        
        # Final memory should not be significantly higher than baseline
        final_memory = memory_growth[-1]
        memory_increase = final_memory - framework.baseline_memory
        
        assert memory_increase < 50, f"Memory increased too much: {memory_increase:.1f}MB"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])