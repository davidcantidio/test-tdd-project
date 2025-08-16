# 🤖 PROMPT GG: STRESS TESTING SUITE

## 🎯 OBJECTIVE
Create comprehensive stress and endurance testing suite to address report.md requirement: "Load/performance testing previously absent; basic load, stress and endurance suites now in place" in the Test Coverage Report.

## 📁 FILE TO CREATE

### tests/performance/test_stress_suite.py (NEW FILE)

```python
#!/usr/bin/env python3
"""
Comprehensive Stress and Endurance Testing Suite
Tests system behavior under extreme load and extended operation periods.
"""

import pytest
import time
import threading
import random
import sqlite3
import concurrent.futures
import psutil
import gc
from datetime import datetime, timedelta
from typing import List, Dict, Any, Callable
from unittest.mock import patch
from dataclasses import dataclass

from streamlit_extension.utils.database import DatabaseManager
from duration_system.duration_calculator import DurationCalculator
from duration_system.duration_formatter import DurationFormatter


@dataclass
class StressTestResult:
    """Results from stress test execution."""
    test_name: str
    duration_seconds: float
    operations_completed: int
    operations_per_second: float
    errors_count: int
    error_rate: float
    memory_peak_mb: float
    cpu_peak_percent: float
    success: bool
    error_details: List[str]


class StressTestMonitor:
    """Monitor system resources during stress tests."""
    
    def __init__(self):
        self.monitoring = False
        self.memory_samples = []
        self.cpu_samples = []
        self.start_time = None
        
    def start_monitoring(self):
        """Start resource monitoring."""
        self.monitoring = True
        self.memory_samples = []
        self.cpu_samples = []
        self.start_time = time.time()
        
        def monitor():
            while self.monitoring:
                try:
                    memory_mb = psutil.virtual_memory().used / (1024 * 1024)
                    cpu_percent = psutil.cpu_percent(interval=0.1)
                    
                    self.memory_samples.append(memory_mb)
                    self.cpu_samples.append(cpu_percent)
                    
                    time.sleep(0.5)  # Sample every 500ms
                except:
                    break
                    
        self.monitor_thread = threading.Thread(target=monitor, daemon=True)
        self.monitor_thread.start()
        
    def stop_monitoring(self) -> Dict[str, float]:
        """Stop monitoring and return statistics."""
        self.monitoring = False
        
        if self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=1.0)
            
        return {
            'peak_memory_mb': max(self.memory_samples) if self.memory_samples else 0,
            'avg_memory_mb': sum(self.memory_samples) / len(self.memory_samples) if self.memory_samples else 0,
            'peak_cpu_percent': max(self.cpu_samples) if self.cpu_samples else 0,
            'avg_cpu_percent': sum(self.cpu_samples) / len(self.cpu_samples) if self.cpu_samples else 0,
            'duration_seconds': time.time() - self.start_time if self.start_time else 0
        }


class DatabaseStressTester:
    """Stress testing for database operations."""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        
    def test_concurrent_writes(self, num_threads: int = 10, operations_per_thread: int = 100) -> StressTestResult:
        """Test concurrent write operations."""
        errors = []
        operations_completed = 0
        monitor = StressTestMonitor()
        
        def write_operations():
            nonlocal operations_completed
            for i in range(operations_per_thread):
                try:
                    # Create test epic
                    epic_data = {
                        'title': f'Stress Test Epic {threading.current_thread().ident}_{i}',
                        'description': f'Created during stress test at {datetime.now()}',
                        'client_id': 1,  # Assuming client 1 exists
                        'points_value': random.randint(10, 100)
                    }
                    
                    epic_id = self.db_manager.create_epic(epic_data)
                    if epic_id:
                        operations_completed += 1
                        
                        # Create tasks for the epic
                        for j in range(3):
                            task_data = {
                                'title': f'Stress Task {i}_{j}',
                                'epic_id': epic_id,
                                'tdd_phase': random.choice(['red', 'green', 'refactor'])
                            }
                            self.db_manager.create_task(task_data)
                            operations_completed += 1
                            
                except Exception as e:
                    errors.append(str(e))
                    
                # Small delay to prevent overwhelming
                time.sleep(0.01)
        
        # Start monitoring
        monitor.start_monitoring()
        start_time = time.time()
        
        # Execute concurrent operations
        threads = []
        for _ in range(num_threads):
            thread = threading.Thread(target=write_operations)
            threads.append(thread)
            thread.start()
            
        # Wait for completion
        for thread in threads:
            thread.join()
            
        end_time = time.time()
        duration = end_time - start_time
        
        # Stop monitoring
        stats = monitor.stop_monitoring()
        
        # Calculate results
        total_operations = num_threads * operations_per_thread * 4  # 1 epic + 3 tasks
        error_rate = len(errors) / total_operations if total_operations > 0 else 0
        ops_per_second = operations_completed / duration if duration > 0 else 0
        
        return StressTestResult(
            test_name="concurrent_writes",
            duration_seconds=duration,
            operations_completed=operations_completed,
            operations_per_second=ops_per_second,
            errors_count=len(errors),
            error_rate=error_rate,
            memory_peak_mb=stats['peak_memory_mb'],
            cpu_peak_percent=stats['peak_cpu_percent'],
            success=error_rate < 0.1,  # Success if error rate < 10%
            error_details=errors[:10]  # Keep first 10 errors
        )
        
    def test_read_heavy_load(self, num_threads: int = 20, queries_per_thread: int = 500) -> StressTestResult:
        """Test heavy read load on database."""
        errors = []
        operations_completed = 0
        monitor = StressTestMonitor()
        
        def read_operations():
            nonlocal operations_completed
            for i in range(queries_per_thread):
                try:
                    # Mix of different read operations
                    operation_type = random.choice(['epics', 'tasks', 'analytics', 'clients'])
                    
                    if operation_type == 'epics':
                        self.db_manager.get_epics()
                    elif operation_type == 'tasks':
                        self.db_manager.get_tasks()
                    elif operation_type == 'analytics':
                        # Assuming we have some epics
                        epics = self.db_manager.get_epics()
                        if epics:
                            epic_id = epics[0]['id']
                            self.db_manager.get_epic_analytics(epic_id)
                    elif operation_type == 'clients':
                        self.db_manager.get_clients()
                        
                    operations_completed += 1
                    
                except Exception as e:
                    errors.append(str(e))
        
        # Start monitoring
        monitor.start_monitoring()
        start_time = time.time()
        
        # Execute concurrent reads
        threads = []
        for _ in range(num_threads):
            thread = threading.Thread(target=read_operations)
            threads.append(thread)
            thread.start()
            
        # Wait for completion
        for thread in threads:
            thread.join()
            
        end_time = time.time()
        duration = end_time - start_time
        
        # Stop monitoring
        stats = monitor.stop_monitoring()
        
        # Calculate results
        total_operations = num_threads * queries_per_thread
        error_rate = len(errors) / total_operations if total_operations > 0 else 0
        ops_per_second = operations_completed / duration if duration > 0 else 0
        
        return StressTestResult(
            test_name="read_heavy_load",
            duration_seconds=duration,
            operations_completed=operations_completed,
            operations_per_second=ops_per_second,
            errors_count=len(errors),
            error_rate=error_rate,
            memory_peak_mb=stats['peak_memory_mb'],
            cpu_peak_percent=stats['peak_cpu_percent'],
            success=error_rate < 0.05,  # Success if error rate < 5%
            error_details=errors[:10]
        )
        
    def test_connection_pool_stress(self, num_connections: int = 50, operations_per_connection: int = 50) -> StressTestResult:
        """Test connection pool under stress."""
        errors = []
        operations_completed = 0
        monitor = StressTestMonitor()
        
        def connection_operations():
            nonlocal operations_completed
            try:
                # Create new DB manager instance to test connection pooling
                local_db = DatabaseManager()
                
                for i in range(operations_per_connection):
                    try:
                        # Mix of operations that require connections
                        operations = [
                            lambda: local_db.get_health_check(),
                            lambda: local_db.get_epics(),
                            lambda: local_db.get_clients()
                        ]
                        
                        operation = random.choice(operations)
                        operation()
                        operations_completed += 1
                        
                        # Small delay
                        time.sleep(0.001)
                        
                    except Exception as e:
                        errors.append(str(e))
                        
            finally:
                # Ensure connection is closed
                try:
                    local_db.close_connections()
                except:
                    pass
        
        # Start monitoring
        monitor.start_monitoring()
        start_time = time.time()
        
        # Execute with many connections
        threads = []
        for _ in range(num_connections):
            thread = threading.Thread(target=connection_operations)
            threads.append(thread)
            thread.start()
            
        # Wait for completion
        for thread in threads:
            thread.join()
            
        end_time = time.time()
        duration = end_time - start_time
        
        # Stop monitoring
        stats = monitor.stop_monitoring()
        
        # Calculate results
        total_operations = num_connections * operations_per_connection
        error_rate = len(errors) / total_operations if total_operations > 0 else 0
        ops_per_second = operations_completed / duration if duration > 0 else 0
        
        return StressTestResult(
            test_name="connection_pool_stress",
            duration_seconds=duration,
            operations_completed=operations_completed,
            operations_per_second=ops_per_second,
            errors_count=len(errors),
            error_rate=error_rate,
            memory_peak_mb=stats['peak_memory_mb'],
            cpu_peak_percent=stats['peak_cpu_percent'],
            success=error_rate < 0.02,  # Success if error rate < 2%
            error_details=errors[:10]
        )


class MemoryStressTester:
    """Memory stress testing."""
    
    def test_memory_leak_detection(self, iterations: int = 1000) -> StressTestResult:
        """Test for memory leaks in duration calculations."""
        errors = []
        operations_completed = 0
        monitor = StressTestMonitor()
        
        monitor.start_monitoring()
        start_time = time.time()
        
        calculator = DurationCalculator()
        formatter = DurationFormatter()
        
        initial_memory = psutil.virtual_memory().used / (1024 * 1024)
        
        try:
            for i in range(iterations):
                try:
                    # Perform memory-intensive operations
                    duration_text = f"{random.randint(1, 100)} days {random.randint(1, 23)} hours"
                    
                    # Parse duration
                    result = calculator.parse_duration_text(duration_text)
                    
                    # Format duration
                    if result and result.total_duration_hours:
                        formatted = formatter.format_duration(result.total_duration_hours)
                        
                    # Create large temporary data structures
                    large_data = [random.random() for _ in range(1000)]
                    del large_data
                    
                    operations_completed += 1
                    
                    # Force garbage collection periodically
                    if i % 100 == 0:
                        gc.collect()
                        
                except Exception as e:
                    errors.append(str(e))
                    
        except Exception as e:
            errors.append(f"Critical error: {str(e)}")
            
        end_time = time.time()
        duration = end_time - start_time
        
        # Final garbage collection
        gc.collect()
        final_memory = psutil.virtual_memory().used / (1024 * 1024)
        
        # Stop monitoring
        stats = monitor.stop_monitoring()
        
        # Check for memory leak
        memory_growth = final_memory - initial_memory
        memory_leak_detected = memory_growth > 100  # More than 100MB growth
        
        error_rate = len(errors) / iterations if iterations > 0 else 0
        ops_per_second = operations_completed / duration if duration > 0 else 0
        
        return StressTestResult(
            test_name="memory_leak_detection",
            duration_seconds=duration,
            operations_completed=operations_completed,
            operations_per_second=ops_per_second,
            errors_count=len(errors),
            error_rate=error_rate,
            memory_peak_mb=stats['peak_memory_mb'],
            cpu_peak_percent=stats['peak_cpu_percent'],
            success=not memory_leak_detected and error_rate < 0.01,
            error_details=errors[:10] + [f"Memory growth: {memory_growth:.2f}MB"]
        )


class EnduranceTestRunner:
    """Long-running endurance tests."""
    
    def test_24_hour_simulation(self, duration_minutes: int = 60) -> StressTestResult:
        """Simulate 24-hour operation in compressed time."""
        errors = []
        operations_completed = 0
        monitor = StressTestMonitor()
        
        monitor.start_monitoring()
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        
        db_manager = DatabaseManager()
        
        # Simulate realistic usage patterns
        operation_cycle = 0
        
        try:
            while time.time() < end_time:
                try:
                    cycle_type = operation_cycle % 4
                    
                    if cycle_type == 0:
                        # Heavy read period (simulate day shift)
                        for _ in range(10):
                            db_manager.get_epics()
                            db_manager.get_tasks()
                            operations_completed += 2
                            
                    elif cycle_type == 1:
                        # Write operations (simulate active development)
                        epic_data = {
                            'title': f'Endurance Epic {operation_cycle}',
                            'client_id': 1,
                            'points_value': random.randint(10, 50)
                        }
                        epic_id = db_manager.create_epic(epic_data)
                        if epic_id:
                            operations_completed += 1
                            
                    elif cycle_type == 2:
                        # Analytics operations (simulate reporting)
                        epics = db_manager.get_epics()
                        if epics:
                            epic_id = epics[0]['id']
                            db_manager.get_epic_analytics(epic_id)
                            operations_completed += 1
                            
                    elif cycle_type == 3:
                        # Light maintenance (simulate off-hours)
                        db_manager.get_health_check()
                        operations_completed += 1
                        
                    operation_cycle += 1
                    
                    # Simulate realistic delays
                    time.sleep(random.uniform(0.1, 0.5))
                    
                except Exception as e:
                    errors.append(str(e))
                    
                # Periodic cleanup
                if operation_cycle % 1000 == 0:
                    gc.collect()
                    
        except Exception as e:
            errors.append(f"Critical endurance error: {str(e)}")
            
        duration = time.time() - start_time
        stats = monitor.stop_monitoring()
        
        error_rate = len(errors) / operations_completed if operations_completed > 0 else 1
        ops_per_second = operations_completed / duration if duration > 0 else 0
        
        return StressTestResult(
            test_name="endurance_24h_simulation",
            duration_seconds=duration,
            operations_completed=operations_completed,
            operations_per_second=ops_per_second,
            errors_count=len(errors),
            error_rate=error_rate,
            memory_peak_mb=stats['peak_memory_mb'],
            cpu_peak_percent=stats['peak_cpu_percent'],
            success=error_rate < 0.05 and operations_completed > 100,
            error_details=errors[:10]
        )


# Pytest Test Classes

class TestDatabaseStress:
    """Database stress tests."""
    
    def test_concurrent_write_stress(self):
        """Test concurrent database writes."""
        tester = DatabaseStressTester()
        result = tester.test_concurrent_writes(num_threads=5, operations_per_thread=50)
        
        assert result.success, f"Stress test failed: {result.error_details}"
        assert result.error_rate < 0.1, f"Error rate too high: {result.error_rate:.2%}"
        assert result.operations_per_second > 10, f"Performance too low: {result.operations_per_second:.2f} ops/s"
        
    def test_read_heavy_load_stress(self):
        """Test heavy read load."""
        tester = DatabaseStressTester()
        result = tester.test_read_heavy_load(num_threads=10, queries_per_thread=100)
        
        assert result.success, f"Read stress test failed: {result.error_details}"
        assert result.error_rate < 0.05, f"Error rate too high: {result.error_rate:.2%}"
        assert result.operations_per_second > 50, f"Read performance too low: {result.operations_per_second:.2f} ops/s"
        
    def test_connection_pool_stress(self):
        """Test connection pool under stress."""
        tester = DatabaseStressTester()
        result = tester.test_connection_pool_stress(num_connections=20, operations_per_connection=25)
        
        assert result.success, f"Connection pool stress test failed: {result.error_details}"
        assert result.error_rate < 0.02, f"Error rate too high: {result.error_rate:.2%}"


class TestMemoryStress:
    """Memory stress tests."""
    
    def test_memory_leak_detection(self):
        """Test for memory leaks."""
        tester = MemoryStressTester()
        result = tester.test_memory_leak_detection(iterations=500)
        
        assert result.success, f"Memory leak detected: {result.error_details}"
        assert result.error_rate < 0.01, f"Error rate too high: {result.error_rate:.2%}"


class TestEnduranceStress:
    """Endurance stress tests."""
    
    @pytest.mark.slow
    def test_endurance_simulation(self):
        """Test endurance under simulated 24-hour load."""
        tester = EnduranceTestRunner()
        result = tester.test_24_hour_simulation(duration_minutes=5)  # 5-minute simulation
        
        assert result.success, f"Endurance test failed: {result.error_details}"
        assert result.error_rate < 0.05, f"Error rate too high: {result.error_rate:.2%}"
        assert result.operations_completed > 50, f"Too few operations: {result.operations_completed}"


def generate_stress_test_report(results: List[StressTestResult]) -> str:
    """Generate comprehensive stress test report."""
    report = []
    report.append("# Stress Test Report")
    report.append("=" * 50)
    report.append(f"Generated: {datetime.now().isoformat()}")
    report.append("")
    
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r.success)
    
    report.append(f"## Summary")
    report.append(f"Total Tests: {total_tests}")
    report.append(f"Passed: {passed_tests}")
    report.append(f"Failed: {total_tests - passed_tests}")
    report.append(f"Success Rate: {passed_tests/total_tests*100:.1f}%")
    report.append("")
    
    for result in results:
        status = "✅ PASS" if result.success else "❌ FAIL"
        report.append(f"## {result.test_name} {status}")
        report.append(f"- Duration: {result.duration_seconds:.2f}s")
        report.append(f"- Operations: {result.operations_completed}")
        report.append(f"- Ops/sec: {result.operations_per_second:.2f}")
        report.append(f"- Error Rate: {result.error_rate:.2%}")
        report.append(f"- Peak Memory: {result.memory_peak_mb:.2f}MB")
        report.append(f"- Peak CPU: {result.cpu_peak_percent:.1f}%")
        
        if result.error_details:
            report.append("- Errors:")
            for error in result.error_details[:5]:
                report.append(f"  - {error}")
        report.append("")
    
    return "\n".join(report)


if __name__ == "__main__":
    # Run stress tests manually
    print("🔥 Running Stress Test Suite...")
    
    results = []
    
    # Database stress tests
    db_tester = DatabaseStressTester()
    results.append(db_tester.test_concurrent_writes(num_threads=3, operations_per_thread=20))
    results.append(db_tester.test_read_heavy_load(num_threads=5, queries_per_thread=100))
    results.append(db_tester.test_connection_pool_stress(num_connections=10, operations_per_connection=20))
    
    # Memory stress tests
    mem_tester = MemoryStressTester()
    results.append(mem_tester.test_memory_leak_detection(iterations=200))
    
    # Generate report
    report = generate_stress_test_report(results)
    print(report)
    
    # Save report
    with open('stress_test_report.txt', 'w') as f:
        f.write(report)
    
    print("📊 Stress test report saved to: stress_test_report.txt")
```

## 📋 ADDITIONAL TEST FILES

### 1. tests/performance/test_breakpoint_testing.py

Create breakpoint testing to find system limits:

```python
#!/usr/bin/env python3
"""
Breakpoint Testing - Find System Breaking Points
Gradually increase load until system fails to find limits.
"""

import pytest
from test_stress_suite import DatabaseStressTester, StressTestResult


class BreakpointTester:
    """Find system breaking points."""
    
    def find_max_concurrent_connections(self) -> Dict[str, Any]:
        """Find maximum concurrent connections before failure."""
        tester = DatabaseStressTester()
        
        max_successful = 0
        breaking_point = None
        
        for connections in [5, 10, 20, 50, 100, 200]:
            result = tester.test_connection_pool_stress(
                num_connections=connections, 
                operations_per_connection=10
            )
            
            if result.success and result.error_rate < 0.05:
                max_successful = connections
            else:
                breaking_point = connections
                break
                
        return {
            'max_successful_connections': max_successful,
            'breaking_point': breaking_point,
            'safe_limit': int(max_successful * 0.8)  # 80% of max
        }
```

### 2. tests/performance/conftest.py

Pytest configuration for stress tests:

```python
import pytest

def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "stress: mark test as stress test (may take long time)"
    )
    config.addinivalue_line(
        "markers", "endurance: mark test as endurance test (very long running)"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow"
    )

def pytest_collection_modifyitems(config, items):
    """Skip stress tests by default."""
    if config.getoption("--stress") or config.getoption("--endurance"):
        return
        
    skip_stress = pytest.mark.skip(reason="need --stress option to run")
    skip_endurance = pytest.mark.skip(reason="need --endurance option to run")
    
    for item in items:
        if "stress" in item.keywords:
            item.add_marker(skip_stress)
        if "endurance" in item.keywords:
            item.add_marker(skip_endurance)

def pytest_addoption(parser):
    """Add command line options."""
    parser.addoption(
        "--stress", action="store_true", default=False, help="run stress tests"
    )
    parser.addoption(
        "--endurance", action="store_true", default=False, help="run endurance tests"
    )
```

## ✅ REQUIREMENTS

1. **Create comprehensive stress testing suite** with database, memory, and endurance tests
2. **Include resource monitoring** during test execution
3. **Add breakpoint testing** to find system limits
4. **Provide detailed reporting** with performance metrics
5. **Include pytest integration** with custom markers
6. **Add concurrent operation testing** for race conditions
7. **Include memory leak detection** tests
8. **Add endurance testing** for long-running stability

## 🚫 WHAT NOT TO CHANGE
- Existing test files or test infrastructure
- Application logic or functionality
- Database schema or data
- Import statements in existing files

## ✅ VERIFICATION CHECKLIST
- [ ] Comprehensive stress test suite created
- [ ] Resource monitoring implemented
- [ ] Breakpoint testing included
- [ ] Detailed reporting system provided
- [ ] Pytest integration with markers
- [ ] Memory leak detection tests
- [ ] Endurance testing implemented
- [ ] All tests can run independently
- [ ] Performance thresholds defined
- [ ] Error reporting comprehensive

## 🎯 CONTEXT
This addresses report.md requirement: "Load/performance testing previously absent; basic load, stress and endurance suites now in place" in the Test Coverage Report.

The stress testing suite will help identify system limits and ensure stability under load.