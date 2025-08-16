#!/usr/bin/env python3
"""
🔧 Connection Pool Debug Test Suite

Comprehensive testing of connection pool behavior under various stress conditions
to identify potential issues, deadlocks, and performance bottlenecks.
"""

import sqlite3
import threading
import time
import pytest
from pathlib import Path

from duration_system.database_transactions import DatabaseConnectionPool


def create_test_db(db_path):
    """Create a test database with sample data."""
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE test_table (id INTEGER PRIMARY KEY, data TEXT)")
    conn.execute("INSERT INTO test_table (data) VALUES ('test_data')")
    conn.commit()
    conn.close()


class TestConnectionPoolDebug:
    """Comprehensive connection pool debugging tests."""

    def test_connection_pool_limit_stress(self, tmp_path):
        """Test connection pool behavior under stress with limited connections."""
        db_path = tmp_path / "stress_test.db"
        create_test_db(db_path)
        
        # Very small pool to force contention
        pool = DatabaseConnectionPool(str(db_path), max_connections=2, connection_timeout=1.0)
        
        results = []
        errors = []
        
        def worker(worker_id):
            try:
                start_time = time.time()
                with pool.get_connection() as conn:
                    # Simulate some work
                    conn.execute("SELECT * FROM test_table")
                    time.sleep(0.1)  # Hold connection briefly
                    results.append({
                        'worker_id': worker_id,
                        'duration': time.time() - start_time,
                        'success': True
                    })
            except Exception as e:
                errors.append({
                    'worker_id': worker_id,
                    'error': str(e),
                    'duration': time.time() - start_time
                })
        
        # Start 10 workers competing for 2 connections
        threads = []
        for i in range(10):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join(timeout=5.0)  # Prevent hanging
        
        pool.close_all()
        
        print(f"\nConnection Pool Stress Test Results:")
        print(f"Successful operations: {len(results)}")
        print(f"Failed operations: {len(errors)}")
        print(f"Pool stats: {pool.stats}")
        
        if errors:
            print("Errors encountered:")
            for error in errors:
                print(f"  Worker {error['worker_id']}: {error['error']}")
        
        # All workers should succeed or timeout gracefully
        assert len(results) + len(errors) == 10
        assert len(errors) <= 5  # Some timeouts are acceptable under stress

    def test_connection_pool_deadlock_prevention(self, tmp_path):
        """Test for potential deadlocks in connection pool."""
        db_path = tmp_path / "deadlock_test.db"
        create_test_db(db_path)
        
        pool = DatabaseConnectionPool(str(db_path), max_connections=1, connection_timeout=2.0)
        
        deadlock_detected = False
        results = []
        
        def worker(worker_id):
            nonlocal deadlock_detected
            try:
                start_time = time.time()
                with pool.get_connection() as conn:
                    # Simulate nested connection attempt (should timeout, not deadlock)
                    conn.execute("SELECT 1")
                    time.sleep(0.5)
                    results.append(worker_id)
                duration = time.time() - start_time
                
                # If this takes too long, we might have a deadlock
                if duration > 5.0:
                    deadlock_detected = True
                    
            except Exception as e:
                # Timeouts are expected and acceptable
                if "timeout" not in str(e).lower():
                    deadlock_detected = True
        
        # Start multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait with timeout to detect deadlocks
        for thread in threads:
            thread.join(timeout=10.0)
            if thread.is_alive():
                deadlock_detected = True
                print(f"Warning: Thread appears to be deadlocked")
        
        pool.close_all()
        
        print(f"\nDeadlock Prevention Test Results:")
        print(f"Successful workers: {results}")
        print(f"Deadlock detected: {deadlock_detected}")
        print(f"Pool stats: {pool.stats}")
        
        assert not deadlock_detected, "Potential deadlock detected in connection pool"

    def test_connection_pool_health_monitoring(self, tmp_path):
        """Test connection health monitoring and recovery."""
        db_path = tmp_path / "health_test.db"
        create_test_db(db_path)
        
        pool = DatabaseConnectionPool(str(db_path), max_connections=3, connection_timeout=1.0)
        
        # Test normal operation
        with pool.get_connection() as conn:
            result = conn.execute("SELECT COUNT(*) FROM test_table").fetchone()
            assert result[0] == 1
        
        # Test connection health after normal operation
        initial_stats = pool.stats.copy()
        
        # Test multiple rapid connections
        for i in range(5):
            with pool.get_connection() as conn:
                conn.execute("SELECT 1")
        
        final_stats = pool.stats.copy()
        
        print(f"\nConnection Health Test Results:")
        print(f"Initial stats: {initial_stats}")
        print(f"Final stats: {final_stats}")
        print(f"Connections created: {final_stats['connections_created']}")
        print(f"Connections reused: {final_stats['connections_reused']}")
        
        pool.close_all()
        
        # Verify that pool is reusing connections efficiently
        assert final_stats['connections_reused'] >= 2, "Pool should reuse connections"
        assert final_stats['connections_created'] <= 3, "Pool should not create too many connections"

    def test_connection_pool_timeout_behavior(self, tmp_path):
        """Test connection pool timeout behavior under contention."""
        db_path = tmp_path / "timeout_test.db"
        create_test_db(db_path)
        
        # Short timeout to test timeout behavior
        pool = DatabaseConnectionPool(str(db_path), max_connections=1, connection_timeout=0.5)
        
        timeout_count = 0
        success_count = 0
        
        def worker():
            nonlocal timeout_count, success_count
            try:
                with pool.get_connection() as conn:
                    conn.execute("SELECT 1")
                    time.sleep(0.8)  # Hold connection longer than timeout
                success_count += 1
            except Exception as e:
                if "timeout" in str(e).lower():
                    timeout_count += 1
                else:
                    raise
        
        # Start 3 workers for 1 connection
        threads = []
        for i in range(3):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        pool.close_all()
        
        print(f"\nTimeout Behavior Test Results:")
        print(f"Successful connections: {success_count}")
        print(f"Timed out connections: {timeout_count}")
        print(f"Pool stats: {pool.stats}")
        
        # Should have 1 success and 2 timeouts
        assert success_count >= 1, "At least one connection should succeed"
        assert timeout_count >= 1, "Some connections should timeout as expected"
        assert success_count + timeout_count == 3, "All workers should complete"

    def test_connection_pool_emergency_connections(self, tmp_path):
        """Test emergency connection behavior when pool is exhausted."""
        db_path = tmp_path / "emergency_test.db"
        create_test_db(db_path)
        
        pool = DatabaseConnectionPool(str(db_path), max_connections=1, connection_timeout=0.2)
        
        emergency_used = False
        
        def test_emergency():
            nonlocal emergency_used
            with pool.get_connection() as conn:
                # This should get an emergency connection since pool is exhausted
                result = conn.execute("SELECT 1").fetchone()
                if result:
                    emergency_used = True
        
        # Hold the only pooled connection
        with pool.get_connection() as primary_conn:
            primary_conn.execute("SELECT 1")
            
            # Start thread that should get emergency connection
            thread = threading.Thread(target=test_emergency)
            thread.start()
            thread.join(timeout=2.0)
            
            assert not thread.is_alive(), "Emergency connection thread should complete"
        
        pool.close_all()
        
        print(f"\nEmergency Connection Test Results:")
        print(f"Emergency connection used: {emergency_used}")
        print(f"Pool stats: {pool.stats}")
        
        assert emergency_used, "Emergency connection should be used when pool is exhausted"


if __name__ == "__main__":
    print("🔧 Connection Pool Debug Test Suite")
    print("=" * 50)
    
    # Run tests manually for debugging
    import tempfile
    import shutil
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        test_instance = TestConnectionPoolDebug()
        
        try:
            print("\n1. Testing connection pool limit stress...")
            test_instance.test_connection_pool_limit_stress(tmp_path)
            print("✅ Stress test completed")
        except Exception as e:
            print(f"❌ Stress test failed: {e}")
        
        try:
            print("\n2. Testing deadlock prevention...")
            test_instance.test_connection_pool_deadlock_prevention(tmp_path)
            print("✅ Deadlock prevention test completed")
        except Exception as e:
            print(f"❌ Deadlock prevention test failed: {e}")
        
        try:
            print("\n3. Testing health monitoring...")
            test_instance.test_connection_pool_health_monitoring(tmp_path)
            print("✅ Health monitoring test completed")
        except Exception as e:
            print(f"❌ Health monitoring test failed: {e}")
        
        try:
            print("\n4. Testing timeout behavior...")
            test_instance.test_connection_pool_timeout_behavior(tmp_path)
            print("✅ Timeout behavior test completed")
        except Exception as e:
            print(f"❌ Timeout behavior test failed: {e}")
        
        try:
            print("\n5. Testing emergency connections...")
            test_instance.test_connection_pool_emergency_connections(tmp_path)
            print("✅ Emergency connection test completed")
        except Exception as e:
            print(f"❌ Emergency connection test failed: {e}")
    
    print("\n🎯 Connection Pool Debug Suite completed!")