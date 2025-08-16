"""
🧪 Load Testing Scenarios

Tests for database performance under concurrent load and high-volume scenarios.
Ensures the pagination system performs well under realistic production conditions.
"""

import sqlite3
import threading
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from streamlit_extension.utils.database import DatabaseManager


def _create_db(path, count=100):
    """Create test database with sample data."""
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE items (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)")
    conn.executemany("INSERT INTO items (name) VALUES (?)", [(f"name{i}",) for i in range(count)])
    conn.commit()
    conn.close()


class TestLoadScenarios:
    """Test database performance under various load conditions."""

    def test_concurrent_pagination_requests(self, tmp_path):
        """Test concurrent pagination requests performance."""
        db_path = tmp_path / "test.db"
        _create_db(db_path, 100)
        db = DatabaseManager(framework_db_path=str(db_path))
        
        results = []
        errors = []

        def worker():
            """Worker function for concurrent access."""
            try:
                res = db.get_paginated_results("items", page=1, per_page=10)
                results.append(len(res.items))
            except Exception as e:
                errors.append(str(e))

        # Create and start multiple threads
        threads = [threading.Thread(target=worker) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Verify all requests succeeded
        assert len(errors) == 0, f"Errors during concurrent access: {errors}"
        assert len(results) == 5
        assert sum(results) == 50  # 5 threads × 10 items each

    def test_high_volume_pagination(self, tmp_path):
        """Test pagination with high-volume data."""
        db_path = tmp_path / "test.db"
        _create_db(db_path, 1000)  # Larger dataset
        db = DatabaseManager(framework_db_path=str(db_path))
        
        # Test multiple pages
        total_items = 0
        for page in range(1, 6):  # Pages 1-5
            result = db.get_paginated_results("items", page=page, per_page=20)
            total_items += len(result.items)
            
            # Performance checks
            assert result.query_time_ms < 1000  # Should be under 1 second
            assert len(result.items) <= 20
            assert result.total_count == 1000

        assert total_items == 100  # 5 pages × 20 items

    def test_concurrent_different_tables(self, tmp_path):
        """Test concurrent access to different tables."""
        db_path = tmp_path / "test.db"
        
        # Create database with multiple tables
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE items (id INTEGER PRIMARY KEY, name TEXT)")
        conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT)")
        conn.executemany("INSERT INTO items (name) VALUES (?)", [(f"item{i}",) for i in range(50)])
        conn.executemany("INSERT INTO users (email) VALUES (?)", [(f"user{i}@test.com",) for i in range(50)])
        conn.commit()
        conn.close()
        
        db = DatabaseManager(framework_db_path=str(db_path))
        results = []
        errors = []

        def worker_items():
            try:
                res = db.get_paginated_results("items", page=1, per_page=10)
                results.append(("items", len(res.items)))
            except Exception as e:
                errors.append(f"items: {e}")

        def worker_users():
            try:
                res = db.get_paginated_results("users", page=1, per_page=10)  
                results.append(("users", len(res.items)))
            except Exception as e:
                errors.append(f"users: {e}")

        # Start concurrent access to different tables
        threads = []
        for _ in range(3):
            threads.append(threading.Thread(target=worker_items))
            threads.append(threading.Thread(target=worker_users))
            
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Verify results
        assert len(errors) == 0, f"Errors: {errors}"
        assert len(results) == 6  # 3 items + 3 users
        
        items_results = [r for r in results if r[0] == "items"]
        users_results = [r for r in results if r[0] == "users"]
        
        assert len(items_results) == 3
        assert len(users_results) == 3
        assert all(r[1] == 10 for r in items_results)
        assert all(r[1] == 10 for r in users_results)

    def test_memory_efficiency_large_offset(self, tmp_path):
        """Test memory efficiency with large offset pagination."""
        db_path = tmp_path / "test.db"
        _create_db(db_path, 200)
        db = DatabaseManager(framework_db_path=str(db_path))
        
        # Test pagination with large offset (potential performance issue)
        result = db.get_paginated_results("items", page=10, per_page=10)  # OFFSET 90
        
        assert len(result.items) == 10
        assert result.page == 10
        assert result.total_count == 200
        assert result.query_time_ms >= 0  # Performance metric recorded

    def test_stress_test_rapid_requests(self, tmp_path):
        """Stress test with rapid sequential requests."""
        db_path = tmp_path / "test.db"
        _create_db(db_path, 150)
        db = DatabaseManager(framework_db_path=str(db_path))
        
        # Rapid sequential requests
        start_time = threading.Event()
        results = []
        errors = []

        def rapid_worker():
            start_time.wait()  # Wait for all threads to be ready
            try:
                for _ in range(10):  # 10 rapid requests per thread
                    res = db.get_paginated_results("items", page=1, per_page=5)
                    results.append(len(res.items))
            except Exception as e:
                errors.append(str(e))

        # Start multiple threads
        threads = [threading.Thread(target=rapid_worker) for _ in range(3)]
        for t in threads:
            t.start()
            
        # Start all at once
        start_time.set()
        
        for t in threads:
            t.join()

        # Verify no errors and correct results
        assert len(errors) == 0, f"Errors during stress test: {errors}"
        assert len(results) == 30  # 3 threads × 10 requests
        assert all(r == 5 for r in results)  # Each request should return 5 items

    def test_error_handling_under_load(self, tmp_path):
        """Test error handling during concurrent access."""
        db_path = tmp_path / "test.db"
        _create_db(db_path, 50)
        db = DatabaseManager(framework_db_path=str(db_path))
        
        success_count = 0
        error_count = 0
        results_lock = threading.Lock()

        def worker_with_errors():
            nonlocal success_count, error_count
            try:
                # Mix of valid and invalid requests
                if threading.current_thread().name.endswith("0"):
                    # Invalid table name (should fail gracefully)
                    db.get_paginated_results("invalid_table", page=1)
                else:
                    # Valid request
                    result = db.get_paginated_results("items", page=1, per_page=10)
                    with results_lock:
                        success_count += 1
            except ValueError:
                # Expected error for invalid table
                with results_lock:
                    error_count += 1
            except Exception:
                # Unexpected errors
                with results_lock:
                    error_count += 1

        # Start threads with mixed valid/invalid requests
        threads = [threading.Thread(target=worker_with_errors, name=f"thread_{i}") for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should have some successes and some controlled errors
        assert success_count > 0
        assert error_count > 0
        assert success_count + error_count == 10