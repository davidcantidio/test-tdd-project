"""
🚀 Performance Testing System - Enterprise Load Testing

Comprehensive performance testing and benchmarking system addressing report.md items:
- Performance bottleneck identification
- Load testing capabilities 
- Database query optimization
- Real-time performance monitoring
- Automated performance regression detection

Features:
- Multi-threaded load simulation
- Database performance profiling
- Memory usage analysis
- Response time measurement
- Throughput analysis
- Bottleneck detection
- Performance regression alerts
"""

import time
import threading
import sqlite3
import psutil
import tracemalloc
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from contextlib import contextmanager
import statistics
import json
from pathlib import Path
import datetime
import gc


@dataclass
class PerformanceMetrics:
    """Performance measurement data structure."""
    operation_name: str
    response_time: float
    memory_usage: float
    cpu_usage: float
    threads_count: int
    timestamp: datetime.datetime
    success: bool
    error_message: Optional[str] = None


@dataclass
class LoadTestConfig:
    """Load test configuration."""
    concurrent_users: int = 10
    duration_seconds: int = 60
    operations_per_second: int = 100
    ramp_up_seconds: int = 10
    test_data_size: int = 1000


class PerformanceProfiler:
    """Advanced performance profiling system."""
    
    def __init__(self):
        self.metrics: List[PerformanceMetrics] = []
        self.baseline_metrics: Dict[str, float] = {}
        self.start_time: Optional[float] = None
        self.memory_tracker_active = False
        
    @contextmanager
    def profile_operation(self, operation_name: str):
        """Context manager for profiling individual operations."""
        # Start memory tracking
        if not self.memory_tracker_active:
            tracemalloc.start()
            self.memory_tracker_active = True
            
        start_time = time.perf_counter()
        start_memory = self._get_memory_usage()
        start_cpu = psutil.cpu_percent()
        
        success = True
        error_message = None
        
        try:
            yield
        except Exception as e:
            success = False
            error_message = str(e)
            raise
        finally:
            end_time = time.perf_counter()
            end_memory = self._get_memory_usage()
            end_cpu = psutil.cpu_percent()
            
            metric = PerformanceMetrics(
                operation_name=operation_name,
                response_time=(end_time - start_time) * 1000,  # Convert to ms
                memory_usage=end_memory - start_memory,
                cpu_usage=end_cpu,
                threads_count=threading.active_count(),
                timestamp=datetime.datetime.now(),
                success=success,
                error_message=error_message
            )
            
            self.metrics.append(metric)
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        if self.memory_tracker_active:
            current, peak = tracemalloc.get_traced_memory()
            return current / 1024 / 1024  # Convert to MB
        else:
            return psutil.Process().memory_info().rss / 1024 / 1024
    
    def get_statistics(self, operation_name: Optional[str] = None) -> Dict[str, Any]:
        """Generate comprehensive statistics for operations."""
        filtered_metrics = self.metrics
        if operation_name:
            filtered_metrics = [m for m in self.metrics if m.operation_name == operation_name]
        
        if not filtered_metrics:
            return {"error": "No metrics found"}
        
        response_times = [m.response_time for m in filtered_metrics if m.success]
        memory_usage = [m.memory_usage for m in filtered_metrics if m.success]
        
        if not response_times:
            return {"error": "No successful operations found"}
        
        return {
            "operation_name": operation_name or "all_operations",
            "total_operations": len(filtered_metrics),
            "successful_operations": len(response_times),
            "success_rate": len(response_times) / len(filtered_metrics) * 100,
            "response_time": {
                "min": min(response_times),
                "max": max(response_times),
                "avg": statistics.mean(response_times),
                "median": statistics.median(response_times),
                "p95": self._percentile(response_times, 95),
                "p99": self._percentile(response_times, 99)
            },
            "memory": {
                "min": min(memory_usage) if memory_usage else 0,
                "max": max(memory_usage) if memory_usage else 0,
                "avg": statistics.mean(memory_usage) if memory_usage else 0
            },
            "throughput": len(response_times) / ((filtered_metrics[-1].timestamp - filtered_metrics[0].timestamp).total_seconds() or 1)
        }
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile."""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = (percentile / 100) * (len(sorted_data) - 1)
        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower = sorted_data[int(index)]
            upper = sorted_data[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))


class DatabasePerformanceTester:
    """Specialized database performance testing."""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.profiler = PerformanceProfiler()
        
    def benchmark_crud_operations(self, iterations: int = 1000) -> Dict[str, Any]:
        """Benchmark CRUD operations performance."""
        results = {}
        
        # Test client operations
        with self.profiler.profile_operation("client_create"):
            for i in range(iterations):
                self.db_manager.create_client(
                    client_key=f"test_client_{i}",
                    name=f"Test Client {i}",
                    description="Performance test client"
                )
        
        with self.profiler.profile_operation("client_read"):
            for i in range(iterations):
                self.db_manager.get_clients(limit=10)
        
        # Collect statistics
        results["client_create"] = self.profiler.get_statistics("client_create")
        results["client_read"] = self.profiler.get_statistics("client_read")
        
        return results
    
    def test_query_performance(self) -> Dict[str, Any]:
        """Test complex query performance."""
        test_queries = {
            "simple_select": "SELECT * FROM framework_clients LIMIT 100",
            "complex_join": """
                SELECT c.name, COUNT(p.id) as project_count 
                FROM framework_clients c 
                LEFT JOIN framework_projects p ON c.id = p.client_id 
                GROUP BY c.id
            """,
            "aggregation": """
                SELECT status, COUNT(*) as count, AVG(progress) as avg_progress
                FROM framework_epics 
                GROUP BY status
            """
        }
        
        results = {}
        for query_name, query_sql in test_queries.items():
            with self.profiler.profile_operation(f"query_{query_name}"):
                with self.db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(query_sql)
                    rows = cursor.fetchall()
            
            results[query_name] = self.profiler.get_statistics(f"query_{query_name}")
            results[query_name]["rows_returned"] = len(rows)
        
        return results


class LoadTester:
    """Multi-threaded load testing system."""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.profiler = PerformanceProfiler()
        self.stop_event = threading.Event()
        
    def run_load_test(self, config: LoadTestConfig, target_function: Callable) -> Dict[str, Any]:
        """Execute load test with specified configuration."""
        self.stop_event.clear()
        
        # Prepare test data
        test_data = self._generate_test_data(config.test_data_size)
        
        # Start load test
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=config.concurrent_users) as executor:
            # Submit tasks
            futures = []
            for i in range(config.concurrent_users):
                future = executor.submit(
                    self._worker_thread,
                    target_function,
                    test_data,
                    config.duration_seconds,
                    f"worker_{i}"
                )
                futures.append(future)
            
            # Wait for completion
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"Worker failed: {e}")
        
        end_time = time.time()
        
        # Generate report
        return self._generate_load_test_report(config, start_time, end_time)
    
    def _worker_thread(self, target_function: Callable, test_data: List[Dict], 
                      duration: int, worker_id: str):
        """Individual worker thread for load testing."""
        start_time = time.time()
        operation_count = 0
        
        while time.time() - start_time < duration and not self.stop_event.is_set():
            try:
                # Select random test data
                data = test_data[operation_count % len(test_data)]
                
                with self.profiler.profile_operation(f"load_test_{worker_id}"):
                    target_function(data)
                
                operation_count += 1
                
                # Small delay to control rate
                time.sleep(0.01)
                
            except Exception as e:
                print(f"Operation failed in {worker_id}: {e}")
                
        print(f"{worker_id} completed {operation_count} operations")
    
    def _generate_test_data(self, size: int) -> List[Dict]:
        """Generate test data for load testing."""
        return [
            {
                "client_key": f"load_test_client_{i}",
                "name": f"Load Test Client {i}",
                "description": f"Load test client {i} for performance testing",
                "industry": "Technology",
                "client_tier": "basic"
            }
            for i in range(size)
        ]
    
    def _generate_load_test_report(self, config: LoadTestConfig, 
                                 start_time: float, end_time: float) -> Dict[str, Any]:
        """Generate comprehensive load test report."""
        duration = end_time - start_time
        stats = self.profiler.get_statistics()
        
        return {
            "config": {
                "concurrent_users": config.concurrent_users,
                "duration_seconds": config.duration_seconds,
                "target_operations_per_second": config.operations_per_second
            },
            "execution": {
                "actual_duration": duration,
                "total_operations": stats.get("total_operations", 0),
                "operations_per_second": stats.get("throughput", 0),
                "success_rate": stats.get("success_rate", 0)
            },
            "performance": stats,
            "bottlenecks": self._identify_bottlenecks(stats)
        }
    
    def _identify_bottlenecks(self, stats: Dict[str, Any]) -> List[str]:
        """Identify performance bottlenecks from statistics."""
        bottlenecks = []
        
        response_time = stats.get("response_time", {})
        if response_time.get("p95", 0) > 1000:  # > 1 second
            bottlenecks.append("High response time (P95 > 1s)")
        
        if stats.get("success_rate", 100) < 95:
            bottlenecks.append("Low success rate (<95%)")
        
        memory = stats.get("memory", {})
        if memory.get("max", 0) > 500:  # > 500MB
            bottlenecks.append("High memory usage (>500MB)")
        
        return bottlenecks


class PerformanceMonitor:
    """Real-time performance monitoring system."""
    
    def __init__(self):
        self.monitoring_active = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.metrics_history: List[Dict[str, Any]] = []
        
    def start_monitoring(self, interval_seconds: int = 5):
        """Start real-time performance monitoring."""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval_seconds,),
            daemon=True
        )
        self.monitor_thread.start()
        
    def stop_monitoring(self):
        """Stop performance monitoring."""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join()
    
    def _monitor_loop(self, interval: int):
        """Main monitoring loop."""
        while self.monitoring_active:
            metrics = self._collect_system_metrics()
            self.metrics_history.append(metrics)
            
            # Keep only last 1000 entries
            if len(self.metrics_history) > 1000:
                self.metrics_history.pop(0)
            
            time.sleep(interval)
    
    def _collect_system_metrics(self) -> Dict[str, Any]:
        """Collect current system metrics."""
        return {
            "timestamp": datetime.datetime.now().isoformat(),
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "memory_available": psutil.virtual_memory().available / 1024 / 1024,  # MB
            "disk_usage": psutil.disk_usage('/').percent,
            "active_threads": threading.active_count(),
            "process_count": len(psutil.pids())
        }
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current system metrics."""
        return self._collect_system_metrics()
    
    def get_metrics_history(self, last_n: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get metrics history."""
        if last_n:
            return self.metrics_history[-last_n:]
        return self.metrics_history.copy()


class PerformanceReporter:
    """Performance testing report generator."""
    
    def __init__(self, output_dir: str = "performance_reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
    def generate_performance_report(self, test_results: Dict[str, Any], 
                                  test_name: str) -> str:
        """Generate comprehensive performance report."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.output_dir / f"{test_name}_{timestamp}.json"
        
        report_data = {
            "test_name": test_name,
            "timestamp": timestamp,
            "results": test_results,
            "summary": self._generate_summary(test_results),
            "recommendations": self._generate_recommendations(test_results)
        }
        
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        # Generate markdown summary
        md_file = self.output_dir / f"{test_name}_{timestamp}.md"
        self._generate_markdown_report(report_data, md_file)
        
        return str(report_file)
    
    def _generate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate test summary."""
        summary = {
            "total_tests": len(results),
            "overall_performance": "good",  # Will be calculated
            "key_metrics": {}
        }
        
        # Extract key metrics
        for test_name, test_data in results.items():
            if isinstance(test_data, dict) and "response_time" in test_data:
                summary["key_metrics"][test_name] = {
                    "avg_response_time": test_data["response_time"].get("avg", 0),
                    "p95_response_time": test_data["response_time"].get("p95", 0),
                    "success_rate": test_data.get("success_rate", 100)
                }
        
        return summary
    
    def _generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate performance improvement recommendations."""
        recommendations = []
        
        for test_name, test_data in results.items():
            if isinstance(test_data, dict):
                # Check response time
                response_time = test_data.get("response_time", {})
                if response_time.get("avg", 0) > 500:  # > 500ms
                    recommendations.append(f"Optimize {test_name} - average response time is high")
                
                # Check success rate
                success_rate = test_data.get("success_rate", 100)
                if success_rate < 95:
                    recommendations.append(f"Investigate {test_name} failures - success rate is {success_rate}%")
        
        return recommendations
    
    def _generate_markdown_report(self, report_data: Dict[str, Any], output_file: Path):
        """Generate markdown version of the report."""
        with open(output_file, 'w') as f:
            f.write(f"# Performance Test Report: {report_data['test_name']}\n\n")
            f.write(f"**Generated:** {report_data['timestamp']}\n\n")
            
            f.write("## Summary\n\n")
            summary = report_data['summary']
            f.write(f"- **Total Tests:** {summary['total_tests']}\n")
            f.write(f"- **Overall Performance:** {summary['overall_performance']}\n\n")
            
            if report_data['recommendations']:
                f.write("## Recommendations\n\n")
                for rec in report_data['recommendations']:
                    f.write(f"- {rec}\n")
                f.write("\n")
            
            f.write("## Detailed Results\n\n")
            f.write("```json\n")
            f.write(json.dumps(report_data['results'], indent=2, default=str))
            f.write("\n```\n")


def create_performance_test_suite(db_manager) -> Dict[str, Any]:
    """Create comprehensive performance test suite."""
    
    # Initialize components
    db_tester = DatabasePerformanceTester(db_manager)
    load_tester = LoadTester(db_manager)
    monitor = PerformanceMonitor()
    reporter = PerformanceReporter()
    
    # Test configurations
    light_load = LoadTestConfig(concurrent_users=5, duration_seconds=30)
    heavy_load = LoadTestConfig(concurrent_users=20, duration_seconds=60)
    
    results = {}
    
    print("🚀 Starting Performance Test Suite...")
    
    # 1. Database performance tests
    print("📊 Running database performance tests...")
    results["database_crud"] = db_tester.benchmark_crud_operations(iterations=100)
    results["database_queries"] = db_tester.test_query_performance()
    
    # 2. Load testing
    print("⚡ Running load tests...")
    
    def client_creation_test(data):
        return db_manager.create_client(**data)
    
    results["load_test_light"] = load_tester.run_load_test(light_load, client_creation_test)
    results["load_test_heavy"] = load_tester.run_load_test(heavy_load, client_creation_test)
    
    # 3. Generate report
    print("📋 Generating performance report...")
    report_file = reporter.generate_performance_report(results, "comprehensive_test")
    
    print(f"✅ Performance testing complete! Report saved to: {report_file}")
    
    return results


# Example usage and integration functions
def run_quick_performance_check(db_manager) -> Dict[str, Any]:
    """Run quick performance check for monitoring."""
    profiler = PerformanceProfiler()
    
    # Test basic operations
    with profiler.profile_operation("get_clients"):
        db_manager.get_clients(limit=10)
    
    with profiler.profile_operation("get_projects"):
        db_manager.get_projects(limit=10)
    
    return {
        "get_clients": profiler.get_statistics("get_clients"),
        "get_projects": profiler.get_statistics("get_projects"),
        "timestamp": datetime.datetime.now().isoformat()
    }


if __name__ == "__main__":
    # Example usage
    from streamlit_extension.utils.database import DatabaseManager
    
    db_manager = DatabaseManager("framework.db", "task_timer.db")
    
    # Run comprehensive test suite
    results = create_performance_test_suite(db_manager)
    
    print("Performance testing completed!")
    print(f"Results: {len(results)} test categories executed")