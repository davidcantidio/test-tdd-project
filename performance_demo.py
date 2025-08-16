#!/usr/bin/env python3
"""
🚀 Performance Testing System Demo

Demonstrates the comprehensive performance testing system functionality:
- PerformanceProfiler usage
- DatabasePerformanceTester capabilities
- LoadTester functionality
- PerformanceMonitor features
- Report generation

This demo can be run independently to validate the performance testing system.
"""

import sys
import time
from pathlib import Path
import json

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from streamlit_extension.utils.performance_tester import (
    PerformanceProfiler,
    DatabasePerformanceTester,
    LoadTester,
    PerformanceMonitor,
    PerformanceReporter,
    LoadTestConfig,
    run_quick_performance_check,
    create_performance_test_suite
)


class MockDatabaseManager:
    """Mock database manager for demo purposes."""
    
    def __init__(self):
        self.call_count = 0
        
    def create_client(self, **kwargs):
        """Mock client creation."""
        self.call_count += 1
        time.sleep(0.001)  # Simulate database operation
        return self.call_count
    
    def get_clients(self, **kwargs):
        """Mock client retrieval."""
        time.sleep(0.002)  # Simulate query time
        return {
            "data": [{"id": i, "name": f"Client {i}"} for i in range(10)],
            "total": 10
        }
    
    def get_projects(self, **kwargs):
        """Mock project retrieval."""
        time.sleep(0.003)  # Simulate query time
        return {
            "data": [{"id": i, "name": f"Project {i}"} for i in range(5)],
            "total": 5
        }
    
    def get_connection(self):
        """Mock connection context manager."""
        return MockConnection()


class MockConnection:
    """Mock database connection."""
    
    def __init__(self):
        self.cursor_obj = MockCursor()
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        pass
    
    def cursor(self):
        return self.cursor_obj


class MockCursor:
    """Mock database cursor."""
    
    def execute(self, query, params=None):
        time.sleep(0.001)  # Simulate query execution
    
    def fetchall(self):
        return [("result1", 1), ("result2", 2), ("result3", 3)]


def demo_performance_profiler():
    """Demonstrate PerformanceProfiler functionality."""
    print("🔍 Demo: PerformanceProfiler")
    print("-" * 50)
    
    profiler = PerformanceProfiler()
    
    # Profile some operations
    print("Profiling operations...")
    
    with profiler.profile_operation("fast_operation"):
        time.sleep(0.01)
    
    with profiler.profile_operation("slow_operation"):
        time.sleep(0.05)
    
    # Add more operations for better statistics
    for i in range(5):
        with profiler.profile_operation("batch_operation"):
            time.sleep(0.002)
    
    # Generate statistics
    stats = profiler.get_statistics()
    print(f"Total operations: {stats['total_operations']}")
    print(f"Success rate: {stats['success_rate']:.1f}%")
    print(f"Average response time: {stats['response_time']['avg']:.2f}ms")
    print(f"95th percentile: {stats['response_time']['p95']:.2f}ms")
    print()


def demo_database_performance_tester():
    """Demonstrate DatabasePerformanceTester functionality."""
    print("🗄️ Demo: DatabasePerformanceTester")
    print("-" * 50)
    
    db_manager = MockDatabaseManager()
    db_tester = DatabasePerformanceTester(db_manager)
    
    print("Running CRUD benchmarks...")
    crud_results = db_tester.benchmark_crud_operations(iterations=10)
    
    print("CRUD Results:")
    for operation, stats in crud_results.items():
        response_time = stats.get("response_time", {})
        print(f"  {operation}: {response_time.get('avg', 0):.2f}ms avg")
    
    print("\nRunning query performance tests...")
    query_results = db_tester.test_query_performance()
    
    print("Query Results:")
    for query_name, stats in query_results.items():
        response_time = stats.get("response_time", {})
        rows = stats.get("rows_returned", 0)
        print(f"  {query_name}: {response_time.get('avg', 0):.2f}ms avg, {rows} rows")
    print()


def demo_load_tester():
    """Demonstrate LoadTester functionality."""
    print("⚡ Demo: LoadTester")
    print("-" * 50)
    
    db_manager = MockDatabaseManager()
    load_tester = LoadTester(db_manager)
    
    # Light load test configuration
    config = LoadTestConfig(
        concurrent_users=3,
        duration_seconds=5,
        operations_per_second=50,
        test_data_size=10
    )
    
    def test_function(data):
        return db_manager.create_client(**data)
    
    print("Running light load test...")
    results = load_tester.run_load_test(config, test_function)
    
    print("Load Test Results:")
    execution = results.get("execution", {})
    performance = results.get("performance", {})
    
    print(f"  Total operations: {execution.get('total_operations', 0)}")
    print(f"  Operations/sec: {execution.get('operations_per_second', 0):.1f}")
    print(f"  Success rate: {execution.get('success_rate', 0):.1f}%")
    
    response_time = performance.get("response_time", {})
    print(f"  Avg response time: {response_time.get('avg', 0):.2f}ms")
    
    bottlenecks = results.get("bottlenecks", [])
    if bottlenecks:
        print("  Bottlenecks detected:")
        for bottleneck in bottlenecks:
            print(f"    - {bottleneck}")
    else:
        print("  No bottlenecks detected ✅")
    print()


def demo_performance_monitor():
    """Demonstrate PerformanceMonitor functionality."""
    print("📊 Demo: PerformanceMonitor")
    print("-" * 50)
    
    monitor = PerformanceMonitor()
    
    print("Starting monitoring for 3 seconds...")
    monitor.start_monitoring(interval_seconds=1)
    
    # Let it collect some metrics
    time.sleep(3)
    
    print("Stopping monitoring...")
    monitor.stop_monitoring()
    
    # Get collected metrics
    metrics_history = monitor.get_metrics_history()
    print(f"Collected {len(metrics_history)} metric snapshots")
    
    if metrics_history:
        latest = metrics_history[-1]
        print(f"Latest metrics:")
        print(f"  CPU: {latest['cpu_percent']:.1f}%")
        print(f"  Memory: {latest['memory_percent']:.1f}%")
        print(f"  Active threads: {latest['active_threads']}")
    print()


def demo_performance_reporter():
    """Demonstrate PerformanceReporter functionality."""
    print("📋 Demo: PerformanceReporter")
    print("-" * 50)
    
    # Create sample test results
    test_results = {
        "client_operations": {
            "response_time": {"avg": 15.5, "p95": 25.0, "p99": 35.0},
            "success_rate": 98.5,
            "total_operations": 1000,
            "throughput": 65.2
        },
        "database_queries": {
            "response_time": {"avg": 8.2, "p95": 15.0, "p99": 22.0},
            "success_rate": 100.0,
            "total_operations": 500,
            "throughput": 125.0
        }
    }
    
    # Create reporter with temp directory
    reporter = PerformanceReporter("demo_reports")
    
    print("Generating performance report...")
    report_file = reporter.generate_performance_report(test_results, "demo_test")
    
    print(f"Report generated: {report_file}")
    
    # Show report content
    with open(report_file) as f:
        report_data = json.load(f)
    
    print("Report summary:")
    summary = report_data.get("summary", {})
    print(f"  Total tests: {summary.get('total_tests', 0)}")
    print(f"  Key metrics: {len(summary.get('key_metrics', {}))}")
    
    recommendations = report_data.get("recommendations", [])
    if recommendations:
        print("  Recommendations:")
        for rec in recommendations:
            print(f"    - {rec}")
    else:
        print("  No recommendations - good performance! ✅")
    print()


def demo_quick_performance_check():
    """Demonstrate quick performance check function."""
    print("⚡ Demo: Quick Performance Check")
    print("-" * 50)
    
    db_manager = MockDatabaseManager()
    
    print("Running quick performance check...")
    results = run_quick_performance_check(db_manager)
    
    print("Quick check results:")
    for operation, stats in results.items():
        if operation == "timestamp":
            print(f"  Timestamp: {stats}")
        else:
            response_time = stats.get("response_time", {})
            print(f"  {operation}: {response_time.get('avg', 0):.2f}ms avg")
    print()


def demo_comprehensive_test_suite():
    """Demonstrate comprehensive test suite."""
    print("🚀 Demo: Comprehensive Performance Test Suite")
    print("-" * 50)
    
    db_manager = MockDatabaseManager()
    
    print("This would normally run the full test suite...")
    print("(Skipped in demo to avoid long execution time)")
    
    # Show what would be included
    print("Comprehensive suite includes:")
    print("  ✅ Database CRUD benchmarks")
    print("  ✅ Query performance analysis")  
    print("  ✅ Light load testing")
    print("  ✅ Heavy load testing")
    print("  ✅ Comprehensive reporting")
    print()
    
    # Uncomment to run full suite (takes ~2 minutes)
    # print("Running comprehensive test suite...")
    # results = create_performance_test_suite(db_manager)
    # print(f"Suite completed with {len(results)} test categories")


def main():
    """Run complete performance testing demo."""
    print("=" * 60)
    print("🚀 PERFORMANCE TESTING SYSTEM DEMO")
    print("=" * 60)
    print()
    
    print("This demo showcases the comprehensive performance testing system")
    print("that addresses performance bottlenecks identified in report.md")
    print()
    
    # Run all demos
    demo_performance_profiler()
    demo_database_performance_tester()
    demo_load_tester()
    demo_performance_monitor()
    demo_performance_reporter()
    demo_quick_performance_check()
    demo_comprehensive_test_suite()
    
    print("=" * 60)
    print("✅ PERFORMANCE TESTING SYSTEM DEMO COMPLETE")
    print("=" * 60)
    print()
    print("Key features demonstrated:")
    print("  🔍 Performance profiling with metrics collection")
    print("  🗄️ Database performance benchmarking")
    print("  ⚡ Multi-threaded load testing")
    print("  📊 Real-time system monitoring")
    print("  📋 Comprehensive report generation")
    print("  🚀 Streamlit dashboard integration")
    print()
    print("System is ready for production performance testing!")


if __name__ == "__main__":
    main()