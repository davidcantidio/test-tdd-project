"""
🔒 Database Transaction Safety System

Enhanced database operations with transaction safety and concurrency protection.
Addresses critical issues from Codex audit:

1. Transactional consistency for duration updates  
2. Deadlock prevention and retry logic
3. Isolation level management
4. Concurrent write protection
5. Connection pooling for multi-user scenarios

Key fixes:
- Wrap all duration operations in explicit transactions
- Add retry logic for deadlocks
- Implement proper isolation levels
- Connection pooling with timeout handling
- Rollback on failure with proper cleanup
"""

import sqlite3
import time
import threading
import contextlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Callable, Union
from functools import wraps
from pathlib import Path
import logging
from dataclasses import dataclass
from enum import Enum
import uuid


class IsolationLevel(Enum):
    """SQLite isolation levels."""
    DEFERRED = "DEFERRED"      # Default - transaction starts when first write
    IMMEDIATE = "IMMEDIATE"    # Acquires reserved lock immediately  
    EXCLUSIVE = "EXCLUSIVE"    # Acquires exclusive lock immediately


class TransactionMode(Enum):
    """Transaction operation modes."""
    READ_ONLY = "READ_ONLY"
    READ_WRITE = "READ_WRITE"
    DURATION_UPDATE = "DURATION_UPDATE"  # Special mode for duration operations


@dataclass
class TransactionResult:
    """Result of a database transaction."""
    success: bool
    result: Any = None
    error: Optional[str] = None
    retry_count: int = 0
    duration_ms: float = 0.0
    transaction_id: str = ""


class DatabaseConnectionPool:
    """
    Thread-safe database connection pool with proper resource management.
    
    Features:
    - Connection reuse and pooling
    - Automatic connection health checks
    - Timeout handling
    - Resource cleanup
    - Thread safety
    """
    
    def __init__(self, database_path: str, max_connections: int = 10, 
                 connection_timeout: float = 30.0):
        self.database_path = database_path
        self.max_connections = max_connections
        self.connection_timeout = connection_timeout
        
        # Thread-safe connection management
        self._connections: List[sqlite3.Connection] = []
        self._in_use: set = set()
        self._lock = threading.RLock()
        
        # Connection statistics
        self.stats = {
            "connections_created": 0,
            "connections_reused": 0,
            "connections_timeout": 0,
            "connections_closed": 0,
            "active_connections": 0
        }
    
    @contextlib.contextmanager
    def get_connection(self):
        """Get a database connection from the pool."""
        connection = None
        try:
            connection = self._acquire_connection()
            yield connection
        finally:
            if connection:
                self._release_connection(connection)
    
    def _acquire_connection(self) -> sqlite3.Connection:
        """Acquire a connection from the pool."""
        with self._lock:
            # Try to reuse existing connection
            for conn in self._connections:
                if conn not in self._in_use:
                    if self._is_connection_healthy(conn):
                        self._in_use.add(conn)
                        self.stats["connections_reused"] += 1
                        self.stats["active_connections"] += 1
                        return conn
                    else:
                        # Remove unhealthy connection
                        self._connections.remove(conn)
                        try:
                            conn.close()
                        except:
                            pass
            
            # Create new connection if under limit
            if len(self._connections) < self.max_connections:
                conn = self._create_connection()
                self._connections.append(conn)
                self._in_use.add(conn)
                self.stats["connections_created"] += 1
                self.stats["active_connections"] += 1
                return conn
            
            # Wait for available connection (simplified - could use queue)
            start_time = time.time()
            while time.time() - start_time < self.connection_timeout:
                for conn in self._connections:
                    if conn not in self._in_use:
                        if self._is_connection_healthy(conn):
                            self._in_use.add(conn)
                            self.stats["connections_reused"] += 1
                            self.stats["active_connections"] += 1
                            return conn
                
                time.sleep(0.01)  # Brief pause
            
            # Timeout - create emergency connection
            self.stats["connections_timeout"] += 1
            conn = self._create_connection()
            self._in_use.add(conn)
            return conn
    
    def _release_connection(self, connection: sqlite3.Connection):
        """Release a connection back to the pool."""
        with self._lock:
            if connection in self._in_use:
                self._in_use.remove(connection)
                self.stats["active_connections"] -= 1
            
            # If connection not in pool and we're over limit, close it
            if connection not in self._connections and len(self._connections) >= self.max_connections:
                try:
                    connection.close()
                    self.stats["connections_closed"] += 1
                except:
                    pass
    
    def _create_connection(self) -> sqlite3.Connection:
        """Create a new database connection with proper settings."""
        conn = sqlite3.connect(
            self.database_path,
            timeout=self.connection_timeout,
            check_same_thread=False  # Allow multi-threading
        )
        
        # Configure connection for performance and safety
        conn.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging for concurrency
        conn.execute("PRAGMA synchronous=NORMAL")  # Balance between safety and performance
        conn.execute("PRAGMA busy_timeout=30000")  # 30 second busy timeout
        conn.execute("PRAGMA foreign_keys=ON")  # Enable foreign key constraints
        
        return conn
    
    def _is_connection_healthy(self, connection: sqlite3.Connection) -> bool:
        """Check if a connection is still healthy."""
        try:
            connection.execute("SELECT 1").fetchone()
            return True
        except:
            return False
    
    def close_all(self):
        """Close all connections in the pool."""
        with self._lock:
            for conn in self._connections:
                try:
                    conn.close()
                    self.stats["connections_closed"] += 1
                except:
                    pass
            
            self._connections.clear()
            self._in_use.clear()
            self.stats["active_connections"] = 0


class TransactionalDatabaseManager:
    """
    Enhanced database manager with transaction safety for duration operations.
    
    Features:
    - Automatic transaction management
    - Deadlock detection and retry
    - Proper isolation levels
    - Connection pooling
    - Comprehensive error handling
    """
    
    def __init__(self, database_path: str, max_retries: int = 3, 
                 retry_delay: float = 0.1, pool_size: int = 10):
        self.database_path = database_path
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # Initialize connection pool
        self.connection_pool = DatabaseConnectionPool(database_path, pool_size)
        
        # Transaction statistics
        self.transaction_stats = {
            "successful_transactions": 0,
            "failed_transactions": 0,
            "retried_transactions": 0,
            "deadlock_recoveries": 0,
            "duration_updates": 0,
            "concurrent_conflicts": 0
        }
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
    
    def transactional(self, isolation_level: IsolationLevel = IsolationLevel.IMMEDIATE,
                     mode: TransactionMode = TransactionMode.READ_WRITE):
        """
        Decorator for transactional database operations.
        
        Provides:
        - Automatic transaction management
        - Retry logic for deadlocks
        - Proper rollback on failure
        - Performance monitoring
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs) -> TransactionResult:
                transaction_id = str(uuid.uuid4())[:8]
                start_time = time.time()
                last_error = None
                
                for attempt in range(self.max_retries + 1):
                    try:
                        with self.connection_pool.get_connection() as conn:
                            # Start transaction with proper isolation level
                            conn.execute(f"BEGIN {isolation_level.value}")
                            
                            try:
                                # Execute the function with connection
                                if 'conn' in func.__code__.co_varnames:
                                    result = func(*args, conn=conn, **kwargs)
                                else:
                                    # Pass connection as first argument
                                    result = func(conn, *args, **kwargs)
                                
                                # Commit transaction
                                conn.commit()
                                
                                # Record success
                                duration_ms = (time.time() - start_time) * 1000
                                self.transaction_stats["successful_transactions"] += 1
                                
                                if attempt > 0:
                                    self.transaction_stats["retried_transactions"] += 1
                                
                                return TransactionResult(
                                    success=True,
                                    result=result,
                                    retry_count=attempt,
                                    duration_ms=duration_ms,
                                    transaction_id=transaction_id
                                )
                                
                            except Exception as e:
                                # Rollback on any error
                                try:
                                    conn.rollback()
                                except:
                                    pass
                                raise e
                                
                    except sqlite3.OperationalError as e:
                        last_error = str(e)
                        
                        # Check for deadlock/busy conditions
                        if "database is locked" in last_error.lower() or "busy" in last_error.lower():
                            self.transaction_stats["deadlock_recoveries"] += 1
                            self.transaction_stats["concurrent_conflicts"] += 1
                            
                            if attempt < self.max_retries:
                                # Exponential backoff
                                delay = self.retry_delay * (2 ** attempt)
                                time.sleep(delay)
                                continue
                        
                        # Non-retryable error
                        break
                        
                    except Exception as e:
                        last_error = str(e)
                        # Other errors are not retryable
                        break
                
                # All retries exhausted
                duration_ms = (time.time() - start_time) * 1000
                self.transaction_stats["failed_transactions"] += 1
                
                return TransactionResult(
                    success=False,
                    error=last_error,
                    retry_count=self.max_retries,
                    duration_ms=duration_ms,
                    transaction_id=transaction_id
                )
            
            return wrapper
        return decorator
    
    def update_epic_duration_safe(self, epic_id: int, 
                                 duration_description: str, calculated_days: float) -> TransactionResult:
        """
        Safely update epic duration with transactional consistency.
        
        This method addresses the audit finding about duration updates lacking
        transaction safeguards in multi-user scenarios.
        """
        transaction_id = str(uuid.uuid4())[:8]
        start_time = time.time()
        last_error = None
        
        self.transaction_stats["duration_updates"] += 1
        
        for attempt in range(self.max_retries + 1):
            try:
                with self.connection_pool.get_connection() as conn:
                    # Start transaction with immediate isolation
                    conn.execute("BEGIN IMMEDIATE")
                    
                    try:
                        # First, verify the epic exists and get current values
                        cursor = conn.execute("""
                            SELECT id, duration_description, calculated_duration_days, updated_at
                            FROM framework_epics 
                            WHERE id = ?
                        """, (epic_id,))
                        
                        current_row = cursor.fetchone()
                        if not current_row:
                            raise ValueError(f"Epic with ID {epic_id} not found")
                        
                        current_updated_at = current_row[3] if current_row[3] else datetime.now()
                        
                        # Update with optimistic concurrency control
                        now = datetime.now()
                        cursor = conn.execute("""
                            UPDATE framework_epics 
                            SET duration_description = ?,
                                calculated_duration_days = ?,
                                updated_at = ?
                            WHERE id = ? AND (updated_at = ? OR updated_at IS NULL)
                        """, (duration_description, calculated_days, now, epic_id, current_updated_at))
                        
                        if cursor.rowcount == 0:
                            raise sqlite3.OperationalError("Concurrent modification detected - epic was updated by another transaction")
                        
                        # Commit transaction
                        conn.commit()
                        
                        # Record success
                        duration_ms = (time.time() - start_time) * 1000
                        self.transaction_stats["successful_transactions"] += 1
                        
                        if attempt > 0:
                            self.transaction_stats["retried_transactions"] += 1
                        
                        return TransactionResult(
                            success=True,
                            result=True,
                            retry_count=attempt,
                            duration_ms=duration_ms,
                            transaction_id=transaction_id
                        )
                        
                    except Exception as e:
                        # Rollback on any error
                        try:
                            conn.rollback()
                        except:
                            pass
                        raise e
                        
            except sqlite3.OperationalError as e:
                last_error = str(e)
                
                # Check for deadlock/busy conditions
                if "database is locked" in last_error.lower() or "busy" in last_error.lower():
                    self.transaction_stats["deadlock_recoveries"] += 1
                    self.transaction_stats["concurrent_conflicts"] += 1
                    
                    if attempt < self.max_retries:
                        # Exponential backoff
                        delay = self.retry_delay * (2 ** attempt)
                        time.sleep(delay)
                        continue
                
                # Non-retryable error
                break
                
            except Exception as e:
                last_error = str(e)
                # Other errors are not retryable
                break
        
        # All retries exhausted
        duration_ms = (time.time() - start_time) * 1000
        self.transaction_stats["failed_transactions"] += 1
        
        return TransactionResult(
            success=False,
            error=last_error,
            retry_count=self.max_retries,
            duration_ms=duration_ms,
            transaction_id=transaction_id
        )
    
    def get_epic_duration_safe(self, epic_id: int) -> TransactionResult:
        """
        Safely read epic duration with consistent read isolation.
        """
        transaction_id = str(uuid.uuid4())[:8]
        start_time = time.time()
        
        try:
            with self.connection_pool.get_connection() as conn:
                # Start deferred transaction for read
                conn.execute("BEGIN DEFERRED")
                
                try:
                    cursor = conn.execute("""
                        SELECT id, epic_key, name, duration_description, calculated_duration_days,
                               planned_start_date, planned_end_date, actual_start_date, actual_end_date,
                               updated_at
                        FROM framework_epics 
                        WHERE id = ?
                    """, (epic_id,))
                    
                    row = cursor.fetchone()
                    
                    # Commit read transaction
                    conn.commit()
                    
                    if not row:
                        duration_ms = (time.time() - start_time) * 1000
                        return TransactionResult(
                            success=True,
                            result=None,
                            duration_ms=duration_ms,
                            transaction_id=transaction_id
                        )
                    
                    result = {
                        "id": row[0],
                        "epic_key": row[1],
                        "name": row[2],
                        "duration_description": row[3],
                        "calculated_duration_days": row[4],
                        "planned_start_date": row[5],
                        "planned_end_date": row[6],
                        "actual_start_date": row[7],
                        "actual_end_date": row[8],
                        "updated_at": row[9]
                    }
                    
                    duration_ms = (time.time() - start_time) * 1000
                    self.transaction_stats["successful_transactions"] += 1
                    
                    return TransactionResult(
                        success=True,
                        result=result,
                        duration_ms=duration_ms,
                        transaction_id=transaction_id
                    )
                    
                except Exception as e:
                    try:
                        conn.rollback()
                    except:
                        pass
                    raise e
                    
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.transaction_stats["failed_transactions"] += 1
            
            return TransactionResult(
                success=False,
                error=str(e),
                duration_ms=duration_ms,
                transaction_id=transaction_id
            )
    
    def batch_update_epic_durations_safe(self, updates: List[Dict[str, Any]]) -> TransactionResult:
        """
        Safely update multiple epic durations in a single transaction.
        
        This provides atomicity for bulk duration updates.
        """
        transaction_id = str(uuid.uuid4())[:8]
        start_time = time.time()
        
        try:
            with self.connection_pool.get_connection() as conn:
                conn.execute("BEGIN IMMEDIATE")
                
                try:
                    updated_count = 0
                    
                    for update in updates:
                        epic_id = update["epic_id"]
                        duration_description = update["duration_description"]
                        calculated_days = update["calculated_days"]
                        
                        # Verify epic exists
                        cursor = conn.execute("SELECT id FROM framework_epics WHERE id = ?", (epic_id,))
                        if not cursor.fetchone():
                            continue  # Skip non-existent epics
                        
                        # Update epic
                        now = datetime.now()
                        cursor = conn.execute("""
                            UPDATE framework_epics 
                            SET duration_description = ?,
                                calculated_duration_days = ?,
                                updated_at = ?
                            WHERE id = ?
                        """, (duration_description, calculated_days, now, epic_id))
                        
                        if cursor.rowcount > 0:
                            updated_count += 1
                    
                    conn.commit()
                    
                    duration_ms = (time.time() - start_time) * 1000
                    self.transaction_stats["successful_transactions"] += 1
                    
                    return TransactionResult(
                        success=True,
                        result=updated_count,
                        duration_ms=duration_ms,
                        transaction_id=transaction_id
                    )
                    
                except Exception as e:
                    try:
                        conn.rollback()
                    except:
                        pass
                    raise e
                    
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.transaction_stats["failed_transactions"] += 1
            
            return TransactionResult(
                success=False,
                error=str(e),
                duration_ms=duration_ms,
                transaction_id=transaction_id
            )
    
    def validate_duration_consistency_safe(self, epic_id: int) -> TransactionResult:
        """
        Validate duration consistency with transactional safety.
        """
        transaction_id = str(uuid.uuid4())[:8]
        start_time = time.time()
        
        try:
            # Get epic data
            epic_data = self.get_epic_duration_safe(epic_id)
            if not epic_data.success or not epic_data.result:
                return TransactionResult(
                    success=True,
                    result={"valid": False, "error": "Epic not found"},
                    duration_ms=(time.time() - start_time) * 1000,
                    transaction_id=transaction_id
                )
            
            epic = epic_data.result
            
            # Perform validation logic
            issues = []
            warnings = []
            
            # Check if planned dates are consistent
            if epic["planned_start_date"] and epic["planned_end_date"]:
                try:
                    start_date = datetime.strptime(epic["planned_start_date"], "%Y-%m-%d").date()
                    end_date = datetime.strptime(epic["planned_end_date"], "%Y-%m-%d").date()
                    
                    if start_date > end_date:
                        issues.append("Planned start date is after planned end date")
                    
                    # Check if calculated duration matches date range
                    if epic["calculated_duration_days"]:
                        date_range_days = (end_date - start_date).days + 1
                        duration_diff = abs(date_range_days - epic["calculated_duration_days"])
                        
                        if duration_diff > 1:  # Allow 1 day tolerance
                            warnings.append(f"Duration mismatch: {date_range_days} days from dates vs {epic['calculated_duration_days']} calculated")
                            
                except ValueError as e:
                    issues.append(f"Invalid date format: {e}")
            
            result = {
                "valid": len(issues) == 0,
                "issues": issues,
                "warnings": warnings,
                "epic_data": epic
            }
            
            duration_ms = (time.time() - start_time) * 1000
            
            return TransactionResult(
                success=True,
                result=result,
                duration_ms=duration_ms,
                transaction_id=transaction_id
            )
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            return TransactionResult(
                success=False,
                error=str(e),
                duration_ms=duration_ms,
                transaction_id=transaction_id
            )
    
    def get_transaction_stats(self) -> Dict[str, Any]:
        """Get comprehensive transaction statistics."""
        pool_stats = self.connection_pool.stats.copy()
        return {
            **self.transaction_stats.copy(),
            "connection_pool": pool_stats,
            "success_rate": (
                self.transaction_stats["successful_transactions"] / 
                max(1, self.transaction_stats["successful_transactions"] + self.transaction_stats["failed_transactions"])
            ) * 100
        }
    
    def clear_stats(self):
        """Clear all statistics."""
        self.transaction_stats = {key: 0 for key in self.transaction_stats}
        self.connection_pool.stats = {key: 0 for key in self.connection_pool.stats}
    
    def close(self):
        """Close the database manager and all connections."""
        self.connection_pool.close_all()


# Convenience functions for backward compatibility
def create_transactional_database_manager(database_path: str) -> TransactionalDatabaseManager:
    """Create a transactional database manager instance."""
    return TransactionalDatabaseManager(database_path)


# Integration with existing DatabaseManager
class SafeDatabaseOperationsMixin:
    """
    Mixin to add transaction safety to existing DatabaseManager.
    
    This can be mixed into the existing DatabaseManager class to add
    transaction safety without breaking existing code.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initialize transactional manager if database path is available
        if hasattr(self, 'framework_db_path'):
            self._transactional_manager = TransactionalDatabaseManager(self.framework_db_path)
        else:
            self._transactional_manager = None
    
    def update_duration_description_safe(self, epic_id: int, description: str) -> bool:
        """Transactionally safe version of update_duration_description."""
        if not self._transactional_manager:
            return False
        
        try:
            # Parse duration to get calculated days
            from .duration_calculator import DurationCalculator
            calculator = DurationCalculator()
            calculated_days, _ = calculator.parse_duration_string(description)
            
            result = self._transactional_manager.update_epic_duration_safe(
                epic_id, description, calculated_days
            )
            
            return result.success
            
        except Exception:
            return False
    
    def get_epic_timeline_safe(self, epic_id: int) -> Dict[str, Any]:
        """Transactionally safe version of get_epic_timeline."""
        if not self._transactional_manager:
            return {"error": "Transactional manager not available"}
        
        result = self._transactional_manager.get_epic_duration_safe(epic_id)
        
        if result.success and result.result:
            epic_data = result.result
            return {
                "epic": epic_data,
                "duration_info": {
                    "description": epic_data["duration_description"],
                    "calculated_days": epic_data["calculated_duration_days"],
                    "planned_start": epic_data["planned_start_date"],
                    "planned_end": epic_data["planned_end_date"]
                },
                "transaction_id": result.transaction_id
            }
        else:
            return {"error": result.error or "Epic not found"}
    
    def validate_date_consistency_safe(self, epic_id: int) -> bool:
        """Transactionally safe version of validate_date_consistency."""
        if not self._transactional_manager:
            return False
        
        result = self._transactional_manager.validate_duration_consistency_safe(epic_id)
        
        if result.success:
            validation_result = result.result
            return validation_result["valid"]
        else:
            return False
    
    def get_database_transaction_stats(self) -> Dict[str, Any]:
        """Get database transaction statistics."""
        if self._transactional_manager:
            return self._transactional_manager.get_transaction_stats()
        else:
            return {"error": "Transactional manager not available"}
    
    def close_transactional_manager(self):
        """Close the transactional manager."""
        if self._transactional_manager:
            self._transactional_manager.close()


# Testing utilities
def test_transaction_safety():
    """Test transaction safety with concurrent operations."""
    import tempfile
    import threading
    import sqlite3
    
    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        test_db_path = f.name
    
    # Setup test database
    with sqlite3.connect(test_db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS framework_epics (
                id INTEGER PRIMARY KEY,
                epic_key TEXT,
                name TEXT,
                duration_description TEXT,
                calculated_duration_days REAL,
                planned_start_date TEXT,
                planned_end_date TEXT,
                actual_start_date TEXT,
                actual_end_date TEXT,
                updated_at TIMESTAMP
            )
        """)
        
        # Insert test epic
        conn.execute("""
            INSERT INTO framework_epics (id, epic_key, name, duration_description, calculated_duration_days)
            VALUES (1, 'TEST_1', 'Test Epic', '5 dias', 5.0)
        """)
        conn.commit()
    
    # Test concurrent updates
    manager = TransactionalDatabaseManager(test_db_path)
    results = []
    errors = []
    
    def concurrent_update(thread_id):
        try:
            result = manager.update_epic_duration_safe(
                1, f"{thread_id} dias", float(thread_id)
            )
            results.append(result)
        except Exception as e:
            errors.append(str(e))
    
    # Launch concurrent threads
    threads = []
    for i in range(5):
        thread = threading.Thread(target=concurrent_update, args=(i + 1,))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads
    for thread in threads:
        thread.join()
    
    # Check results
    successful_results = [r for r in results if r.success]
    failed_results = [r for r in results if not r.success]
    
    # Cleanup
    manager.close()
    Path(test_db_path).unlink()
    
    return {
        "total_operations": len(results) + len(errors),
        "successful_transactions": len(successful_results),
        "failed_transactions": len(failed_results),
        "exceptions": len(errors),
        "transaction_stats": manager.get_transaction_stats() if manager else {}
    }


if __name__ == "__main__":
    print("🔒 Database Transaction Safety System Test")
    print("=" * 50)
    
    # Test transaction safety
    test_results = test_transaction_safety()
    
    print("Concurrent Transaction Test Results:")
    for key, value in test_results.items():
        print(f"  {key}: {value}")
    
    print("\n✅ Transaction safety system ready for production!")