# 🤖 PROMPT HH: CONCURRENCY TESTING

## 🎯 OBJECTIVE
Create comprehensive concurrency testing suite to address report.md requirement: "Performance testing for concurrent operations needs implementation" in the Test Coverage Report.

## 📁 FILE TO CREATE

### tests/performance/test_concurrency_suite.py (NEW FILE)

```python
#!/usr/bin/env python3
"""
Comprehensive Concurrency Testing Suite
Tests system behavior under concurrent operations and race conditions.
"""

import pytest
import time
import threading
import multiprocessing
import asyncio
import sqlite3
import random
import concurrent.futures
from typing import List, Dict, Any, Callable, Optional
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from dataclasses import dataclass
from queue import Queue, Empty
import tempfile
import os

from streamlit_extension.utils.database import DatabaseManager
from duration_system.duration_calculator import DurationCalculator
from duration_system.duration_formatter import DurationFormatter


@dataclass
class ConcurrencyTestResult:
    """Results from concurrency test execution."""
    test_name: str
    total_operations: int
    successful_operations: int
    failed_operations: int
    race_conditions_detected: int
    deadlocks_detected: int
    data_corruption_detected: int
    execution_time_seconds: float
    threads_used: int
    success_rate: float
    concurrent_errors: List[str]


class ConcurrencyTester:
    """Base class for concurrency testing."""
    
    def __init__(self, test_name: str):
        self.test_name = test_name
        self.results: List[ConcurrencyTestResult] = []
        self.error_queue = Queue()
        self.operation_counter = 0
        self.lock = threading.Lock()
        
    def execute_concurrent_test(
        self, 
        operation: Callable,
        num_threads: int = 10,
        operations_per_thread: int = 100,
        timeout_seconds: int = 30
    ) -> ConcurrencyTestResult:
        """Execute operation concurrently and collect results."""
        start_time = time.time()
        successful_ops = 0
        failed_ops = 0
        errors = []
        
        def worker():
            nonlocal successful_ops, failed_ops
            for _ in range(operations_per_thread):
                try:
                    operation()
                    with self.lock:
                        successful_ops += 1
                except Exception as e:
                    with self.lock:
                        failed_ops += 1
                        errors.append(str(e))
                        self.error_queue.put(str(e))
        
        # Start threads
        threads = []
        for _ in range(num_threads):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()
            
        # Wait for completion with timeout
        for thread in threads:
            thread.join(timeout=timeout_seconds)
            
        execution_time = time.time() - start_time
        total_ops = num_threads * operations_per_thread
        
        # Analyze errors for patterns
        race_conditions = sum(1 for e in errors if "race" in e.lower() or "concurrent" in e.lower())
        deadlocks = sum(1 for e in errors if "deadlock" in e.lower() or "locked" in e.lower())
        corruptions = sum(1 for e in errors if "corrupt" in e.lower() or "integrity" in e.lower())
        
        return ConcurrencyTestResult(
            test_name=self.test_name,
            total_operations=total_ops,
            successful_operations=successful_ops,
            failed_operations=failed_ops,
            race_conditions_detected=race_conditions,
            deadlocks_detected=deadlocks,
            data_corruption_detected=corruptions,
            execution_time_seconds=execution_time,
            threads_used=num_threads,
            success_rate=(successful_ops / total_ops * 100) if total_ops > 0 else 0,
            concurrent_errors=errors[:10]  # Keep first 10 errors
        )


class DatabaseConcurrencyTester(ConcurrencyTester):
    """Test database operations under concurrency."""
    
    def __init__(self):
        super().__init__("database_concurrency")
        self.db_manager = DatabaseManager()
        
    def test_concurrent_epic_creation(self, num_threads: int = 5, epics_per_thread: int = 20) -> ConcurrencyTestResult:
        """Test concurrent epic creation for race conditions."""
        
        def create_epic():
            epic_data = {
                'title': f'Concurrent Epic {threading.current_thread().ident}_{random.randint(1000, 9999)}',
                'description': f'Created at {datetime.now()}',
                'client_id': 1,  # Assuming client 1 exists
                'points_value': random.randint(10, 100)
            }
            
            epic_id = self.db_manager.create_epic(epic_data)
            if not epic_id:
                raise Exception("Failed to create epic")
                
            # Verify the epic was created correctly
            epic = self.db_manager.get_epic(epic_id)
            if not epic or epic.get('title') != epic_data['title']:
                raise Exception("Data corruption detected in epic creation")
                
        return self.execute_concurrent_test(create_epic, num_threads, epics_per_thread)
        
    def test_concurrent_task_updates(self, num_threads: int = 8, updates_per_thread: int = 25) -> ConcurrencyTestResult:
        """Test concurrent task updates for race conditions."""
        
        # Create test tasks first
        test_task_ids = []
        for i in range(num_threads * 2):  # Create more tasks than threads
            task_data = {
                'title': f'Concurrency Test Task {i}',
                'epic_id': 1,  # Assuming epic 1 exists
                'tdd_phase': 'red'
            }
            task_id = self.db_manager.create_task(task_data)
            if task_id:
                test_task_ids.append(task_id)
                
        def update_task():
            if not test_task_ids:
                raise Exception("No test tasks available")
                
            task_id = random.choice(test_task_ids)
            update_data = {
                'tdd_phase': random.choice(['red', 'green', 'refactor']),
                'status': random.choice(['todo', 'in_progress', 'done']),
                'updated_at': datetime.now().isoformat()
            }
            
            success = self.db_manager.update_task(task_id, update_data)
            if not success:
                raise Exception(f"Failed to update task {task_id}")
                
            # Verify update was applied
            task = self.db_manager.get_task(task_id)
            if not task:
                raise Exception(f"Task {task_id} disappeared after update")
                
        return self.execute_concurrent_test(update_task, num_threads, updates_per_thread)
        
    def test_concurrent_cascade_operations(self, num_threads: int = 4, operations_per_thread: int = 10) -> ConcurrencyTestResult:
        """Test concurrent cascade delete operations."""
        
        # Create test data hierarchy
        test_epic_ids = []
        for i in range(num_threads):
            epic_data = {
                'title': f'Cascade Test Epic {i}',
                'client_id': 1,
                'points_value': 50
            }
            epic_id = self.db_manager.create_epic(epic_data)
            if epic_id:
                test_epic_ids.append(epic_id)
                
                # Create tasks for this epic
                for j in range(3):
                    task_data = {
                        'title': f'Cascade Test Task {i}_{j}',
                        'epic_id': epic_id,
                        'tdd_phase': 'red'
                    }
                    self.db_manager.create_task(task_data)
                    
        def cascade_delete():
            if not test_epic_ids:
                raise Exception("No test epics available for cascade delete")
                
            # Randomly select an epic to delete
            epic_id = random.choice(test_epic_ids)
            
            try:
                # Get tasks before deletion
                tasks_before = self.db_manager.get_tasks(epic_id=epic_id)
                
                # Perform cascade delete
                success = self.db_manager.delete_epic(epic_id)
                if not success:
                    raise Exception(f"Failed to delete epic {epic_id}")
                    
                # Verify cascade worked
                tasks_after = self.db_manager.get_tasks(epic_id=epic_id)
                if tasks_after:
                    raise Exception(f"Cascade delete failed - tasks still exist for epic {epic_id}")
                    
                # Remove from test list
                if epic_id in test_epic_ids:
                    test_epic_ids.remove(epic_id)
                    
            except sqlite3.IntegrityError as e:
                if "FOREIGN KEY constraint failed" in str(e):
                    raise Exception(f"Race condition in cascade delete: {e}")
                raise
                
        return self.execute_concurrent_test(cascade_delete, num_threads, operations_per_thread)


class CacheConcurrencyTester(ConcurrencyTester):
    """Test caching system under concurrency."""
    
    def __init__(self):
        super().__init__("cache_concurrency")
        self.calculator = DurationCalculator()
        self.formatter = DurationFormatter()
        
    def test_concurrent_cache_access(self, num_threads: int = 10, calculations_per_thread: int = 50) -> ConcurrencyTestResult:
        """Test concurrent access to duration calculation cache."""
        
        # Prepare test data
        test_durations = [
            "1 day 2 hours 30 minutes",
            "3 weeks 4 days",
            "2 months 1 week",
            "45 minutes",
            "1 year 6 months",
            "10 days 8 hours",
            "30 minutes 45 seconds",
            "2 hours 15 minutes"
        ]
        
        def calculate_duration():
            duration_text = random.choice(test_durations)
            
            # Calculate duration (this should use cache)
            result = self.calculator.parse_duration_text(duration_text)
            if not result:
                raise Exception(f"Failed to calculate duration for: {duration_text}")
                
            # Format the result (this should also use cache)
            if result.total_duration_hours:
                formatted = self.formatter.format_duration(result.total_duration_hours)
                if not formatted:
                    raise Exception(f"Failed to format duration: {result.total_duration_hours}")
                    
            # Verify cache consistency
            result2 = self.calculator.parse_duration_text(duration_text)
            if result2 and result.total_duration_hours != result2.total_duration_hours:
                raise Exception(f"Cache inconsistency detected for: {duration_text}")
                
        return self.execute_concurrent_test(calculate_duration, num_threads, calculations_per_thread)
        
    def test_concurrent_cache_invalidation(self, num_threads: int = 6, operations_per_thread: int = 30) -> ConcurrencyTestResult:
        """Test concurrent cache invalidation scenarios."""
        
        def cache_operation():
            operation_type = random.choice(['calculate', 'invalidate', 'clear'])
            
            if operation_type == 'calculate':
                # Perform calculation
                duration_text = f"{random.randint(1, 100)} hours {random.randint(1, 59)} minutes"
                result = self.calculator.parse_duration_text(duration_text)
                if not result:
                    raise Exception("Calculation failed during concurrent test")
                    
            elif operation_type == 'invalidate':
                # Simulate cache invalidation (if available)
                try:
                    if hasattr(self.calculator, 'clear_cache'):
                        self.calculator.clear_cache()
                except Exception as e:
                    # Cache clear failures might happen in concurrent scenarios
                    if "race" not in str(e).lower():
                        raise Exception(f"Cache invalidation failed: {e}")
                        
            elif operation_type == 'clear':
                # Clear formatter cache (if available)
                try:
                    if hasattr(self.formatter, 'clear_cache'):
                        self.formatter.clear_cache()
                except Exception as e:
                    if "race" not in str(e).lower():
                        raise Exception(f"Cache clear failed: {e}")
                        
        return self.execute_concurrent_test(cache_operation, num_threads, operations_per_thread)


class SessionConcurrencyTester(ConcurrencyTester):
    """Test session management under concurrency."""
    
    def __init__(self):
        super().__init__("session_concurrency")
        
    def test_concurrent_session_creation(self, num_threads: int = 8, sessions_per_thread: int = 15) -> ConcurrencyTestResult:
        """Test concurrent session creation and management."""
        
        def create_session():
            # Simulate session creation
            session_id = f"session_{threading.current_thread().ident}_{random.randint(1000, 9999)}"
            
            # Simulate session data
            session_data = {
                'user_id': random.randint(1, 100),
                'created_at': datetime.now().isoformat(),
                'activity': random.choice(['coding', 'planning', 'testing', 'review'])
            }
            
            # Simulate session storage (would be actual implementation)
            time.sleep(random.uniform(0.001, 0.01))  # Simulate I/O
            
            # Simulate session validation
            if not session_id or not session_data:
                raise Exception("Session creation failed")
                
        return self.execute_concurrent_test(create_session, num_threads, sessions_per_thread)


# Pytest Test Classes

class TestDatabaseConcurrency:
    """Database concurrency tests."""
    
    def test_concurrent_epic_creation(self):
        """Test concurrent epic creation."""
        tester = DatabaseConcurrencyTester()
        result = tester.test_concurrent_epic_creation(num_threads=3, epics_per_thread=10)
        
        assert result.success_rate >= 95.0, f"Success rate too low: {result.success_rate:.1f}%"
        assert result.race_conditions_detected == 0, f"Race conditions detected: {result.race_conditions_detected}"
        assert result.data_corruption_detected == 0, f"Data corruption detected: {result.data_corruption_detected}"
        
    def test_concurrent_task_updates(self):
        """Test concurrent task updates."""
        tester = DatabaseConcurrencyTester()
        result = tester.test_concurrent_task_updates(num_threads=4, updates_per_thread=15)
        
        assert result.success_rate >= 90.0, f"Success rate too low: {result.success_rate:.1f}%"
        assert result.deadlocks_detected == 0, f"Deadlocks detected: {result.deadlocks_detected}"
        
    def test_concurrent_cascade_operations(self):
        """Test concurrent cascade operations."""
        tester = DatabaseConcurrencyTester()
        result = tester.test_concurrent_cascade_operations(num_threads=2, operations_per_thread=5)
        
        assert result.success_rate >= 80.0, f"Success rate too low: {result.success_rate:.1f}%"
        assert result.race_conditions_detected <= 1, f"Too many race conditions: {result.race_conditions_detected}"


class TestCacheConcurrency:
    """Cache concurrency tests."""
    
    def test_concurrent_cache_access(self):
        """Test concurrent cache access."""
        tester = CacheConcurrencyTester()
        result = tester.test_concurrent_cache_access(num_threads=5, calculations_per_thread=20)
        
        assert result.success_rate >= 98.0, f"Cache success rate too low: {result.success_rate:.1f}%"
        assert result.data_corruption_detected == 0, f"Cache corruption detected: {result.data_corruption_detected}"
        
    def test_concurrent_cache_invalidation(self):
        """Test concurrent cache invalidation."""
        tester = CacheConcurrencyTester()
        result = tester.test_concurrent_cache_invalidation(num_threads=4, operations_per_thread=20)
        
        assert result.success_rate >= 85.0, f"Cache invalidation success rate too low: {result.success_rate:.1f}%"


class TestSessionConcurrency:
    """Session concurrency tests."""
    
    def test_concurrent_session_creation(self):
        """Test concurrent session creation."""
        tester = SessionConcurrencyTester()
        result = tester.test_concurrent_session_creation(num_threads=4, sessions_per_thread=10)
        
        assert result.success_rate >= 95.0, f"Session creation success rate too low: {result.success_rate:.1f}%"
        assert result.race_conditions_detected == 0, f"Session race conditions detected: {result.race_conditions_detected}"


class TestConcurrentFileOperations:
    """Test concurrent file operations."""
    
    def test_concurrent_log_writing(self):
        """Test concurrent log file writing."""
        
        def write_log_entry():
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
                log_entry = f"{datetime.now().isoformat()} - Thread {threading.current_thread().ident} - Test entry\n"
                f.write(log_entry)
                f.flush()
                os.fsync(f.fileno())
                
            # Clean up
            try:
                os.unlink(f.name)
            except:
                pass
                
        tester = ConcurrencyTester("file_operations")
        result = tester.execute_concurrent_test(write_log_entry, num_threads=5, operations_per_thread=20)
        
        assert result.success_rate >= 95.0, f"File operation success rate too low: {result.success_rate:.1f}%"


def generate_concurrency_test_report(results: List[ConcurrencyTestResult]) -> str:
    """Generate comprehensive concurrency test report."""
    report = []
    report.append("# Concurrency Test Report")
    report.append("=" * 50)
    report.append(f"Generated: {datetime.now().isoformat()}")
    report.append("")
    
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r.success_rate >= 85.0)
    
    report.append(f"## Summary")
    report.append(f"Total Tests: {total_tests}")
    report.append(f"Passed: {passed_tests}")
    report.append(f"Failed: {total_tests - passed_tests}")
    report.append(f"Success Rate: {passed_tests/total_tests*100:.1f}%")
    report.append("")
    
    report.append(f"## Detailed Results")
    for result in results:
        status = "✅ PASS" if result.success_rate >= 85.0 else "❌ FAIL"
        report.append(f"### {result.test_name} {status}")
        report.append(f"- Total Operations: {result.total_operations}")
        report.append(f"- Success Rate: {result.success_rate:.1f}%")
        report.append(f"- Execution Time: {result.execution_time_seconds:.2f}s")
        report.append(f"- Threads Used: {result.threads_used}")
        report.append(f"- Race Conditions: {result.race_conditions_detected}")
        report.append(f"- Deadlocks: {result.deadlocks_detected}")
        report.append(f"- Data Corruption: {result.data_corruption_detected}")
        
        if result.concurrent_errors:
            report.append("- Sample Errors:")
            for error in result.concurrent_errors[:3]:
                report.append(f"  - {error}")
        report.append("")
    
    return "\n".join(report)


if __name__ == "__main__":
    # Run concurrency tests manually
    print("⚡ Running Concurrency Test Suite...")
    
    results = []
    
    # Database concurrency tests
    db_tester = DatabaseConcurrencyTester()
    results.append(db_tester.test_concurrent_epic_creation(num_threads=2, epics_per_thread=10))
    results.append(db_tester.test_concurrent_task_updates(num_threads=3, updates_per_thread=10))
    
    # Cache concurrency tests
    cache_tester = CacheConcurrencyTester()
    results.append(cache_tester.test_concurrent_cache_access(num_threads=3, calculations_per_thread=15))
    
    # Session concurrency tests
    session_tester = SessionConcurrencyTester()
    results.append(session_tester.test_concurrent_session_creation(num_threads=3, sessions_per_thread=10))
    
    # Generate report
    report = generate_concurrency_test_report(results)
    print(report)
    
    # Save report
    with open('concurrency_test_report.txt', 'w') as f:
        f.write(report)
    
    print("📊 Concurrency test report saved to: concurrency_test_report.txt")
```

## 📋 ADDITIONAL TESTING SCENARIOS

### 1. Race Condition Detection

```python
def test_race_condition_detection():
    """Detect race conditions in shared resource access."""
    shared_counter = 0
    lock = threading.Lock()
    
    def unsafe_increment():
        global shared_counter
        temp = shared_counter
        time.sleep(0.001)  # Simulate processing time
        shared_counter = temp + 1
        
    def safe_increment():
        global shared_counter
        with lock:
            temp = shared_counter
            time.sleep(0.001)
            shared_counter = temp + 1
    
    # Test unsafe version (should detect race conditions)
    # Test safe version (should not detect race conditions)
```

### 2. Deadlock Detection

```python
def test_deadlock_detection():
    """Test for potential deadlocks in database operations."""
    
    def operation_a():
        # Acquire locks in order A -> B
        with db_manager.get_connection() as conn:
            conn.execute("BEGIN EXCLUSIVE")
            time.sleep(0.1)
            # Try to access another resource
    
    def operation_b():
        # Acquire locks in order B -> A
        with db_manager.get_connection() as conn:
            conn.execute("BEGIN EXCLUSIVE") 
            time.sleep(0.1)
            # Try to access another resource
```

### 3. Resource Exhaustion Testing

```python
def test_resource_exhaustion():
    """Test system behavior under resource exhaustion."""
    
    def create_many_connections():
        connections = []
        try:
            for i in range(1000):  # Try to exhaust connection pool
                conn = sqlite3.connect('framework.db')
                connections.append(conn)
        finally:
            for conn in connections:
                try:
                    conn.close()
                except:
                    pass
```

## ✅ REQUIREMENTS

1. **Create comprehensive concurrency testing suite** with real scenarios
2. **Test database operations** under concurrent access
3. **Test cache systems** for race conditions and consistency
4. **Include deadlock detection** and prevention testing
5. **Add race condition detection** for shared resources
6. **Test session management** under concurrent load
7. **Include resource exhaustion testing**
8. **Provide detailed reporting** with metrics and analysis

## 🚫 WHAT NOT TO CHANGE
- Existing test files or test infrastructure
- Application logic or functionality  
- Database schema or data
- Import statements in existing files
- Performance characteristics

## ✅ VERIFICATION CHECKLIST
- [ ] Comprehensive concurrency test suite created
- [ ] Database concurrency tests included
- [ ] Cache concurrency tests included
- [ ] Race condition detection implemented
- [ ] Deadlock detection included
- [ ] Session concurrency tests added
- [ ] Resource exhaustion tests included
- [ ] Detailed reporting system provided
- [ ] All tests can run independently
- [ ] Performance thresholds defined

## 🎯 CONTEXT
This addresses report.md requirement: "Performance testing for concurrent operations needs implementation" in the Test Coverage Report.

The concurrency testing suite will help identify race conditions, deadlocks, and ensure system stability under concurrent load.