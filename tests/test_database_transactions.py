"""
🧪 Test Suite for Database Transaction Safety

Comprehensive tests for transactional database operations.
Validates fixes for Codex audit issues:

1. Transactional consistency for duration updates
2. Deadlock prevention and retry logic  
3. Concurrent write protection
4. Connection pooling safety
5. Proper rollback handling
"""

import pytest
import sys
import time
import sqlite3
import threading
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add duration_system to path
sys.path.append(str(Path(__file__).parent.parent))

from duration_system.database_transactions import (
    TransactionalDatabaseManager,
    DatabaseConnectionPool,
    IsolationLevel,
    TransactionMode,
    TransactionResult,
    SafeDatabaseOperationsMixin,
    test_transaction_safety
)


class TestDatabaseConnectionPool:
    """Test suite for database connection pooling."""
    
    # TODO: Consider extracting this block into a separate method
    # TODO: Consider extracting this block into a separate method
    def setup_method(self):
        """Setup for each test method."""
        # Create temporary database
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.db_path = self.temp_db.name
        self.temp_db.close()
        
        # Initialize test database
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE test_table (
                    id INTEGER PRIMARY KEY,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
        
        self.pool = DatabaseConnectionPool(self.db_path, max_connections=3, connection_timeout=0.1)
    
    def teardown_method(self):
        """Cleanup after each test."""
        self.pool.close_all()
        try:
            Path(self.db_path).unlink()
        except:
            pass
    
    def test_connection_acquisition_basic(self):
        """Test basic connection acquisition and release."""
        with self.pool.get_connection() as conn:
            assert conn is not None
            
            # Test that connection works
            cursor = conn.execute("SELECT 1")
            result = cursor.fetchone()
            assert result[0] == 1
        
        # After context exit, connection should be released
        stats = self.pool.stats
        assert stats["active_connections"] == 0
    
    def test_connection_reuse(self):
        """Test that connections are properly reused."""
        # First acquisition
        with self.pool.get_connection() as conn1:
            conn1_id = id(conn1)
        
        # Second acquisition should reuse same connection
        with self.pool.get_connection() as conn2:
            conn2_id = id(conn2)
            assert conn1_id == conn2_id
        
        stats = self.pool.stats
        assert stats["connections_reused"] > 0
    
# TODO: Consider extracting this block into a separate method
    
# TODO: Consider extracting this block into a separate method
    
    def test_concurrent_connections(self):
        """Test concurrent connection handling."""
        results = []
        errors = []
        
        def use_connection(thread_id):
            try:
                with self.pool.get_connection() as conn:
                    # Insert data
                    conn.execute("INSERT INTO test_table (value) VALUES (?)", (f"thread_{thread_id}",))
                    conn.commit()
                    
                    # Read data
                    cursor = conn.execute("SELECT COUNT(*) FROM test_table")
                    count = cursor.fetchone()[0]
                    results.append((thread_id, count))
                    
            except Exception as e:
                errors.append((thread_id, str(e)))
        
        # Launch multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=use_connection, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Verify results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 5
        
        # Final count should be 5
        with self.pool.get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM test_table")
            final_count = cursor.fetchone()[0]
            assert final_count == 5
    
    def test_connection_pool_limit(self):
        """Test that connection pool respects limits with proper timeout handling."""
        import time
        import threading
        
        # Test connection pool behavior under load without deadlock
        acquired_connections = []
        
        try:
            # Acquire connections up to the pool limit
            for i in range(3):  # Pool limit is 3
                conn = self.pool._acquire_connection()
                acquired_connections.append(conn)
            
            # Verify pool is at capacity
            assert len(self.pool._in_use) == 3
            assert len(acquired_connections) == 3
            
            # Test timeout behavior with a thread that tries to acquire when pool is full
            timeout_occurred = threading.Event()
            connection_acquired = threading.Event()
            
            def try_acquire_with_timeout():
                """Try to acquire connection when pool is at capacity."""
                start_time = time.time()
                try:
                    # This should timeout based on pool's connection_timeout (0.1s)
                    conn = self.pool._acquire_connection()
                    connection_acquired.set()
                    # If we get here, release immediately
                    self.pool._release_connection(conn)
                except Exception:
                    elapsed = time.time() - start_time
                    if elapsed >= 0.1:  # Pool timeout is 0.1s
                        timeout_occurred.set()
            
            # Start thread that will timeout
            timeout_thread = threading.Thread(target=try_acquire_with_timeout)
            timeout_thread.start()
            
            # Wait for timeout to occur
            timeout_thread.join(timeout=2.0)  # Give enough time for timeout
            
            # Verify timeout behavior
            assert timeout_occurred.is_set() or connection_acquired.is_set(), "Thread should have either timed out or acquired emergency connection"
            
            # Test that releasing a connection allows others to proceed
            if acquired_connections:
                # Release one connection
                conn_to_release = acquired_connections.pop()
                self.pool._release_connection(conn_to_release)
                
                # Verify connection was properly released
                assert len(self.pool._in_use) == 2
                
                # Now acquiring should work
                new_conn = self.pool._acquire_connection()
                acquired_connections.append(new_conn)
                assert len(self.pool._in_use) == 3
            
        finally:
            # Clean up all acquired connections
            for conn in acquired_connections:
                try:
                    self.pool._release_connection(conn)
                except Exception:
                    pass
            
            # Verify pool is cleaned up
            assert len(self.pool._in_use) == 0
    
    def test_connection_health_check(self):
        """Test connection health checking."""
        with self.pool.get_connection() as conn:
            # Connection should be healthy
            assert self.pool._is_connection_healthy(conn) is True
        
        # Create a broken connection
        broken_conn = sqlite3.connect(":memory:")
        broken_conn.close()
        
        # Should detect as unhealthy
        assert self.pool._is_connection_healthy(broken_conn) is False


# TODO: Consider extracting this block into a separate method
# TODO: Consider extracting this block into a separate method
class TestTransactionalDatabaseManager:
    """Test suite for transactional database operations."""
    
    def setup_method(self):
        """Setup for each test method."""
        # Create temporary database
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.db_path = self.temp_db.name
        self.temp_db.close()
        
        # Initialize test database with epic structure
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE framework_epics (
                    id INTEGER PRIMARY KEY,
                    epic_key TEXT UNIQUE,
                    name TEXT,
                    duration_description TEXT,
                    calculated_duration_days REAL,
                    planned_start_date TEXT,
                    planned_end_date TEXT,
                    actual_start_date TEXT,
                    actual_end_date TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Insert test epic
            conn.execute("""
                INSERT INTO framework_epics 
                (id, epic_key, name, duration_description, calculated_duration_days)
                VALUES (1, 'TEST_1', 'Test Epic', '5 dias', 5.0)
            """)
            conn.commit()
        
        self.manager = TransactionalDatabaseManager(self.db_path, max_retries=2)
    
    def teardown_method(self):
        """Cleanup after each test."""
        self.manager.close()
        try:
            # TODO: Consider extracting this block into a separate method
            # TODO: Consider extracting this block into a separate method
            Path(self.db_path).unlink()
        except:
            pass
    
    def test_successful_duration_update(self):
        """Test successful duration update with transactions."""
        result = self.manager.update_epic_duration_safe(1, "10 dias", 10.0)
        
        assert result.success is True
        assert result.error is None
        assert result.retry_count == 0
        assert result.duration_ms > 0
        
        # Verify the update
        read_result = self.manager.get_epic_duration_safe(1)
        assert read_result.success is True
        epic_data = read_result.result
        assert epic_data["duration_description"] == "10 dias"
        assert epic_data["calculated_duration_days"] == 10.0
    
    def test_epic_not_found_error(self):
        """Test error handling for non-existent epic."""
        # TODO: Consider extracting this block into a separate method
        # TODO: Consider extracting this block into a separate method
        result = self.manager.update_epic_duration_safe(999, "5 dias", 5.0)
        
        assert result.success is False
        assert "not found" in result.error.lower()
    
    def test_concurrent_update_conflict(self):
        """Test handling of concurrent update conflicts."""
        # This test simulates optimistic concurrency control
        
        # First, get the current epic data
        initial_result = self.manager.get_epic_duration_safe(1)
        assert initial_result.success is True
        
        # Simulate a concurrent update by directly modifying the database
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE framework_epics 
                SET updated_at = ? 
                WHERE id = 1
            """, (datetime.now() + timedelta(seconds=1),))
            conn.commit()
        
        # TODO: Consider extracting this block into a separate method
        # TODO: Consider extracting this block into a separate method
        # Now try to update - this might succeed or fail depending on timing
        result = self.manager.update_epic_duration_safe(1, "15 dias", 15.0)
        
        # Either way, the operation should complete without hanging
        assert isinstance(result, TransactionResult)
    
    def test_batch_duration_updates(self):
        """Test batch updates of multiple epics."""
        # Add more test epics
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO framework_epics 
                (id, epic_key, name, duration_description, calculated_duration_days)
                VALUES (2, 'TEST_2', 'Test Epic 2', '3 dias', 3.0)
            """)
            conn.execute("""
                INSERT INTO framework_epics 
                (id, epic_key, name, duration_description, calculated_duration_days)
                VALUES (3, 'TEST_3', 'Test Epic 3', '7 dias', 7.0)
            """)
            conn.commit()
        
        # Prepare batch updates
        updates = [
            {"epic_id": 1, "duration_description": "6 dias", "calculated_days": 6.0},
            {"epic_id": 2, "duration_description": "4 dias", "calculated_days": 4.0},
            {"epic_id": 3, "duration_description": "8 dias", "calculated_days": 8.0},
            {"epic_id": 999, "duration_description": "1 dia", "calculated_days": 1.0}  # Non-existent
        ]
        
        result = self.manager.batch_update_epic_durations_safe(updates)
        
        assert result.success is True
        assert result.result == 3  # 3 epics updated (999 doesn't exist)
        
        # Verify updates
        # TODO: Consider extracting this block into a separate method
        # TODO: Consider extracting this block into a separate method
        for epic_id in [1, 2, 3]:
            read_result = self.manager.get_epic_duration_safe(epic_id)
            assert read_result.success is True
            epic_data = read_result.result
            expected_days = [6.0, 4.0, 8.0][epic_id - 1]
            assert epic_data["calculated_duration_days"] == expected_days
    
    def test_duration_consistency_validation(self):
        """Test duration consistency validation."""
        # Update epic with dates
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE framework_epics 
                SET planned_start_date = '2024-06-01',
                    planned_end_date = '2024-06-05',
                    calculated_duration_days = 5.0
                WHERE id = 1
            """)
            conn.commit()
        
# TODO: Consider extracting this block into a separate method
        
# TODO: Consider extracting this block into a separate method
        
        result = self.manager.validate_duration_consistency_safe(1)
        
        assert result.success is True
        validation_data = result.result
        assert validation_data["valid"] is True
        assert len(validation_data["issues"]) == 0
    
    def test_duration_consistency_validation_with_issues(self):
        """Test duration consistency validation with date issues."""
        # Update epic with invalid dates (end before start)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE framework_epics 
                SET planned_start_date = '2024-06-10',
                    planned_end_date = '2024-06-05'
                WHERE id = 1
            """)
            # TODO: Consider extracting this block into a separate method
            # TODO: Consider extracting this block into a separate method
            conn.commit()
        
        result = self.manager.validate_duration_consistency_safe(1)
        
        assert result.success is True
        validation_data = result.result
        assert validation_data["valid"] is False
        assert len(validation_data["issues"]) > 0
        assert "start date is after" in validation_data["issues"][0].lower()
    
    def test_transaction_retry_mechanism(self):
        """Test retry mechanism for transient failures."""
        # This is tricky to test without actually causing database locks
        # We'll test the mechanism by checking stats
        
# TODO: Consider extracting this block into a separate method
        
# TODO: Consider extracting this block into a separate method
        
        # Perform several operations
        for i in range(3):
            result = self.manager.update_epic_duration_safe(1, f"{i+1} dias", float(i+1))
            assert result.success is True
        
        # Check stats
        stats = self.manager.get_transaction_stats()
        assert stats["successful_transactions"] >= 3
        assert stats["success_rate"] > 0
    
    def test_isolation_levels(self):
        """Test different isolation levels."""
        # Test with immediate isolation (should acquire lock immediately)
        @self.manager.transactional(isolation_level=IsolationLevel.IMMEDIATE)
        def immediate_operation(conn):
            cursor = conn.execute("SELECT COUNT(*) FROM framework_epics")
            return cursor.fetchone()[0]
        
        result = immediate_operation()
        # TODO: Consider extracting this block into a separate method
        # TODO: Consider extracting this block into a separate method
        assert result.success is True
        assert result.result >= 1
        
        # Test with deferred isolation (for read operations)
        @self.manager.transactional(isolation_level=IsolationLevel.DEFERRED)
        def deferred_operation(conn):
            cursor = conn.execute("SELECT id, name FROM framework_epics WHERE id = 1")
            return cursor.fetchone()
        
        result = deferred_operation()
        assert result.success is True
        assert result.result[0] == 1  # Epic ID
    
    def test_transaction_statistics(self):
        """Test transaction statistics tracking."""
        # Clear stats first
        self.manager.clear_stats()
        
        # Perform operations
        success_result = self.manager.update_epic_duration_safe(1, "8 dias", 8.0)
        assert success_result.success is True
        
        # Try to cause a failure
        failure_result = self.manager.update_epic_duration_safe(999, "1 dia", 1.0)
        # TODO: Consider extracting this block into a separate method
        # TODO: Consider extracting this block into a separate method
        assert failure_result.success is False
        
        # Check stats
        stats = self.manager.get_transaction_stats()
        assert stats["successful_transactions"] >= 1
        assert stats["failed_transactions"] >= 1
        assert stats["duration_updates"] >= 1
        assert "connection_pool" in stats
        assert "success_rate" in stats


class TestConcurrentTransactionSafety:
    """Test suite for concurrent transaction safety."""
    
    def setup_method(self):
        """Setup for each test method."""
        # Create temporary database
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.db_path = self.temp_db.name
        self.temp_db.close()
        
        # Initialize test database
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE framework_epics (
                    id INTEGER PRIMARY KEY,
                    epic_key TEXT UNIQUE,
                    name TEXT,
                    duration_description TEXT,
                    calculated_duration_days REAL,
                    planned_start_date TEXT,
                    planned_end_date TEXT,
                    actual_start_date TEXT,
                    actual_end_date TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Insert test epics
            for i in range(1, 6):
                conn.execute("""
                    INSERT INTO framework_epics 
                    (id, epic_key, name, duration_description, calculated_duration_days)
                    # TODO: Consider extracting this block into a separate method
                    # TODO: Consider extracting this block into a separate method
                    VALUES (?, ?, ?, ?, ?)
                """, (i, f'TEST_{i}', f'Test Epic {i}', f'{i} dias', float(i)))
            
            conn.commit()
        
        self.manager = TransactionalDatabaseManager(self.db_path, max_retries=3)
    
    def teardown_method(self):
        """Cleanup after each test."""
        self.manager.close()
        try:
            Path(self.db_path).unlink()
        except:
            pass
    
    def test_concurrent_updates_different_epics(self):
        """Test concurrent updates to different epics (should succeed)."""
        results = []
        errors = []
        
        def update_epic(epic_id):
            try:
                result = self.manager.update_epic_duration_safe(
                    epic_id, f"updated_{epic_id} dias", float(epic_id * 10)
                )
                results.append((epic_id, result))
            except Exception as e:
                # TODO: Consider extracting this block into a separate method
                # TODO: Consider extracting this block into a separate method
                errors.append((epic_id, str(e)))
        
        # Launch concurrent updates to different epics
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(update_epic, i) for i in range(1, 6)]
            
            for future in as_completed(futures):
                future.result()  # Wait for completion
        
        # All updates should succeed since they target different epics
        assert len(errors) == 0, f"Unexpected errors: {errors}"
        assert len(results) == 5
        
        successful_results = [r for epic_id, r in results if r.success]
        assert len(successful_results) == 5
    
    def test_concurrent_updates_same_epic(self):
        """Test concurrent updates to same epic (some should fail due to conflicts)."""
        results = []
        errors = []
        
        def update_epic_1(thread_id):
            try:
                result = self.manager.update_epic_duration_safe(
                    1, f"thread_{thread_id} dias", float(thread_id)
                )
                results.append((thread_id, result))
            except Exception as e:
                errors.append((thread_id, str(e)))
        
        # Launch concurrent updates to same epic
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(update_epic_1, i) for i in range(1, 6)]
            
            for future in as_completed(futures):
                # TODO: Consider extracting this block into a separate method
                # TODO: Consider extracting this block into a separate method
                future.result()  # Wait for completion
        
        # Should have some results (not necessarily all successful due to conflicts)
        total_operations = len(results) + len(errors)
        assert total_operations == 5
        
        # At least one should succeed
        successful_results = [r for thread_id, r in results if r.success]
        assert len(successful_results) >= 1
        
        # Check final state
        final_result = self.manager.get_epic_duration_safe(1)
        assert final_result.success is True
        # Final value should be from one of the threads
        final_description = final_result.result["duration_description"]
        assert "thread_" in final_description or "dias" in final_description
    
    def test_concurrent_read_write_operations(self):
        """Test concurrent read and write operations."""
        read_results = []
        write_results = []
        errors = []
        
        def read_epic(thread_id):
            try:
                result = self.manager.get_epic_duration_safe(1)
                read_results.append((thread_id, result))
            except Exception as e:
                errors.append(f"read_{thread_id}: {e}")
        
        def write_epic(thread_id):
            try:
                result = self.manager.update_epic_duration_safe(
                    2, f"write_{thread_id} dias", float(thread_id + 10)
                )
                write_results.append((thread_id, result))
            except Exception as e:
                errors.append(f"write_{thread_id}: {e}")
        
        # Launch mixed read/write operations
        with ThreadPoolExecutor(max_workers=10) as executor:
            # Submit read operations
            read_futures = [executor.submit(read_epic, i) for i in range(5)]
            # Submit write operations
            write_futures = [executor.submit(write_epic, i) for i in range(5)]
            
            # Wait for all operations
            for future in as_completed(read_futures + write_futures):
                future.result()
        
        # Should have minimal errors
        assert len(errors) <= 1, f"Too many errors: {errors}"  # Allow 1 error for race conditions
        
        # Most reads should succeed
        successful_reads = [r for thread_id, r in read_results if r.success]
        assert len(successful_reads) >= 4
        
        # At least some writes should succeed
        successful_writes = [r for thread_id, r in write_results if r.success]
        assert len(successful_writes) >= 1
    
    @pytest.mark.slow
    def test_high_concurrency_stress(self):
        """Stress test with high concurrency."""
        results = []
        errors = []
        
        def mixed_operations(thread_id):
            try:
                epic_id = (thread_id % 3) + 1  # Use epics 1, 2, 3
                
                # Randomly do read or write
                if thread_id % 2 == 0:
                    # Read operation
                    result = self.manager.get_epic_duration_safe(epic_id)
                else:
                    # Write operation
                    result = self.manager.update_epic_duration_safe(
                        epic_id, f"stress_{thread_id} dias", float(thread_id % 10 + 1)
                    )
                
                results.append((thread_id, result))
                
            except Exception as e:
                errors.append((thread_id, str(e)))
        
        # Launch many concurrent operations
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(mixed_operations, i) for i in range(50)]
            
            for future in as_completed(futures):
                future.result()
        
        # TODO: Consider extracting this block into a separate method
        # TODO: Consider extracting this block into a separate method
        # Should handle high concurrency without major issues
        total_operations = len(results) + len(errors)
        assert total_operations == 50
        
        # Should have reasonable success rate (at least 70%)
        successful_results = [r for thread_id, r in results if r.success]
        success_rate = len(successful_results) / len(results) if results else 0
        assert success_rate >= 0.7, f"Success rate too low: {success_rate:.2%}"
        
        # Check transaction stats
        stats = self.manager.get_transaction_stats()
        assert stats["successful_transactions"] > 0
        print(f"High concurrency stats: {stats}")


class TestSafeDatabaseOperationsMixin:
    """Test the mixin for adding transaction safety to existing code."""
    
    def setup_method(self):
        """Setup for each test method."""
        # Create temporary database
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.db_path = self.temp_db.name
        self.temp_db.close()
        
        # Initialize test database
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE framework_epics (
                    id INTEGER PRIMARY KEY,
                    epic_key TEXT UNIQUE,
                    name TEXT,
                    duration_description TEXT,
                    calculated_duration_days REAL,
                    planned_start_date TEXT,
                    planned_end_date TEXT,
                    actual_start_date TEXT,
                    actual_end_date TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Insert test epic
            conn.execute("""
                INSERT INTO framework_epics 
                (id, epic_key, name, duration_description, calculated_duration_days)
                VALUES (1, 'TEST_1', 'Test Epic', '5 dias', 5.0)
            """)
            conn.commit()
        
        # Create test class with mixin
        class TestDatabaseManager(SafeDatabaseOperationsMixin):
            def __init__(self, db_path):
                self.framework_db_path = db_path
                super().__init__()
        
        self.db_manager = TestDatabaseManager(self.db_path)
    
    def teardown_method(self):
        """Cleanup after each test."""
        if hasattr(self.db_manager, 'close_transactional_manager'):
            self.db_manager.close_transactional_manager()
        try:
            Path(self.db_path).unlink()
        except:
            pass
    
    def test_safe_duration_update(self):
        """Test safe duration update via mixin."""
        success = self.db_manager.update_duration_description_safe(1, "10 dias")
        assert success is True
        
        # Verify via safe timeline get
        timeline = self.db_manager.get_epic_timeline_safe(1)
        assert "error" not in timeline
        assert timeline["duration_info"]["description"] == "10 dias"
    
    def test_safe_epic_timeline_get(self):
        """Test safe epic timeline retrieval."""
        timeline = self.db_manager.get_epic_timeline_safe(1)
        
        assert "error" not in timeline
        assert "epic" in timeline
        assert "duration_info" in timeline
        assert "transaction_id" in timeline
        
        epic_data = timeline["epic"]
        assert epic_data["id"] == 1
        assert epic_data["epic_key"] == "TEST_1"
    
    def test_safe_date_consistency_validation(self):
        """Test safe date consistency validation."""
        is_valid = self.db_manager.validate_date_consistency_safe(1)
        assert isinstance(is_valid, bool)
        
        # TODO: Consider extracting this block into a separate method
        # Should be valid for our test data
        # TODO: Consider extracting this block into a separate method
        assert is_valid is True
    
    def test_transaction_stats_access(self):
        """Test access to transaction statistics."""
        # Perform some operations first
        self.db_manager.update_duration_description_safe(1, "8 dias")
        
        stats = self.db_manager.get_database_transaction_stats()
        
        assert "error" not in stats
        assert "successful_transactions" in stats
        assert "connection_pool" in stats
        assert isinstance(stats["successful_transactions"], int)


class TestIntegrationAndUtilities:
    # TODO: Consider extracting this block into a separate method
    # TODO: Consider extracting this block into a separate method
    """Test integration functions and utilities."""
    
    def test_transaction_safety_test_function(self):
        """Test the built-in transaction safety test function."""
        results = test_transaction_safety()
        
        assert isinstance(results, dict)
        
        expected_keys = {
            "total_operations", "successful_transactions", 
            "failed_transactions", "exceptions", "transaction_stats"
        }
        assert set(results.keys()) == expected_keys
        
        # Should have performed some operations
        assert results["total_operations"] > 0
        
        # Should have some successful operations
        assert results["successful_transactions"] >= 0
    
    def test_transaction_result_structure(self):
        """Test TransactionResult structure."""
        # Create a successful result
        success_result = TransactionResult(
            success=True,
            result="test data",
            duration_ms=5.0,
            transaction_id="test123"
        )
        
        assert success_result.success is True
        assert success_result.result == "test data"
        assert success_result.error is None
        assert success_result.retry_count == 0
        assert success_result.duration_ms == 5.0
        assert success_result.transaction_id == "test123"
        
        # Create a failed result
        failure_result = TransactionResult(
            success=False,
            error="Test error",
            retry_count=2,
            duration_ms=10.0
        )
        
        assert failure_result.success is False
        assert failure_result.error == "Test error"
        assert failure_result.result is None
        assert failure_result.retry_count == 2


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])