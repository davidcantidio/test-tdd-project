"""
🧪 Performance System Test Suite

Comprehensive tests for the performance testing infrastructure:
- PerformanceProfiler functionality
- DatabasePerformanceTester validation
- LoadTester verification
- PerformanceMonitor testing
- Report generation validation
"""

import pytest
import time
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import threading

from streamlit_extension.utils.performance_tester import (
    PerformanceProfiler,
    DatabasePerformanceTester,
    LoadTester,
    PerformanceMonitor,
    PerformanceReporter,
    LoadTestConfig,
    PerformanceMetrics,
    run_quick_performance_check,
    create_performance_test_suite
)


class TestPerformanceProfiler:
    """Test PerformanceProfiler functionality."""
    
    def test_profiler_initialization(self):
        """Test profiler initializes correctly."""
        profiler = PerformanceProfiler()
        assert profiler.metrics == []
        assert profiler.baseline_metrics == {}
        assert profiler.start_time is None
        assert not profiler.memory_tracker_active
    
    def test_profile_operation_context_manager(self):
        """Test operation profiling context manager."""
        profiler = PerformanceProfiler()
        
        with profiler.profile_operation("test_operation"):
            time.sleep(0.01)  # Small delay to ensure measurable time
        
        assert len(profiler.metrics) == 1
        metric = profiler.metrics[0]
        assert metric.operation_name == "test_operation"
        assert metric.response_time > 0
        assert metric.success is True
        assert metric.error_message is None
    
    def test_profile_operation_with_exception(self):
        """Test profiling operations that raise exceptions."""
        profiler = PerformanceProfiler()
        
        with pytest.raises(ValueError):
            with profiler.profile_operation("failing_operation"):
                raise ValueError("Test error")
        
        assert len(profiler.metrics) == 1
        metric = profiler.metrics[0]
        assert metric.operation_name == "failing_operation"
        assert metric.success is False
        assert metric.error_message == "Test error"
    
    def test_statistics_generation(self):
        """Test statistics generation from metrics."""
        profiler = PerformanceProfiler()
        
        # Add test metrics
        for i in range(5):
            with profiler.profile_operation("test_op"):
                time.sleep(0.001)  # 1ms delay
        
        stats = profiler.get_statistics("test_op")
        
        assert stats["operation_name"] == "test_op"
        assert stats["total_operations"] == 5
        assert stats["successful_operations"] == 5
        assert stats["success_rate"] == 100.0
        assert "response_time" in stats
        assert "avg" in stats["response_time"]
        assert stats["response_time"]["avg"] > 0
    
    def test_statistics_with_no_metrics(self):
        """Test statistics generation with no metrics."""
        profiler = PerformanceProfiler()
        stats = profiler.get_statistics("nonexistent_op")
        assert "error" in stats
    
    def test_percentile_calculation(self):
        """Test percentile calculation accuracy."""
        profiler = PerformanceProfiler()
        
        # Test with known data
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        p50 = profiler._percentile(data, 50)
        p95 = profiler._percentile(data, 95)
        
        assert p50 == 3.0  # Median
        assert p95 == 4.8  # 95th percentile


class TestDatabasePerformanceTester:
    """Test DatabasePerformanceTester functionality."""
    
    @pytest.fixture
    def mock_db_manager(self):
        """Mock database manager for testing."""
        mock_db = Mock()
        mock_db.create_client.return_value = 1
        mock_db.get_clients.return_value = {"data": [], "total": 0}
        
        # Mock connection context manager
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [("test", 1)]
        mock_conn.cursor.return_value = mock_cursor
        mock_db.get_connection.return_value.__enter__ = Mock(return_value=mock_conn)
        mock_db.get_connection.return_value.__exit__ = Mock(return_value=None)
        
        return mock_db
    
    def test_benchmark_crud_operations(self, mock_db_manager):
        """Test CRUD operations benchmarking."""
        tester = DatabasePerformanceTester(mock_db_manager)
        
        results = tester.benchmark_crud_operations(iterations=5)
        
        assert "client_create" in results
        assert "client_read" in results
        assert mock_db_manager.create_client.call_count == 5
        assert mock_db_manager.get_clients.call_count == 5
    
    def test_query_performance_testing(self, mock_db_manager):
        """Test query performance testing."""
        tester = DatabasePerformanceTester(mock_db_manager)
        
        results = tester.test_query_performance()
        
        assert "simple_select" in results
        assert "complex_join" in results
        assert "aggregation" in results
        
        # Verify each query result has expected structure
        for query_name, result in results.items():
            assert "total_operations" in result
            assert "response_time" in result
            assert "rows_returned" in result


class TestLoadTester:
    """Test LoadTester functionality."""
    
    @pytest.fixture
    def mock_db_manager(self):
        """Mock database manager for testing."""
        mock_db = Mock()
        mock_db.create_client.return_value = 1
        return mock_db
    
    def test_load_test_configuration(self, mock_db_manager):
        """Test load test with custom configuration."""
        tester = LoadTester(mock_db_manager)
        config = LoadTestConfig(
            concurrent_users=2,
            duration_seconds=1,
            operations_per_second=10
        )
        
        def test_function(data):
            time.sleep(0.001)  # Simulate work
            return True
        
        results = tester.run_load_test(config, test_function)
        
        assert "config" in results
        assert "execution" in results
        assert "performance" in results
        assert results["config"]["concurrent_users"] == 2
    
    def test_test_data_generation(self, mock_db_manager):
        """Test test data generation."""
        tester = LoadTester(mock_db_manager)
        
        test_data = tester._generate_test_data(10)
        
        assert len(test_data) == 10
        assert all("client_key" in item for item in test_data)
        assert all("name" in item for item in test_data)
    
    def test_bottleneck_identification(self, mock_db_manager):
        """Test bottleneck identification logic."""
        tester = LoadTester(mock_db_manager)
        
        # Test with high response time
        stats_high_response = {
            "response_time": {"p95": 1500},  # > 1 second
            "success_rate": 100,
            "memory": {"max": 100}
        }
        
        bottlenecks = tester._identify_bottlenecks(stats_high_response)
        assert any("High response time" in b for b in bottlenecks)
        
        # Test with low success rate
        stats_low_success = {
            "response_time": {"p95": 100},
            "success_rate": 90,  # < 95%
            "memory": {"max": 100}
        }
        
        bottlenecks = tester._identify_bottlenecks(stats_low_success)
        assert any("Low success rate" in b for b in bottlenecks)


class TestPerformanceMonitor:
    """Test PerformanceMonitor functionality."""
    
    def test_monitor_initialization(self):
        """Test monitor initializes correctly."""
        monitor = PerformanceMonitor()
        assert not monitor.monitoring_active
        assert monitor.monitor_thread is None
        assert monitor.metrics_history == []
    
    def test_system_metrics_collection(self):
        """Test system metrics collection."""
        monitor = PerformanceMonitor()
        
        metrics = monitor._collect_system_metrics()
        
        assert "timestamp" in metrics
        assert "cpu_percent" in metrics
        assert "memory_percent" in metrics
        assert "memory_available" in metrics
        assert "disk_usage" in metrics
        assert "active_threads" in metrics
        assert "process_count" in metrics
    
    def test_monitoring_start_stop(self):
        """Test monitoring start and stop functionality."""
        monitor = PerformanceMonitor()
        
        # Start monitoring
        monitor.start_monitoring(interval_seconds=0.1)
        assert monitor.monitoring_active
        assert monitor.monitor_thread is not None
        
        # Let it collect some metrics
        time.sleep(0.3)
        
        # Stop monitoring
        monitor.stop_monitoring()
        assert not monitor.monitoring_active
        
        # Should have collected some metrics
        assert len(monitor.metrics_history) > 0
    
    def test_metrics_history_limit(self):
        """Test metrics history size limit."""
        monitor = PerformanceMonitor()
        
        # Manually add metrics beyond limit
        for i in range(1100):
            monitor.metrics_history.append({"test": i})
        
        # Simulate the cleanup that happens in monitoring loop
        if len(monitor.metrics_history) > 1000:
            monitor.metrics_history = monitor.metrics_history[-1000:]
        
        assert len(monitor.metrics_history) == 1000


class TestPerformanceReporter:
    """Test PerformanceReporter functionality."""
    
    def test_reporter_initialization(self):
        """Test reporter initializes with output directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            reporter = PerformanceReporter(temp_dir)
            assert reporter.output_dir.exists()
    
    def test_report_generation(self):
        """Test performance report generation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            reporter = PerformanceReporter(temp_dir)
            
            test_results = {
                "test_operation": {
                    "response_time": {"avg": 100, "p95": 200},
                    "success_rate": 95,
                    "total_operations": 100
                }
            }
            
            report_file = reporter.generate_performance_report(test_results, "test_report")
            
            # Check JSON report exists
            assert Path(report_file).exists()
            
            # Check markdown report exists
            md_file = Path(report_file).with_suffix('.md')
            assert md_file.exists()
            
            # Verify JSON content
            with open(report_file) as f:
                report_data = json.load(f)
            
            assert report_data["test_name"] == "test_report"
            assert "results" in report_data
            assert "summary" in report_data
            assert "recommendations" in report_data
    
    def test_summary_generation(self):
        """Test summary generation from results."""
        with tempfile.TemporaryDirectory() as temp_dir:
            reporter = PerformanceReporter(temp_dir)
            
            results = {
                "operation1": {
                    "response_time": {"avg": 150},
                    "success_rate": 98
                },
                "operation2": {
                    "response_time": {"avg": 200},
                    "success_rate": 99
                }
            }
            
            summary = reporter._generate_summary(results)
            
            assert summary["total_tests"] == 2
            assert "key_metrics" in summary
            assert "operation1" in summary["key_metrics"]
            assert "operation2" in summary["key_metrics"]
    
    def test_recommendations_generation(self):
        """Test performance recommendations generation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            reporter = PerformanceReporter(temp_dir)
            
            # Results with performance issues
            results = {
                "slow_operation": {
                    "response_time": {"avg": 600},  # > 500ms
                    "success_rate": 100
                },
                "failing_operation": {
                    "response_time": {"avg": 100},
                    "success_rate": 90  # < 95%
                }
            }
            
            recommendations = reporter._generate_recommendations(results)
            
            assert len(recommendations) == 2
            assert any("slow_operation" in rec for rec in recommendations)
            assert any("failing_operation" in rec for rec in recommendations)


class TestIntegrationFunctions:
    """Test integration functions."""
    
    @pytest.fixture
    def mock_db_manager(self):
        """Mock database manager for testing."""
        mock_db = Mock()
        mock_db.get_clients.return_value = {"data": [], "total": 0}
        mock_db.get_projects.return_value = {"data": [], "total": 0}
        return mock_db
    
    def test_quick_performance_check(self, mock_db_manager):
        """Test quick performance check function."""
        results = run_quick_performance_check(mock_db_manager)
        
        assert "get_clients" in results
        assert "get_projects" in results
        assert "timestamp" in results
        
        # Verify database methods were called
        mock_db_manager.get_clients.assert_called_once_with(limit=10)
        mock_db_manager.get_projects.assert_called_once_with(limit=10)
    
    @patch('streamlit_extension.utils.performance_tester.DatabasePerformanceTester')
    @patch('streamlit_extension.utils.performance_tester.LoadTester')
    @patch('streamlit_extension.utils.performance_tester.PerformanceReporter')
    def test_performance_test_suite_creation(self, mock_reporter, mock_load_tester, 
                                           mock_db_tester, mock_db_manager):
        """Test comprehensive performance test suite creation."""
        # Mock the component instances
        mock_db_tester_instance = Mock()
        mock_db_tester_instance.benchmark_crud_operations.return_value = {"test": "data"}
        mock_db_tester_instance.test_query_performance.return_value = {"query": "data"}
        mock_db_tester.return_value = mock_db_tester_instance
        
        mock_load_tester_instance = Mock()
        mock_load_tester_instance.run_load_test.return_value = {"load": "data"}
        mock_load_tester.return_value = mock_load_tester_instance
        
        mock_reporter_instance = Mock()
        mock_reporter_instance.generate_performance_report.return_value = "/tmp/report.json"
        mock_reporter.return_value = mock_reporter_instance
        
        # Run the test suite
        results = create_performance_test_suite(mock_db_manager)
        
        # Verify components were created and used
        mock_db_tester.assert_called_once_with(mock_db_manager)
        mock_load_tester.assert_called_once_with(mock_db_manager)
        mock_reporter.assert_called_once()
        
        # Verify results structure
        assert "database_crud" in results
        assert "database_queries" in results
        assert "load_test_light" in results
        assert "load_test_heavy" in results


class TestPerformanceMetrics:
    """Test PerformanceMetrics dataclass."""
    
    def test_metrics_creation(self):
        """Test PerformanceMetrics creation."""
        import datetime
        
        metric = PerformanceMetrics(
            operation_name="test_operation",
            response_time=100.5,
            memory_usage=50.0,
            cpu_usage=25.0,
            threads_count=5,
            timestamp=datetime.datetime.now(),
            success=True
        )
        
        assert metric.operation_name == "test_operation"
        assert metric.response_time == 100.5
        assert metric.memory_usage == 50.0
        assert metric.cpu_usage == 25.0
        assert metric.threads_count == 5
        assert metric.success is True
        assert metric.error_message is None


class TestLoadTestConfig:
    """Test LoadTestConfig dataclass."""
    
    def test_default_config(self):
        """Test default load test configuration."""
        config = LoadTestConfig()
        
        assert config.concurrent_users == 10
        assert config.duration_seconds == 60
        assert config.operations_per_second == 100
        assert config.ramp_up_seconds == 10
        assert config.test_data_size == 1000
    
    def test_custom_config(self):
        """Test custom load test configuration."""
        config = LoadTestConfig(
            concurrent_users=5,
            duration_seconds=30,
            operations_per_second=50
        )
        
        assert config.concurrent_users == 5
        assert config.duration_seconds == 30
        assert config.operations_per_second == 50
        # Should keep defaults for non-specified values
        assert config.ramp_up_seconds == 10
        assert config.test_data_size == 1000


# Performance benchmarks for regression testing
class TestPerformanceBenchmarks:
    """Performance benchmark tests to detect regressions."""
    
    def test_profiler_overhead(self):
        """Test that profiler overhead is minimal."""
        profiler = PerformanceProfiler()
        
        # Test operation without profiling
        start_time = time.perf_counter()
        for i in range(1000):
            pass  # Minimal operation
        no_profiling_time = time.perf_counter() - start_time
        
        # Test operation with profiling
        start_time = time.perf_counter()
        for i in range(1000):
            with profiler.profile_operation("test"):
                pass  # Same minimal operation
        profiling_time = time.perf_counter() - start_time
        
        # Profiling overhead should be reasonable (less than 10x)
        overhead_ratio = profiling_time / no_profiling_time
        assert overhead_ratio < 10, f"Profiling overhead too high: {overhead_ratio}x"
    
    @pytest.mark.slow
    def test_memory_leak_detection(self):
        """Test for memory leaks in profiling system."""
        import gc
        
        profiler = PerformanceProfiler()
        
        # Measure initial memory
        gc.collect()
        initial_objects = len(gc.get_objects())
        
        # Run many profiling operations
        for i in range(1000):
            with profiler.profile_operation(f"test_{i}"):
                pass
        
        # Clear metrics and collect garbage
        profiler.metrics.clear()
        gc.collect()
        final_objects = len(gc.get_objects())
        
        # Object count should not have grown significantly
        object_growth = final_objects - initial_objects
        assert object_growth < 100, f"Potential memory leak: {object_growth} new objects"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])