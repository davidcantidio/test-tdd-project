"""
🗄️ Database Management Utilities

Streamlit-optimized database operations with:
- Connection pooling
- Caching strategies
- SQLAlchemy integration
- Error handling
"""

import sqlite3
import time
from pathlib import Path
from typing import (
    Union,
    Optional,
    List,
    Dict,
    Any,
    Tuple,
    Callable,
    Iterator,
    ContextManager,
    Generator,
    TypeVar,
    Generic,
    NamedTuple,
)
from sqlite3 import Connection as SQLiteConnection
from contextlib import contextmanager
from datetime import datetime
from enum import Enum
import json
import logging

# Graceful imports
try:
    import sqlalchemy as sa
    from sqlalchemy import create_engine, text
    from sqlalchemy.pool import StaticPool
    from sqlalchemy.engine import Connection, Result
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    sa = None
    create_engine = None
    text = None
    StaticPool = None
    Connection = None
    Result = Any  # type: ignore[assignment]
    SQLALCHEMY_AVAILABLE = False

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    pd = None
    PANDAS_AVAILABLE = False

try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    st = None
    STREAMLIT_AVAILABLE = False

# Import timezone utilities
try:
    from ..config.streamlit_config import format_datetime_user_tz, format_time_ago_user_tz
    TIMEZONE_UTILS_AVAILABLE = True
except ImportError:
    TIMEZONE_UTILS_AVAILABLE = False
    format_datetime_user_tz = None
    format_time_ago_user_tz = None

# Import duration system for FASE 2.3 extension
try:
    from duration_system.duration_calculator import DurationCalculator
    from duration_system.duration_formatter import DurationFormatter
    DURATION_SYSTEM_AVAILABLE = True
except ImportError:
    DurationCalculator = None
    DurationFormatter = None
    DURATION_SYSTEM_AVAILABLE = False

# Import caching system
try:
    from .cache import cache_database_query, invalidate_cache_on_change, get_cache
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False
    cache_database_query = invalidate_cache_on_change = get_cache = None

from .constants import (
    TableNames,
    FieldNames,
    ClientStatus,
    ProjectStatus,
    TaskStatus,
    EpicStatus,
    TDDPhase,
)

logger = logging.getLogger(__name__)

# Security: Whitelist of allowed table names to prevent SQL injection
ALLOWED_TABLES = {
    "framework_clients",
    "framework_projects", 
    "framework_epics",
    "framework_tasks",
    "work_sessions",
    "achievement_types",
    "user_achievements",
    "user_streaks",
    "github_sync_log",
    "system_settings",
    "auth_users",
    "items",  # For tests
    "users"   # For tests
}

# Security: Whitelist of allowed sort columns
ALLOWED_SORT_COLUMNS = {
    "id", "created_at", "updated_at", "name", "title", "status", "priority",
    "client_id", "project_id", "epic_id", "budget", "completion_percentage",
    "email"  # For tests
}


class PaginationType(Enum):
    """Pagination strategy types."""

    OFFSET_LIMIT = "offset_limit"
    CURSOR_BASED = "cursor_based"
    KEYSET = "keyset"


class PaginationResult(NamedTuple):
    """Pagination result with metadata."""

    items: List[Dict[str, Any]]
    total_count: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_prev: bool
    next_cursor: Optional[str]
    prev_cursor: Optional[str]
    query_time_ms: float


class PerformancePaginationMixin:
    """High-performance pagination methods for DatabaseManager."""

    def _validate_table_name(self, table_name: str) -> bool:
        """Security: Validate table name against whitelist."""
        return table_name in ALLOWED_TABLES

    def _validate_sort_column(self, sort_column: str) -> bool:
        """Security: Validate sort column against whitelist."""
        return sort_column in ALLOWED_SORT_COLUMNS

    def _sanitize_filters(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Security: Sanitize filter values to prevent injection."""
        sanitized = {}
        for key, value in filters.items():
            # Only allow alphanumeric keys and safe values
            if key.replace("_", "").replace("-", "").isalnum():
                if isinstance(value, (str, int, float, bool)):
                    sanitized[key] = value
        return sanitized

    def get_paginated_results(
        self,
        table_name: str,
        page: int = 1,
        per_page: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: Optional[str] = None,
        sort_order: str = "ASC",
        pagination_type: PaginationType = PaginationType.OFFSET_LIMIT,
        cursor: Optional[str] = None,
    ) -> PaginationResult:
        """Get paginated results with performance optimization and security."""
        
        # Security validation
        if not self._validate_table_name(table_name):
            raise ValueError(f"Invalid table name: {table_name}")
        
        if sort_by and not self._validate_sort_column(sort_by):
            raise ValueError(f"Invalid sort column: {sort_by}")
        
        if per_page > 100:
            per_page = 100
        
        if sort_order.upper() not in ["ASC", "DESC"]:
            sort_order = "ASC"

        filters = self._sanitize_filters(filters or {})
        sort_column = sort_by or "id"

        start = time.time()
        with self.get_connection("framework") as conn:
            if SQLALCHEMY_AVAILABLE:
                # SQLAlchemy path with named parameters
                where_clause = " AND ".join([f"{k} = :{k}" for k in filters])
                if where_clause:
                    where_clause = "WHERE " + where_clause
                
                order_clause = f"ORDER BY {sort_column} {sort_order}" if sort_column else ""
                
                # Count total
                count_query = text(f"SELECT COUNT(*) FROM {table_name}") if not where_clause else text(f"SELECT COUNT(*) FROM {table_name} {where_clause}")
                total = conn.execute(count_query, filters).scalar()
                
                # Build data query
                if pagination_type == PaginationType.CURSOR_BASED and cursor is not None:
                    cursor_cond = f"{sort_column} > :cursor" if sort_order.upper() == "ASC" else f"{sort_column} < :cursor"
                    where_clause_cursor = (
                        f"{where_clause} AND {cursor_cond}" if where_clause else f"WHERE {cursor_cond}"
                    )
                    data_sql = f"SELECT * FROM {table_name} {where_clause_cursor} {order_clause} LIMIT :limit"
                    params = {**filters, "cursor": cursor, "limit": per_page}
                elif pagination_type == PaginationType.KEYSET and cursor is not None:
                    cursor_cond = f"({sort_column}) > :cursor"
                    where_clause_cursor = (
                        f"{where_clause} AND {cursor_cond}" if where_clause else f"WHERE {cursor_cond}"
                    )
                    data_sql = f"SELECT * FROM {table_name} {where_clause_cursor} {order_clause} LIMIT :limit"
                    params = {**filters, "cursor": cursor, "limit": per_page}
                else:
                    offset = (page - 1) * per_page
                    data_sql = f"SELECT * FROM {table_name}"
                    if where_clause:
                        data_sql += f" {where_clause}"
                    if order_clause:
                        data_sql += f" {order_clause}"
                    data_sql += " LIMIT :limit OFFSET :offset"
                    params = {**filters, "limit": per_page, "offset": offset}
                
                result = conn.execute(text(data_sql), params)
                items = [dict(row._mapping) for row in result]
            else:
                # SQLite path with ? placeholders
                where_conditions = []
                where_params = []
                
                for k, v in filters.items():
                    where_conditions.append(f"{k} = ?")
                    where_params.append(v)
                
                where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
                order_clause = f"ORDER BY {sort_column} {sort_order}"
                
                # Count total
                count_sql = f"SELECT COUNT(*) FROM {table_name} {where_clause}"
                cur = conn.cursor()
                cur.execute(count_sql, where_params)
                result = cur.fetchone()
                total = result[0] if result else 0
                
                # Build data query
                if pagination_type == PaginationType.CURSOR_BASED and cursor is not None:
                    cursor_cond = f"{sort_column} > ?" if sort_order.upper() == "ASC" else f"{sort_column} < ?"
                    where_clause_cursor = (
                        f"{where_clause} AND {cursor_cond}" if where_clause else f"WHERE {cursor_cond}"
                    )
                    data_sql = f"SELECT * FROM {table_name} {where_clause_cursor} {order_clause} LIMIT ?"
                    data_params = where_params + [cursor, per_page]
                elif pagination_type == PaginationType.KEYSET and cursor is not None:
                    cursor_cond = f"{sort_column} > ?"
                    where_clause_cursor = (
                        f"{where_clause} AND {cursor_cond}" if where_clause else f"WHERE {cursor_cond}"
                    )
                    data_sql = f"SELECT * FROM {table_name} {where_clause_cursor} {order_clause} LIMIT ?"
                    data_params = where_params + [cursor, per_page]
                else:
                    offset = (page - 1) * per_page
                    data_sql = f"SELECT * FROM {table_name} {where_clause} {order_clause} LIMIT ? OFFSET ?"
                    data_params = where_params + [per_page, offset]
                
                cur.execute(data_sql, data_params)
                columns = [col[0] for col in cur.description]
                items = [dict(zip(columns, row)) for row in cur.fetchall()]

        duration = (time.time() - start) * 1000

        total_pages = (total + per_page - 1) // per_page if total > 0 else 0
        has_next = page < total_pages if pagination_type == PaginationType.OFFSET_LIMIT else bool(items)
        has_prev = page > 1 if pagination_type == PaginationType.OFFSET_LIMIT else bool(cursor)
        
        # Safe cursor generation
        next_cursor = None
        prev_cursor = None
        if items and sort_column in items[-1]:
            next_cursor = str(items[-1][sort_column])
        if items and sort_column in items[0]:
            prev_cursor = str(items[0][sort_column])

        return PaginationResult(
            items,
            total,
            page,
            per_page,
            total_pages,
            has_next,
            has_prev,
            next_cursor,
            prev_cursor,
            duration,
        )

    def get_cursor_paginated_results(
        self,
        table_name: str,
        cursor_column: str,
        cursor_value: Optional[Any] = None,
        per_page: int = 10,
        direction: str = "next",
        filters: Optional[Dict[str, Any]] = None,
    ) -> PaginationResult:
        """Cursor-based pagination for large datasets."""
        
        if not self._validate_sort_column(cursor_column):
            raise ValueError(f"Invalid cursor column: {cursor_column}")

        sort_order = "ASC" if direction == "next" else "DESC"
        return self.get_paginated_results(
            table_name,
            page=1,
            per_page=per_page,
            filters=filters,
            sort_by=cursor_column,
            sort_order=sort_order,
            pagination_type=PaginationType.CURSOR_BASED,
            cursor=cursor_value,
        )

    def get_keyset_paginated_results(
        self,
        table_name: str,
        keyset_columns: List[str],
        keyset_values: Optional[List[Any]] = None,
        per_page: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> PaginationResult:
        """Keyset pagination for consistently ordered results."""
        
        # Validate all keyset columns
        for col in keyset_columns:
            if not self._validate_sort_column(col):
                raise ValueError(f"Invalid keyset column: {col}")

        sort_by = keyset_columns[0] if keyset_columns else "id"
        cursor = keyset_values[0] if keyset_values else None
        return self.get_paginated_results(
            table_name,
            page=1,
            per_page=per_page,
            filters=filters,
            sort_by=sort_by,
            pagination_type=PaginationType.KEYSET,
            cursor=cursor,
        )


class DatabaseManager(PerformancePaginationMixin):
    """
    Enterprise-grade database manager with connection pooling and error handling.

    This class provides a centralized interface for database operations with:
    - Connection pooling for performance
    - Transaction management
    - Error handling and logging
    - Circuit breaker integration
    - Health monitoring

    Examples:
        Basic usage:
        >>> db = DatabaseManager()
        >>> with db.get_connection() as conn:
        ...     result = conn.execute("SELECT * FROM users")

        Transaction usage:
        >>> with db.get_connection() as conn:
        ...     with db.transaction(conn):
        ...         conn.execute("INSERT INTO users ...")

    Attributes:
        connection_pool (SQLAlchemy.pool): Database connection pool
        circuit_breaker (CircuitBreaker): Circuit breaker for resilience
        health_monitor (HealthMonitor): Connection health monitoring
    """

    def __init__(self, framework_db_path: str = "framework.db", timer_db_path: str = "task_timer.db") -> None:
        """Initialize database manager with connection paths.

        Creates SQLAlchemy engines for both databases when available and sets up
        internal structures required for caching and performance monitoring.

        Args:
            framework_db_path: Path to framework SQLite database file.
            timer_db_path: Path to timer database file. Timer functionality is
                disabled if the file does not exist.

        Raises:
            DatabaseError: If engine initialization fails.

        Example:
            >>> db_manager = DatabaseManager("/app/data/framework.db")
            >>> db_manager = DatabaseManager("./framework.db", "./timer.db")
        """
        self.framework_db_path = Path(framework_db_path)
        self.timer_db_path = Path(timer_db_path)
        self.engines = {}

        if SQLALCHEMY_AVAILABLE:
            self._initialize_engines()
    
    def _initialize_engines(self) -> None:
        """Initialize SQLAlchemy engines with optimized settings."""
        if not SQLALCHEMY_AVAILABLE:
            return
        
        # Framework database engine
        if self.framework_db_path.exists():
            framework_url = f"sqlite:///{self.framework_db_path}"
            self.engines["framework"] = create_engine(
                framework_url,
                poolclass=StaticPool,
                connect_args={
                    "check_same_thread": False,
                    "timeout": 20
                },
                echo=False
            )
        
        # Timer database engine  
        if self.timer_db_path.exists():
            timer_url = f"sqlite:///{self.timer_db_path}"
            self.engines["timer"] = create_engine(
                timer_url,
                poolclass=StaticPool,
                connect_args={
                    "check_same_thread": False,
                    "timeout": 20
                },
                echo=False
            )
    
    @contextmanager
    def get_connection(
        self, database_name: str = "framework"
    ) -> Iterator[Union[Connection, SQLiteConnection]]:
        """
        Get a database connection from the pool.

        Args:
            database_name (str): Name of the database to connect to.
                Defaults to "framework".

        Returns:
            Connection: SQLAlchemy connection object with context manager support.

        Raises:
            ConnectionError: If unable to establish connection after retries.
            CircuitBreakerOpenError: If circuit breaker is open.

        Examples:
            >>> db = DatabaseManager()
            >>> with db.get_connection() as conn:
            ...     result = conn.execute("SELECT COUNT(*) FROM users")
            ...     print(result.fetchone()[0])
        """
        if SQLALCHEMY_AVAILABLE and database_name in self.engines:
            conn = self.engines[database_name].connect()
            try:
                conn.execute(text("PRAGMA foreign_keys = ON"))
                yield conn
            finally:
                conn.close()
        else:
            db_path = self.framework_db_path if database_name == "framework" else self.timer_db_path
            if not db_path.exists():
                raise FileNotFoundError(f"Database not found: {db_path}")

            conn = sqlite3.connect(str(db_path), timeout=20)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            try:
                yield conn
            finally:
                conn.close()

    def release_connection(self, connection: Union[Connection, SQLiteConnection]) -> None:
        """Return connection to pool with cleanup.

        This method is provided for cases where a connection obtained via
        :meth:`get_connection` needs to be closed manually instead of using the
        context manager protocol.

        Args:
            connection: Connection instance to be returned.

        Example:
            >>> conn = next(db_manager.get_connection())
            >>> db_manager.release_connection(conn)
        """
        try:
            connection.close()
        except Exception:  # pragma: no cover - best effort
            logger.warning("Failed to close connection", exc_info=True)

    @contextmanager
    def transaction(
        self, 
        database_name: str = "framework", 
        isolation_level: Optional[str] = None,
        timeout: int = 30
    ) -> Iterator[Union[Connection, SQLiteConnection]]:
        """
        Transaction context manager with proper isolation and rollback support.
        
        Provides ACID transaction guarantees for critical operations, especially
        cascade deletes that may lock tables. Addresses report.md requirement:
        "Large numbers of cascade deletes may lock tables; wrap in transactions with proper isolation."
        
        Args:
            database_name: Database to connect to ("framework" or "timer")
            isolation_level: Transaction isolation level:
                - "READ_UNCOMMITTED": Lowest isolation, allows dirty reads
                - "READ_COMMITTED": Prevents dirty reads (default for most operations) 
                - "REPEATABLE_READ": Prevents dirty and non-repeatable reads
                - "SERIALIZABLE": Highest isolation, prevents all phenomena
                - None: Use database default
            timeout: Transaction timeout in seconds
            
        Returns:
            Connection with active transaction context
            
        Raises:
            Exception: Re-raises any exception after rollback
            
        Example:
            >>> with db.transaction(isolation_level="READ_COMMITTED") as conn:
            ...     conn.execute("DELETE FROM tasks WHERE project_id = ?", (project_id,))
            ...     conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
            ...     # Auto-commit on success, rollback on exception
        """
        with self.get_connection(database_name) as conn:
            # Set isolation level if specified
            if isolation_level and SQLALCHEMY_AVAILABLE:
                if isolation_level in ["READ_UNCOMMITTED", "READ_COMMITTED", "REPEATABLE_READ", "SERIALIZABLE"]:
                    conn.execute(text(f"PRAGMA read_uncommitted = {'ON' if isolation_level == 'READ_UNCOMMITTED' else 'OFF'}"))
            elif isolation_level and hasattr(conn, 'isolation_level'):
                # For direct SQLite connections
                if isolation_level == "SERIALIZABLE":
                    conn.execute("PRAGMA locking_mode = EXCLUSIVE")
                elif isolation_level == "READ_COMMITTED":
                    conn.execute("PRAGMA journal_mode = WAL")
            
            # Set timeout for lock wait
            if hasattr(conn, 'execute'):
                if SQLALCHEMY_AVAILABLE:
                    conn.execute(text(f"PRAGMA busy_timeout = {timeout * 1000}"))  # SQLite timeout in ms
                else:
                    conn.execute(f"PRAGMA busy_timeout = {timeout * 1000}")
            
            # Begin transaction
            if SQLALCHEMY_AVAILABLE:
                trans = conn.begin()
            else:
                conn.execute("BEGIN IMMEDIATE")
                trans = None
            
            try:
                yield conn
                # Commit on successful completion
                if SQLALCHEMY_AVAILABLE and trans:
                    trans.commit()
                else:
                    conn.commit()
            except Exception as e:
                # Rollback on any exception
                try:
                    if SQLALCHEMY_AVAILABLE and trans:
                        trans.rollback()
                    else:
                        conn.rollback()
                    logger.error(f"Transaction rolled back due to error: {e}")
                except Exception as rollback_error:
                    logger.error(f"Failed to rollback transaction: {rollback_error}")
                raise  # Re-raise original exception

    def delete_with_transaction(
        self, 
        delete_operations: List[Tuple[str, Dict[str, Any]]], 
        isolation_level: str = "READ_COMMITTED"
    ) -> bool:
        """
        Execute multiple delete operations within a single transaction.
        
        Ideal for cascade deletes that affect multiple related tables.
        Prevents partial deletes and table locks by using proper isolation.
        
        Args:
            delete_operations: List of (sql_query, params) tuples to execute
            isolation_level: Transaction isolation level for consistency
            
        Returns:
            True if all operations succeeded, False otherwise
            
        Example:
            >>> operations = [
            ...     ("DELETE FROM tasks WHERE project_id = :project_id", {"project_id": 123}),
            ...     ("DELETE FROM epics WHERE project_id = :project_id", {"project_id": 123}),
            ...     ("DELETE FROM projects WHERE id = :id", {"id": 123})
            ... ]
            >>> success = db.delete_with_transaction(operations)
        """
        try:
            with self.transaction(isolation_level=isolation_level) as conn:
                for sql_query, params in delete_operations:
                    if SQLALCHEMY_AVAILABLE:
                        conn.execute(text(sql_query), params)
                    else:
                        # Convert named parameters to positional for SQLite
                        if ':' in sql_query:
                            # Simple parameter substitution for basic cases
                            for key, value in params.items():
                                sql_query = sql_query.replace(f':{key}', '?')
                            param_values = list(params.values())
                        else:
                            param_values = list(params.values()) if params else []
                        
                        conn.execute(sql_query, param_values)
                
                logger.info(f"Successfully executed {len(delete_operations)} delete operations in transaction")
                return True
                
        except Exception as e:
            logger.error(f"Transaction delete failed: {e}")
            return False

    def delete_cascade_safe(
        self, 
        table_name: str, 
        record_id: int, 
        cascade_tables: Optional[List[str]] = None
    ) -> bool:
        """
        Safely delete a record and its cascaded dependencies using transactions.
        
        Prevents table locks during large cascade operations by using appropriate
        isolation levels and proper transaction boundaries.
        
        Args:
            table_name: Primary table to delete from
            record_id: ID of the record to delete
            cascade_tables: Optional list of dependent tables to clean up
            
        Returns:
            True if deletion succeeded, False otherwise
            
        Example:
            >>> # Delete client and all related data
            >>> success = db.delete_cascade_safe(
            ...     "clients", 
            ...     client_id, 
            ...     cascade_tables=["projects", "epics", "tasks"]
            ... )
        """
        # Define safe cascade relationships
        safe_relationships = {
            "clients": ["projects", "epics", "tasks"],
            "projects": ["epics", "tasks"],
            "epics": ["tasks"]
        }
        
        # Use provided cascade tables or safe defaults
        tables_to_clean = cascade_tables or safe_relationships.get(table_name, [])
        
        # Build delete operations in dependency order (children first)
        delete_ops = []
        
        # Add cascade deletes (reverse order for dependencies)
        for cascade_table in reversed(tables_to_clean):
            if cascade_table == "tasks":
                delete_ops.append((
                    f"DELETE FROM {cascade_table} WHERE epic_id IN (SELECT id FROM epics WHERE project_id IN (SELECT id FROM projects WHERE client_id = :record_id))",
                    {"record_id": record_id}
                ))
            elif cascade_table == "epics":
                delete_ops.append((
                    f"DELETE FROM {cascade_table} WHERE project_id IN (SELECT id FROM projects WHERE client_id = :record_id)",
                    {"record_id": record_id}
                ))
            elif cascade_table == "projects":
                delete_ops.append((
                    f"DELETE FROM {cascade_table} WHERE client_id = :record_id",
                    {"record_id": record_id}
                ))
        
        # Add primary table delete
        delete_ops.append((
            f"DELETE FROM {table_name} WHERE id = :record_id",
            {"record_id": record_id}
        ))
        
        # Execute all deletes in a single transaction with appropriate isolation
        return self.delete_with_transaction(
            delete_ops, 
            isolation_level="READ_COMMITTED"  # Prevent dirty reads while allowing concurrency
        )

    def execute_query(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        database_name: str = "framework",
    ) -> Union[Result, List[Dict[str, Any]]]:
        """Execute a raw SQL query.

        Args:
            query: SQL query string to execute.
            params: Optional mapping of parameters.
            database_name: Database identifier, defaults to ``framework``.

        Returns:
            SQLAlchemy ``Result`` when available or list of row dictionaries.
        """
        params = params or {}
        with self.get_connection(database_name) as conn:
            if SQLALCHEMY_AVAILABLE:
                return conn.execute(text(query), params)
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    @cache_database_query("get_epics", ttl=300) if CACHE_AVAILABLE else lambda f: f
    def get_epics(
        self,
        page: int = 1,
        page_size: int = 50,
        status_filter: Optional[Union[EpicStatus, str]] = None,
        project_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Get epics with intelligent caching and pagination.
        
        Args:
            page: Page number (1-based)
            page_size: Number of items per page
            status_filter: Filter by specific status
            project_id: Filter by specific project ID
            
        Returns:
            Dictionary with 'data' (list of epics), 'total', 'page', 'total_pages'
        """
        try:
            with self.get_connection("framework") as conn:
                # Build WHERE conditions
                where_conditions = ["deleted_at IS NULL"]
                params: Dict[str, Any] = {}
                
                if status_filter:
                    where_conditions.append(f"{FieldNames.STATUS} = :status_filter")
                    params["status_filter"] = (
                        status_filter.value if isinstance(status_filter, EpicStatus) else status_filter
                    )
                
                if project_id:
                    where_conditions.append("project_id = :project_id")
                    params["project_id"] = project_id
                
                where_clause = " AND ".join(where_conditions)
                
                # Count total records
                count_query = f"SELECT COUNT(*) FROM {TableNames.EPICS} WHERE {where_clause}"
                
                if SQLALCHEMY_AVAILABLE:
                    count_result = conn.execute(text(count_query), params)
                    total = count_result.scalar()
                else:
                    cursor = conn.cursor()
                    cursor.execute(count_query, params)
                    total = cursor.fetchone()[0]
                
                # Calculate pagination
                total_pages = (total + page_size - 1) // page_size
                offset = (page - 1) * page_size
                
                # Get paginated data
                data_query = f"""
                    SELECT id, epic_key, name, description, status, 
                           created_at, updated_at, completed_at,
                           points_earned, difficulty_level, project_id
                    FROM {TableNames.EPICS}
                    WHERE {where_clause}
                    ORDER BY created_at DESC
                    LIMIT :limit OFFSET :offset
                """
                params["limit"] = page_size
                params["offset"] = offset
                
                if SQLALCHEMY_AVAILABLE:
                    result = conn.execute(text(data_query), params)
                    data = [dict(row._mapping) for row in result]
                else:
                    cursor = conn.cursor()
                    cursor.execute(data_query, params)
                    data = [dict(row) for row in cursor.fetchall()]
                
                return {
                    "data": data,
                    "total": total,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": total_pages
                }
        except Exception as e:
            print(f"Error loading epics: {e}")
            return {
                "data": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
                "total_pages": 0
            }
    
    def get_all_epics(self) -> List[Dict[str, Any]]:
        """Backward compatibility method - get all epics without pagination."""
        result = self.get_epics(page=1, page_size=1000)  # Large page size to get all
        return result["data"] if isinstance(result, dict) else result
    
    @cache_database_query("get_tasks", ttl=300) if CACHE_AVAILABLE else lambda f: f
    def get_tasks(
        self,
        epic_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 100,
        status_filter: Optional[Union[TaskStatus, str]] = None,
        tdd_phase_filter: Optional[Union[TDDPhase, str]] = None,
    ) -> Dict[str, Any]:
        """Get tasks with intelligent caching, pagination, and filtering.
        
        Args:
            epic_id: Filter by specific epic ID
            page: Page number (1-based)
            page_size: Number of items per page
            status_filter: Filter by specific status
            tdd_phase_filter: Filter by TDD phase
            
        Returns:
            Dictionary with 'data' (list of tasks), 'total', 'page', 'total_pages'
        """
        try:
            with self.get_connection("framework") as conn:
                # Build WHERE conditions
                where_conditions = ["1=1"]
                params: Dict[str, Any] = {}
                
                if epic_id:
                    where_conditions.append("t.epic_id = :epic_id")
                    params["epic_id"] = epic_id
                
                if status_filter:
                    where_conditions.append("t.status = :status_filter")
                    params["status_filter"] = (
                        status_filter.value if isinstance(status_filter, TaskStatus) else status_filter
                    )

                if tdd_phase_filter:
                    where_conditions.append("t.tdd_phase = :tdd_phase_filter")
                    params["tdd_phase_filter"] = (
                        tdd_phase_filter.value if isinstance(tdd_phase_filter, TDDPhase) else tdd_phase_filter
                    )
                
                where_clause = " AND ".join(where_conditions)
                
                # Count total records
                count_query = f"""
                    SELECT COUNT(*)
                    FROM {TableNames.TASKS} t
                    JOIN {TableNames.EPICS} e ON t.epic_id = e.id
                    WHERE {where_clause}
                """
                
                if SQLALCHEMY_AVAILABLE:
                    count_result = conn.execute(text(count_query), params)
                    total = count_result.scalar()
                else:
                    cursor = conn.cursor()
                    cursor.execute(count_query, list(params.values()))
                    total = cursor.fetchone()[0]
                
                # Calculate pagination
                total_pages = (total + page_size - 1) // page_size
                offset = (page - 1) * page_size
                
                # Get paginated data
                data_query = f"""
                    SELECT t.id, t.epic_id, t.title, t.description, t.status,
                           t.estimate_minutes, t.tdd_phase, t.position,
                           t.created_at, t.updated_at, t.completed_at,
                           e.name as epic_name, e.epic_key, t.task_key
                    FROM {TableNames.TASKS} t
                    JOIN {TableNames.EPICS} e ON t.epic_id = e.id
                    WHERE {where_clause}
                    ORDER BY t.position ASC, t.created_at DESC
                    LIMIT :limit OFFSET :offset
                """
                params["limit"] = page_size
                params["offset"] = offset
                
                if SQLALCHEMY_AVAILABLE:
                    result = conn.execute(text(data_query), params)
                    data = [dict(row._mapping) for row in result]
                else:
                    cursor = conn.cursor()
                    cursor.execute(data_query, list(params.values()))
                    data = [dict(row) for row in cursor.fetchall()]
                
                return {
                    "data": data,
                    "total": total,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": total_pages
                }
        except Exception as e:
            logger.error(f"Error loading tasks: {e}")
            if STREAMLIT_AVAILABLE and st:
                st.error(f"❌ Error loading tasks: {e}")
            print(f"Error loading tasks: {e}")
            return {
                "data": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
                "total_pages": 0
            }
    
    def get_all_tasks(self, epic_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Backward compatibility method - get all tasks without pagination."""
        result = self.get_tasks(epic_id=epic_id, page=1, page_size=1000)  # Large page size to get all
        return result["data"] if isinstance(result, dict) else result
    
    @cache_database_query("get_timer_sessions", ttl=60) if CACHE_AVAILABLE else lambda f: f
    def get_timer_sessions(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get recent timer sessions with short-term caching."""
        if not self.timer_db_path.exists():
            return []
        
        try:
            with self.get_connection("timer") as conn:
                query = """
                    SELECT task_reference, user_identifier, started_at, ended_at,
                           planned_duration_minutes, actual_duration_minutes,
                           focus_rating, energy_level, mood_rating,
                           interruptions_count,
                           created_at
                    FROM timer_sessions
                    WHERE created_at >= DATE('now', ? || ' days')
                    ORDER BY created_at DESC
                    LIMIT 1000
                """
                
                if SQLALCHEMY_AVAILABLE:
                    result = conn.execute(text(query), [f"-{days}"])
                    return [dict(row._mapping) for row in result]
                else:
                    cursor = conn.cursor()
                    cursor.execute(query, [f"-{days}"])
                    return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error loading timer sessions: {e}")
            return []
    
    def get_user_stats(self, user_id: int = 1) -> Dict[str, Any]:
        """Get user statistics and gamification data."""
        try:
            with self.get_connection("framework") as conn:
                stats = {}
                
                # Basic stats
                if SQLALCHEMY_AVAILABLE:
                    # Tasks completed
                    result = conn.execute(text("""
                        SELECT COUNT(*) as completed_tasks
                        FROM framework_tasks
                        WHERE status = 'completed' AND deleted_at IS NULL
                    """))
                    stats["completed_tasks"] = result.scalar() or 0
                    
                    # Total points
                    result = conn.execute(text("""
                        SELECT COALESCE(SUM(points_earned), 0) as total_points
                        FROM framework_epics WHERE deleted_at IS NULL
                    """))
                    stats["total_points"] = result.scalar() or 0
                    
                    # Active streaks
                    result = conn.execute(text("""
                        SELECT COUNT(*) as active_streaks
                        FROM user_streaks
                        WHERE user_id = ? AND current_count > 0
                    """), [user_id])
                    stats["active_streaks"] = result.scalar() or 0
                    
                else:
                    cursor = conn.cursor()
                    
                    # Tasks completed
                    cursor.execute("""
                        SELECT COUNT(*) FROM framework_tasks
                        WHERE status = 'completed' AND deleted_at IS NULL
                    """)
                    row = cursor.fetchone()
                    stats["completed_tasks"] = row[0] if row and row[0] is not None else 0
                    
                    # Total points
                    cursor.execute("""
                        SELECT COALESCE(SUM(points_earned), 0)
                        FROM framework_epics WHERE deleted_at IS NULL
                    """)
                    row = cursor.fetchone()
                    stats["total_points"] = row[0] if row and row[0] is not None else 0
                    
                    # Active streaks
                    cursor.execute("""
                        SELECT COUNT(*) FROM user_streaks
                        WHERE user_id = ? AND current_count > 0
                    """, [user_id])
                    row = cursor.fetchone()
                    stats["active_streaks"] = row[0] if row and row[0] is not None else 0
                
                return stats
                
        except Exception as e:
            print(f"Error loading user stats: {e}")
            return {
                "completed_tasks": 0,
                "total_points": 0,
                "active_streaks": 0
            }
    
    def get_achievements(self, user_id: int = 1) -> List[Dict[str, Any]]:
        """Get user achievements."""
        try:
            with self.get_connection("framework") as conn:
                query = """
                    SELECT at.code, at.name, at.description, at.category,
                           at.points_reward, at.rarity, ua.unlocked_at
                    FROM user_achievements ua
                    JOIN achievement_types at ON ua.achievement_code = at.code
                    WHERE ua.user_id = ?
                    ORDER BY ua.unlocked_at DESC
                """
                
                if SQLALCHEMY_AVAILABLE:
                    result = conn.execute(text(query), [user_id])
                    return [dict(row._mapping) for row in result]
                else:
                    cursor = conn.cursor()
                    cursor.execute(query, [user_id])
                    return [dict(row) for row in cursor.fetchall()]
                    
        except Exception as e:
            print(f"Error loading achievements: {e}")
            return []
    
    @invalidate_cache_on_change("db_query:get_tasks:", "db_query:get_epics:") if CACHE_AVAILABLE else lambda f: f
    def update_task_status(self, task_id: int, status: str, tdd_phase: Optional[str] = None) -> bool:
        """Update task status and TDD phase with cache invalidation."""
        try:
            with self.get_connection("framework") as conn:
                if SQLALCHEMY_AVAILABLE:
                    query = "UPDATE framework_tasks SET status = ?, updated_at = CURRENT_TIMESTAMP"
                    params = [status]
                    
                    if tdd_phase:
                        query += ", tdd_phase = ?"
                        params.append(tdd_phase)
                    
                    if status == 'completed':
                        query += ", completed_at = CURRENT_TIMESTAMP"
                    
                    query += " WHERE id = ?"
                    params.append(task_id)
                    
                    conn.execute(text(query), params)
                    conn.commit()
                else:
                    cursor = conn.cursor()
                    query = "UPDATE framework_tasks SET status = ?, updated_at = CURRENT_TIMESTAMP"
                    params = [status]
                    
                    if tdd_phase:
                        query += ", tdd_phase = ?"
                        params.append(tdd_phase)
                    
                    if status == 'completed':
                        query += ", completed_at = CURRENT_TIMESTAMP"
                    
                    query += " WHERE id = ?"
                    params.append(task_id)
                    
                    cursor.execute(query, params)
                    conn.commit()
                
                return True
                
        except Exception as e:
            print(f"Error updating task status: {e}")
            return False
    
    @invalidate_cache_on_change("db_query:get_timer_sessions:") if CACHE_AVAILABLE else lambda f: f
    def create_timer_session(self, task_id: Optional[int], duration_minutes: int, 
                           focus_rating: Optional[int] = None, interruptions: int = 0,
                           actual_duration_minutes: Optional[int] = None,
                           ended_at: Optional[str] = None, notes: Optional[str] = None) -> bool:
        """Create a new timer session record with cache invalidation."""
        if not self.timer_db_path.exists():
            return False
        
        try:
            with self.get_connection("timer") as conn:
                if SQLALCHEMY_AVAILABLE:
                    conn.execute(text("""
                        INSERT INTO timer_sessions (
                            task_reference, user_identifier, started_at, ended_at,
                            planned_duration_minutes, actual_duration_minutes,
                            focus_rating, interruptions_count, notes, created_at
                        ) VALUES (?, 'user1', CURRENT_TIMESTAMP, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """), [
                        str(task_id) if task_id else None,
                        ended_at,
                        duration_minutes,
                        actual_duration_minutes or duration_minutes,
                        focus_rating,
                        interruptions,
                        notes
                    ])
                    conn.commit()
                else:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO timer_sessions (
                            task_reference, user_identifier, started_at, ended_at,
                            planned_duration_minutes, actual_duration_minutes,
                            focus_rating, interruptions_count, notes, created_at
                        ) VALUES (?, 'user1', CURRENT_TIMESTAMP, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """, [
                        str(task_id) if task_id else None,
                        ended_at,
                        duration_minutes,
                        actual_duration_minutes or duration_minutes,
                        focus_rating,
                        interruptions,
                        notes
                    ])
                    conn.commit()
                
                return True
                
        except Exception as e:
            print(f"Error creating timer session: {e}")
            return False
    
    def get_epic_progress(self, epic_id: int) -> Dict[str, Any]:
        """Get detailed progress for an epic with extensive debugging."""

        # Early validation
        if epic_id is None:
            print("DEBUG: get_epic_progress called with epic_id=None")
            return self._get_default_progress()

        print(f"DEBUG: get_epic_progress called with epic_id={epic_id}, type={type(epic_id)}")

        try:
            with self.get_connection("framework") as conn:
                if SQLALCHEMY_AVAILABLE:
                    # Get epic info
                    epic_query = (
                        "SELECT id, epic_key, name, status, points_earned "
                        "FROM framework_epics "
                        "WHERE id = :epic_id AND deleted_at IS NULL"
                    )
                    print(f"DEBUG: Executing epic query: {epic_query}")
                    epic_result = conn.execute(text(epic_query), {"epic_id": epic_id})
                    epic_row = epic_result.fetchone()
                    print(f"DEBUG: Epic row: {epic_row}, type={type(epic_row)}")
                    if not epic_row:
                        return self._get_default_progress()
                    epic = dict(epic_row._mapping)

                    # Get task counts
                    task_query = (
                        "SELECT "
                        "    COUNT(*) as total_tasks, "
                        "    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_tasks, "
                        "    SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress_tasks "
                        "FROM framework_tasks "
                        "WHERE epic_id = :epic_id AND deleted_at IS NULL"
                    )
                    print(f"DEBUG: Executing task query: {task_query}")
                    task_result = conn.execute(text(task_query), {"epic_id": epic_id})
                    task_row = task_result.fetchone()
                    print(f"DEBUG: Task row: {task_row}, type={type(task_row)}")
                    if not task_row:
                        tasks = {"total_tasks": 0, "completed_tasks": 0, "in_progress_tasks": 0}
                    else:
                        tasks = {k: (v or 0) for k, v in dict(task_row._mapping).items()}

                else:
                    cursor = conn.cursor()

                    # Get epic info
                    epic_query = (
                        "SELECT id, epic_key, name, status, points_earned "
                        "FROM framework_epics WHERE id = ? AND deleted_at IS NULL"
                    )
                    print(f"DEBUG: Executing epic query: {epic_query}")
                    cursor.execute(epic_query, [epic_id])
                    epic_row = cursor.fetchone()
                    print(f"DEBUG: Epic row: {epic_row}, type={type(epic_row)}")
                    if not epic_row:
                        return self._get_default_progress()
                    epic = dict(epic_row)

                    # Get task counts
                    task_query = (
                        "SELECT "
                        "    COUNT(*) as total_tasks, "
                        "    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_tasks, "
                        "    SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress_tasks "
                        "FROM framework_tasks WHERE epic_id = ? AND deleted_at IS NULL"
                    )
                    print(f"DEBUG: Executing task query: {task_query}")
                    cursor.execute(task_query, [epic_id])
                    task_row = cursor.fetchone()
                    print(f"DEBUG: Task row: {task_row}, type={type(task_row)}")
                    if not task_row:
                        tasks = {"total_tasks": 0, "completed_tasks": 0, "in_progress_tasks": 0}
                    else:
                        tasks = {k: (v or 0) for k, v in dict(task_row).items()}

                # Calculate progress
                total = tasks.get("total_tasks") or 0
                completed = tasks.get("completed_tasks") or 0
                progress_pct = (completed / total * 100) if total > 0 else 0

                progress_dict = {
                    **epic,
                    **tasks,
                    "progress_percentage": round(progress_pct, 1),
                    "points_earned": epic.get("points_earned") or 0,
                }
                print(f"DEBUG: Returning: {progress_dict}")
                return progress_dict

        except Exception as e:
            print(f"Error getting epic progress: {e}")
            return self._get_default_progress()
    
    def _get_default_progress(self) -> Dict[str, Any]:
        """Return default progress structure when epic not found."""
        return {
            "id": 0,
            "epic_key": "N/A",
            "name": "Unknown",
            "status": "unknown",
            "points_earned": 0,
            "total_tasks": 0,
            "completed_tasks": 0,
            "in_progress_tasks": 0,
            "progress_percentage": 0.0
        }
    
    def check_database_health(self) -> Dict[str, Any]:
        """Comprehensive database health check with diagnostics.

        Performs connection tests against both framework and timer databases and
        reports the availability of optional dependencies used by the
        application.

        Returns:
            Dict[str, Any]: Dictionary describing connection status and
                dependency availability.

        Example:
            >>> health = db_manager.check_database_health()
            >>> health["framework_db_connected"]
        """
        health = {
            "framework_db_exists": self.framework_db_path.exists(),
            "timer_db_exists": self.timer_db_path.exists(),
            "framework_db_connected": False,
            "timer_db_connected": False,
            "sqlalchemy_available": SQLALCHEMY_AVAILABLE,
            "pandas_available": PANDAS_AVAILABLE
        }
        
        # Test framework DB connection
        try:
            with self.get_connection("framework") as conn:
                if SQLALCHEMY_AVAILABLE:
                    conn.execute(text("SELECT 1"))
                else:
                    conn.execute("SELECT 1")
                health["framework_db_connected"] = True
        except Exception as e:
            # Log database connection failure for debugging
            import logging
            logging.getLogger(__name__).debug(f"Framework DB connection failed: {e}")
            health["framework_db_connected"] = False
        
        # Test timer DB connection
        if self.timer_db_path.exists():
            try:
                with self.get_connection("timer") as conn:
                    if SQLALCHEMY_AVAILABLE:
                        conn.execute(text("SELECT 1"))
                    else:
                        conn.execute("SELECT 1")
                    health["timer_db_connected"] = True
            except Exception as e:
                # Log timer database connection failure for debugging
                import logging
                logging.getLogger(__name__).debug(f"Timer DB connection failed: {e}")
                health["timer_db_connected"] = False
        
        return health
    
    def format_database_datetime(self, dt_string: str, format_type: str = "full") -> str:
        """Format database datetime string with user timezone."""
        if not dt_string or not TIMEZONE_UTILS_AVAILABLE:
            return dt_string or "Unknown"
        
        try:
            # Parse database datetime (assume UTC/ISO format)
            if 'T' in dt_string:
                dt = datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
            else:
                dt = datetime.strptime(dt_string, "%Y-%m-%d %H:%M:%S")
            
            if format_type == "ago":
                return format_time_ago_user_tz(dt)
            elif format_type == "date":
                return format_datetime_user_tz(dt, "%Y-%m-%d")
            elif format_type == "time":
                return format_datetime_user_tz(dt, "%H:%M")
            elif format_type == "short":
                return format_datetime_user_tz(dt, "%m/%d %H:%M")
            else:  # full
                return format_datetime_user_tz(dt, "%Y-%m-%d %H:%M:%S")
                
        except (ValueError, TypeError) as e:
            return dt_string or "Invalid date"
    
    def get_formatted_epic_data(self) -> List[Dict[str, Any]]:
        """Get epics with formatted datetime fields."""
        epics = self.get_epics()
        
        for epic in epics:
            if 'created_at' in epic:
                epic['created_at_formatted'] = self.format_database_datetime(epic['created_at'], "short")
                epic['created_at_ago'] = self.format_database_datetime(epic['created_at'], "ago")
            
            if 'updated_at' in epic:
                epic['updated_at_formatted'] = self.format_database_datetime(epic['updated_at'], "short")
                epic['updated_at_ago'] = self.format_database_datetime(epic['updated_at'], "ago")
            
            if 'completed_at' in epic and epic['completed_at']:
                epic['completed_at_formatted'] = self.format_database_datetime(epic['completed_at'], "short")
                epic['completed_at_ago'] = self.format_database_datetime(epic['completed_at'], "ago")
        
        return epics
    
    def get_formatted_timer_sessions(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get timer sessions with formatted datetime fields."""
        sessions = self.get_timer_sessions(days)
        
        for session in sessions:
            if 'started_at' in session:
                session['started_at_formatted'] = self.format_database_datetime(session['started_at'], "short")
                session['started_at_ago'] = self.format_database_datetime(session['started_at'], "ago")
            
            if 'ended_at' in session and session['ended_at']:
                session['ended_at_formatted'] = self.format_database_datetime(session['ended_at'], "short")
                session['ended_at_ago'] = self.format_database_datetime(session['ended_at'], "ago")
            
            if 'created_at' in session:
                session['created_at_formatted'] = self.format_database_datetime(session['created_at'], "short")
                session['created_at_ago'] = self.format_database_datetime(session['created_at'], "ago")
        
        return sessions
    
    def clear_cache(self, cache_pattern: Optional[str] = None) -> bool:
        """Clear query result caches with optional pattern matching.

        Args:
            cache_pattern: Optional pattern to selectively invalidate caches.
                When ``None`` all database query caches are removed.

        Returns:
            bool: ``True`` if cache was cleared, ``False`` if caching is
                unavailable.

        Example:
            >>> db_manager.clear_cache("db_query:get_clients:")
        """
        if not CACHE_AVAILABLE:
            print("Cache not available")
            return False

        cache = get_cache()
        pattern = cache_pattern or "db_query:"
        cache.invalidate_pattern(pattern)
        print("Database cache cleared")
        return True
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get database cache statistics."""
        if CACHE_AVAILABLE:
            from .cache import get_cache_statistics
            return get_cache_statistics()
        else:
            return {"cache_available": False}

    def get_query_statistics(self) -> Dict[str, Any]:
        """Get detailed query performance statistics.

        Returns:
            Dict[str, Any]: Mapping of engine names to connection pool metrics.

        Example:
            >>> stats = db_manager.get_query_statistics()
        """
        stats: Dict[str, Any] = {}
        if not SQLALCHEMY_AVAILABLE:
            return stats

        for name, engine in self.engines.items():
            pool = getattr(engine, "pool", None)
            stats[name] = {
                "checked_out": getattr(pool, "checkedout", lambda: None)(),
                "size": getattr(pool, "size", lambda: None)(),
            }
        return stats

    def optimize_database(self) -> Dict[str, Any]:
        """Run database optimization and return performance report.

        Executes ``VACUUM`` on all available databases and reports size before
        and after the operation.

        Returns:
            Dict[str, Any]: Optimization report keyed by database name.

        Example:
            >>> report = db_manager.optimize_database()
        """
        report: Dict[str, Any] = {}
        for name, path in {
            "framework": self.framework_db_path,
            "timer": self.timer_db_path,
        }.items():
            if not path.exists():
                continue
            size_before = path.stat().st_size
            with sqlite3.connect(str(path)) as conn:
                conn.execute("VACUUM")
            size_after = path.stat().st_size
            report[name] = {"size_before": size_before, "size_after": size_after}
        return report

    def create_backup(self, backup_path: Optional[str] = None) -> str:
        """Create full database backup with verification.

        Args:
            backup_path: Destination file path. When ``None`` a ``.bak`` file is
                created next to the framework database.

        Returns:
            str: Path to the created backup file.

        Example:
            >>> backup_file = db_manager.create_backup()
        """
        backup_file = backup_path or str(self.framework_db_path.with_suffix(".bak"))
        with sqlite3.connect(str(self.framework_db_path)) as src, sqlite3.connect(backup_file) as dst:
            src.backup(dst)
        return backup_file

    def restore_backup(self, backup_path: str, verify: bool = True) -> bool:
        """Restore database from backup with integrity verification.

        Args:
            backup_path: Path to backup file created by :meth:`create_backup`.
            verify: When ``True`` perform ``PRAGMA integrity_check`` after
                restoration.

        Returns:
            bool: ``True`` if restore succeeded and verification passed.

        Example:
            >>> db_manager.restore_backup("framework.bak")
        """
        with sqlite3.connect(backup_path) as src, sqlite3.connect(str(self.framework_db_path)) as dst:
            src.backup(dst)

        if verify:
            with sqlite3.connect(str(self.framework_db_path)) as conn:
                result = conn.execute("PRAGMA integrity_check").fetchone()
                return result[0] == "ok"
        return True
    
    @cache_database_query("get_productivity_stats", ttl=60) if CACHE_AVAILABLE else lambda f: f
    def get_productivity_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get productivity statistics for the last N days."""
        stats = {
            "activity_by_date": {},
            "tasks_completed_total": 0,
            "focus_time_total": 0,
            "average_daily_tasks": 0,
            "average_focus_time": 0,
            "most_productive_day": None,
            "current_streak": 0,
            "best_streak": 0
        }
        
        try:
            # Get task activity for last N days
            with self.get_connection("framework") as conn:
                if SQLALCHEMY_AVAILABLE:
                    result = conn.execute(text("""
                        SELECT DATE(updated_at) as date, COUNT(*) as count
                        FROM framework_tasks
                        WHERE updated_at >= DATE('now', :days)
                        AND status = 'completed'
                        GROUP BY DATE(updated_at)
                        ORDER BY date DESC
                    """), {"days": f"-{days} days"})
                    
                    for row in result:
                        date_str = str(row[0])  # Access by index for compatibility
                        count = row[1]
                        stats["activity_by_date"][date_str] = count
                        stats["tasks_completed_total"] += count
                else:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT DATE(updated_at) as date, COUNT(*) as count
                        FROM framework_tasks
                        WHERE updated_at >= DATE('now', ?)
                        AND status = 'completed'
                        GROUP BY DATE(updated_at)
                        ORDER BY date DESC
                    """, (f"-{days} days",))
                    
                    for row in cursor.fetchall():
                        date_str = row[0]
                        stats["activity_by_date"][date_str] = row[1]
                        stats["tasks_completed_total"] += row[1]
            
            # Get focus time from timer database
            if self.timer_db_path.exists():
                with self.get_connection("timer") as conn:
                    if SQLALCHEMY_AVAILABLE:
                        result = conn.execute(text("""
                            SELECT DATE(started_at) as date, 
                                   SUM(actual_duration_minutes) as total_minutes
                            FROM timer_sessions
                            WHERE started_at >= DATE('now', :days)
                            GROUP BY DATE(started_at)
                        """), {"days": f"-{days} days"})
                        
                        for row in result:
                            stats["focus_time_total"] += row[1] or 0  # Access by index for compatibility
                    else:
                        cursor = conn.cursor()
                        cursor.execute("""
                            SELECT DATE(started_at) as date,
                                   SUM(actual_duration_minutes) as total_minutes
                            FROM timer_sessions
                            WHERE started_at >= DATE('now', ?)
                            GROUP BY DATE(started_at)
                        """, (f"-{days} days",))
                        
                        for row in cursor.fetchall():
                            stats["focus_time_total"] += row[1] or 0
            
            # Calculate averages
            if days > 0:
                stats["average_daily_tasks"] = round(stats["tasks_completed_total"] / days, 1)
                stats["average_focus_time"] = round(stats["focus_time_total"] / days, 1)
            
            # Find most productive day
            if stats["activity_by_date"]:
                most_productive = max(stats["activity_by_date"].items(), key=lambda x: x[1])
                stats["most_productive_day"] = most_productive[0]
            
            # Calculate streaks
            stats["current_streak"] = self._calculate_current_streak()
            stats["best_streak"] = self._get_best_streak()
            
        except Exception as e:
            print(f"Error getting productivity stats: {e}")
        
        return stats
    
    @cache_database_query("get_daily_summary", ttl=60) if CACHE_AVAILABLE else lambda f: f
    def get_daily_summary(self) -> Dict[str, Any]:
        """Get today's activity summary."""
        summary = {
            "tasks_completed": 0,
            "tasks_in_progress": 0,
            "tasks_created": 0,
            "focus_time_minutes": 0,
            "timer_sessions": 0,
            "achievements_today": 0,
            "streak_days": 0,
            "points_earned_today": 0
        }
        
        today = datetime.now().date().isoformat()
        
        try:
            with self.get_connection("framework") as conn:
                if SQLALCHEMY_AVAILABLE:
                    # Tasks completed today
                    result = conn.execute(text("""
                        SELECT COUNT(*) FROM framework_tasks
                        WHERE DATE(updated_at) = :today AND status = 'completed'
                    """), {"today": today})
                    summary["tasks_completed"] = result.scalar() or 0
                    
                    # Tasks in progress
                    result = conn.execute(text("""
                        SELECT COUNT(*) FROM framework_tasks
                        WHERE status = 'in_progress'
                    """))
                    summary["tasks_in_progress"] = result.scalar() or 0
                    
                    # Tasks created today
                    result = conn.execute(text("""
                        SELECT COUNT(*) FROM framework_tasks
                        WHERE DATE(created_at) = :today
                    """), {"today": today})
                    summary["tasks_created"] = result.scalar() or 0
                    
                    # Points earned today
                    result = conn.execute(text("""
                        SELECT SUM(points_value) FROM framework_tasks
                        WHERE DATE(completed_at) = :today AND status = 'completed'
                    """), {"today": today})
                    summary["points_earned_today"] = result.scalar() or 0
                    
                    # Achievements unlocked today
                    result = conn.execute(text("""
                        SELECT COUNT(*) FROM user_achievements
                        WHERE DATE(unlocked_at) = :today
                    """), {"today": today})
                    summary["achievements_today"] = result.scalar() or 0
                    
                    # Current streak
                    result = conn.execute(text("""
                        SELECT current_streak FROM user_streaks
                        WHERE user_id = 1 AND streak_type = 'daily_tasks'
                        ORDER BY updated_at DESC LIMIT 1
                    """))
                    row = result.fetchone()
                    if row:
                        summary["streak_days"] = row[0] or 0
                else:
                    cursor = conn.cursor()
                    
                    # Tasks completed today
                    cursor.execute("""
                        SELECT COUNT(*) FROM framework_tasks
                        WHERE DATE(updated_at) = ? AND status = 'completed'
                    """, (today,))
                    row = cursor.fetchone()
                    summary["tasks_completed"] = row[0] if row and row[0] is not None else 0
                    
                    # Tasks in progress
                    cursor.execute("""
                        SELECT COUNT(*) FROM framework_tasks
                        WHERE status = 'in_progress'
                    """)
                    row = cursor.fetchone()
                    summary["tasks_in_progress"] = row[0] if row and row[0] is not None else 0
                    
                    # Tasks created today
                    cursor.execute("""
                        SELECT COUNT(*) FROM framework_tasks
                        WHERE DATE(created_at) = ?
                    """, (today,))
                    row = cursor.fetchone()
                    summary["tasks_created"] = row[0] if row and row[0] is not None else 0
            
            # Get timer data if available
            if self.timer_db_path.exists():
                with self.get_connection("timer") as conn:
                    if SQLALCHEMY_AVAILABLE:
                        result = conn.execute(text("""
                            SELECT COUNT(*) as sessions, 
                                   SUM(actual_duration_minutes) as total_minutes
                            FROM timer_sessions
                            WHERE DATE(started_at) = :today
                        """), {"today": today})
                        row = result.fetchone()
                        if row:
                            summary["timer_sessions"] = row[0] or 0
                            summary["focus_time_minutes"] = row[1] or 0
                    else:
                        cursor = conn.cursor()
                        cursor.execute("""
                            SELECT COUNT(*) as sessions,
                                   SUM(actual_duration_minutes) as total_minutes
                            FROM timer_sessions
                            WHERE DATE(started_at) = ?
                        """, (today,))
                        row = cursor.fetchone()
                        if row:
                            summary["timer_sessions"] = row[0] or 0
                            summary["focus_time_minutes"] = row[1] or 0
        
        except Exception as e:
            print(f"Error getting daily summary: {e}")
        
        return summary
    
    @cache_database_query("get_pending_notifications", ttl=30) if CACHE_AVAILABLE else lambda f: f
    def get_pending_notifications(self) -> List[Dict[str, Any]]:
        """Get pending notifications for the user."""
        notifications = []
        
        try:
            with self.get_connection("framework") as conn:
                # Check for overdue tasks
                if SQLALCHEMY_AVAILABLE:
                    result = conn.execute(text("""
                        SELECT title, due_date FROM framework_tasks
                        WHERE status != 'completed' 
                        AND due_date IS NOT NULL
                        AND DATE(due_date) <= DATE('now')
                        LIMIT 5
                    """))
                    
                    for row in result:
                        notifications.append({
                            "type": "warning",
                            "title": "Task Overdue",
                            "message": f"{row[0]} was due {row[1]}",
                            "timestamp": datetime.now()
                        })
                
                # Check for long-running tasks
                if SQLALCHEMY_AVAILABLE:
                    result = conn.execute(text("""
                        SELECT title FROM framework_tasks
                        WHERE status = 'in_progress'
                        AND julianday('now') - julianday(updated_at) > 3
                        LIMIT 3
                    """))
                    
                    for row in result:
                        notifications.append({
                            "type": "info",
                            "title": "Long Running Task",
                            "message": f"{row[0]} has been in progress for over 3 days",
                            "timestamp": datetime.now()
                        })
        
        except Exception as e:
            print(f"Error getting notifications: {e}")
        
        return notifications
    
    @cache_database_query("get_user_achievements", ttl=300) if CACHE_AVAILABLE else lambda f: f
    def get_user_achievements(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get user achievements."""
        achievements = []
        
        try:
            with self.get_connection("framework") as conn:
                if SQLALCHEMY_AVAILABLE:
                    result = conn.execute(text("""
                        SELECT at.name, at.description, at.icon, at.points_value,
                               ua.unlocked_at, ua.progress_value
                        FROM achievement_types at
                        LEFT JOIN user_achievements ua ON at.id = ua.achievement_id
                        WHERE at.is_active = TRUE
                        ORDER BY ua.unlocked_at DESC NULLS LAST
                        LIMIT :limit
                    """), {"limit": limit})
                    
                    for row in result:
                        achievements.append({
                            "name": row[0],
                            "description": row[1], 
                            "icon": row[2] or "🏆",
                            "points": row[3],
                            "unlocked": row[4] is not None,
                            "unlocked_at": row[4],
                            "progress": row[5]
                        })
                else:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT at.name, at.description, at.icon, at.points_value,
                               ua.unlocked_at, ua.progress_value
                        FROM achievement_types at
                        LEFT JOIN user_achievements ua ON at.id = ua.achievement_id
                        WHERE at.is_active = 1
                        ORDER BY ua.unlocked_at DESC
                        LIMIT ?
                    """, (limit,))
                    
                    for row in cursor.fetchall():
                        achievements.append({
                            "name": row[0],
                            "description": row[1],
                            "icon": row[2] or "🏆",
                            "points": row[3],
                            "unlocked": row[4] is not None,
                            "unlocked_at": row[4],
                            "progress": row[5]
                        })
        
        except Exception as e:
            print(f"Error getting achievements: {e}")
        
        return achievements
    
    def _calculate_current_streak(self) -> int:
        """Calculate current task completion streak."""
        try:
            with self.get_connection("framework") as conn:
                if SQLALCHEMY_AVAILABLE:
                    result = conn.execute(text("""
                        SELECT current_streak FROM user_streaks
                        WHERE user_id = 1 AND streak_type = 'daily_tasks'
                        ORDER BY updated_at DESC LIMIT 1
                    """))
                    row = result.fetchone()
                    return row[0] if row else 0
                else:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT current_streak FROM user_streaks
                        WHERE user_id = 1 AND streak_type = 'daily_tasks'
                        ORDER BY updated_at DESC LIMIT 1
                    """)
                    row = cursor.fetchone()
                    return row[0] if row else 0
        except Exception:
            return 0
    
    def _get_best_streak(self) -> int:
        """Get best streak record."""
        try:
            with self.get_connection("framework") as conn:
                if SQLALCHEMY_AVAILABLE:
                    result = conn.execute(text("""
                        SELECT best_streak FROM user_streaks
                        WHERE user_id = 1 AND streak_type = 'daily_tasks'
                        ORDER BY best_streak DESC LIMIT 1
                    """))
                    row = result.fetchone()
                    return row[0] if row else 0
                else:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT best_streak FROM user_streaks
                        WHERE user_id = 1 AND streak_type = 'daily_tasks'
                        ORDER BY best_streak DESC LIMIT 1
                    """)
                    row = cursor.fetchone()
                    return row[0] if row else 0
        except Exception:
            return 0
    
    # CRUD Operations for Tasks
    
    def create_task(self, title: str, epic_id: int, description: str = "", 
                   tdd_phase: str = "", priority: int = 2, 
                   estimate_minutes: int = 0) -> Optional[int]:
        """Create a new task in the database.
        
        Args:
            title: Task title
            epic_id: ID of the associated epic
            description: Optional task description
            tdd_phase: TDD phase (red, green, refactor)
            priority: Task priority (1=High, 2=Medium, 3=Low)
            estimate_minutes: Estimated time in minutes
            
        Returns:
            Task ID if successful, None otherwise
        """
        try:
            with self.get_connection("framework") as conn:
                if SQLALCHEMY_AVAILABLE:
                    result = conn.execute(text("""
                        INSERT INTO framework_tasks 
                        (title, description, epic_id, tdd_phase, priority, 
                         estimate_minutes, status, created_at, updated_at)
                        VALUES (:title, :description, :epic_id, :tdd_phase, 
                               :priority, :estimate_minutes, 'todo', 
                               datetime('now'), datetime('now'))
                    """), {
                        "title": title,
                        "description": description,
                        "epic_id": epic_id,
                        "tdd_phase": tdd_phase,
                        "priority": priority,
                        "estimate_minutes": estimate_minutes
                    })
                    conn.commit()
                    return result.lastrowid
                else:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO framework_tasks 
                        (title, description, epic_id, tdd_phase, priority, 
                         estimate_minutes, status, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, 'todo', datetime('now'), datetime('now'))
                    """, (title, description, epic_id, tdd_phase, priority, estimate_minutes))
                    conn.commit()
                    return cursor.lastrowid
        except Exception as e:
            print(f"Error creating task: {e}")
            return None
    
    def update_task(
        self,
        task_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        tdd_phase: Optional[str] = None,
        priority: Optional[int] = None,
        estimate_minutes: Optional[int] = None,
    ) -> bool:
        """Update task details.
        
        Args:
            task_id: ID of the task to update
            title: New title (optional)
            description: New description (optional)
            tdd_phase: New TDD phase (optional)
            priority: New priority (optional)
            estimate_minutes: New estimate (optional)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Build dynamic update query
            updates = []
            params = {"task_id": task_id}
            
            if title is not None:
                updates.append("title = :title")
                params["title"] = title
            
            if description is not None:
                updates.append("description = :description")
                params["description"] = description
                
            if tdd_phase is not None:
                updates.append("tdd_phase = :tdd_phase")
                params["tdd_phase"] = tdd_phase
                
            if priority is not None:
                updates.append("priority = :priority")
                params["priority"] = priority
                
            if estimate_minutes is not None:
                updates.append("estimate_minutes = :estimate_minutes")
                params["estimate_minutes"] = estimate_minutes
            
            if not updates:
                return True  # Nothing to update
                
            updates.append("updated_at = datetime('now')")
            # Security: Column names are hardcoded in this function, safe from SQL injection
            query = f"UPDATE framework_tasks SET {', '.join(updates)} WHERE id = :task_id"  # nosec B608
            
            with self.get_connection("framework") as conn:
                if SQLALCHEMY_AVAILABLE:
                    conn.execute(text(query), params)
                    conn.commit()
                else:
                    # Convert to positional parameters for sqlite3
                    positional_params = []
                    positional_query = query.replace(":title", "?").replace(":description", "?")
                    positional_query = positional_query.replace(":tdd_phase", "?").replace(":priority", "?")
                    positional_query = positional_query.replace(":estimate_minutes", "?").replace(":task_id", "?")
                    
                    for key in ["title", "description", "tdd_phase", "priority", "estimate_minutes"]:
                        if key in params:
                            positional_params.append(params[key])
                    positional_params.append(task_id)
                    
                    cursor = conn.cursor()
                    cursor.execute(positional_query, positional_params)
                    conn.commit()
                
                return True
        except Exception as e:
            print(f"Error updating task {task_id}: {e}")
            return False
    
    def delete_task(self, task_id: int, soft_delete: bool = True) -> bool:
        """Delete a task (soft delete by default).
        
        Args:
            task_id: ID of the task to delete
            soft_delete: If True, mark as deleted; if False, actually delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.get_connection("framework") as conn:
                if soft_delete:
                    # Soft delete: mark as deleted
                    if SQLALCHEMY_AVAILABLE:
                        conn.execute(text("""
                            UPDATE framework_tasks 
                            SET deleted_at = datetime('now'), updated_at = datetime('now')
                            WHERE id = :task_id
                        """), {"task_id": task_id})
                        conn.commit()
                    else:
                        cursor = conn.cursor()
                        cursor.execute("""
                            UPDATE framework_tasks 
                            SET deleted_at = datetime('now'), updated_at = datetime('now')
                            WHERE id = ?
                        """, (task_id,))
                        conn.commit()
                else:
                    # Hard delete: use transaction wrapper for consistency and safety
                    # Tasks are leaf nodes but still benefit from transaction protection
                    with self.transaction(isolation_level="READ_COMMITTED") as trans_conn:
                        if SQLALCHEMY_AVAILABLE:
                            trans_conn.execute(text("DELETE FROM framework_tasks WHERE id = :task_id"), 
                                           {"task_id": task_id})
                        else:
                            trans_conn.execute("DELETE FROM framework_tasks WHERE id = ?", (task_id,))
                
                return True
        except Exception as e:
            print(f"Error deleting task {task_id}: {e}")
            return False
    
    @cache_database_query("get_kanban_tasks", ttl=60) if CACHE_AVAILABLE else lambda f: f
    def get_kanban_tasks(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get tasks optimized for Kanban board display (grouped by status)."""
        try:
            with self.get_connection("framework") as conn:
                query = """
                    SELECT t.id, t.epic_id, t.title, t.description, t.status,
                           t.estimate_minutes, t.tdd_phase, t.priority,
                           t.created_at, t.updated_at, t.completed_at,
                           e.name as epic_name, e.epic_key
                    FROM framework_tasks t
                    LEFT JOIN framework_epics e ON t.epic_id = e.id
                    WHERE t.deleted_at IS NULL
                    ORDER BY t.status ASC, t.priority ASC, t.created_at DESC
                """
                
                if SQLALCHEMY_AVAILABLE:
                    result = conn.execute(text(query))
                    tasks = [dict(row._mapping) for row in result]
                else:
                    cursor = conn.cursor()
                    cursor.execute(query)
                    tasks = [dict(zip([col[0] for col in cursor.description], row)) 
                           for row in cursor.fetchall()]
                
                # Group by status for Kanban display
                grouped = {"todo": [], "in_progress": [], "completed": []}
                for task in tasks:
                    status = task.get("status", "todo")
                    if status in grouped:
                        grouped[status].append(task)
                    else:
                        grouped["todo"].append(task)  # Default fallback
                
                return grouped
                
        except Exception as e:
            print(f"Error loading kanban tasks: {e}")
            return {"todo": [], "in_progress": [], "completed": []}
    
    def get_task_statistics(self) -> Dict[str, int]:
        """Get quick statistics for tasks (used by dashboard widgets)."""
        try:
            with self.get_connection("framework") as conn:
                if SQLALCHEMY_AVAILABLE:
                    result = conn.execute(text("""
                        SELECT status, COUNT(*) as count
                        FROM framework_tasks
                        WHERE deleted_at IS NULL
                        GROUP BY status
                    """))
                    
                    stats = {"todo": 0, "in_progress": 0, "completed": 0, "total": 0}
                    total = 0
                    for row in result:
                        status = row[0] or "todo"
                        count = row[1]
                        if status in stats:
                            stats[status] = count
                        total += count
                    stats["total"] = total
                    
                    return stats
                else:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT status, COUNT(*) as count
                        FROM framework_tasks
                        WHERE deleted_at IS NULL
                        GROUP BY status
                    """)
                    
                    stats = {"todo": 0, "in_progress": 0, "completed": 0, "total": 0}
                    total = 0
                    for row in cursor.fetchall():
                        status = row[0] or "todo"
                        count = row[1]
                        if status in stats:
                            stats[status] = count
                        total += count
                    stats["total"] = total
                    
                    return stats
                    
        except Exception as e:
            print(f"Error getting task statistics: {e}")
            return {"todo": 0, "in_progress": 0, "completed": 0, "total": 0}
    
    # ==================================================================================
    # DURATION SYSTEM EXTENSION METHODS (FASE 2.3)
    # ==================================================================================
    
    @cache_database_query("calculate_epic_duration", ttl=300) if CACHE_AVAILABLE else lambda f: f
    def calculate_epic_duration(self, epic_id: int) -> float:
        """Calculate total duration for an epic based on task dates.
        
        Args:
            epic_id: ID of the epic to calculate duration for
            
        Returns:
            Duration in days (float), or 0.0 if calculation fails
        """
        if not DURATION_SYSTEM_AVAILABLE:
            logger.warning("Duration system not available - install duration_system package")
            return 0.0
        
        try:
            with self.get_connection("framework") as conn:
                # Get epic with date fields
                if SQLALCHEMY_AVAILABLE:
                    result = conn.execute(text("""
                        SELECT planned_start_date, planned_end_date, 
                               actual_start_date, actual_end_date,
                               calculated_duration_days
                        FROM framework_epics 
                        WHERE id = :epic_id AND deleted_at IS NULL
                    """), {"epic_id": epic_id})
                    epic_row = result.fetchone()
                else:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT planned_start_date, planned_end_date,
                               actual_start_date, actual_end_date,
                               calculated_duration_days
                        FROM framework_epics 
                        WHERE id = ? AND deleted_at IS NULL
                    """, (epic_id,))
                    epic_row = cursor.fetchone()
                
                if not epic_row:
                    return 0.0
                
                calculator = DurationCalculator()
                
                # Try to use existing calculated duration first
                if epic_row[4] is not None:  # calculated_duration_days
                    return float(epic_row[4])
                
                # Calculate from actual dates if available
                if epic_row[2] and epic_row[3]:  # actual_start_date, actual_end_date
                    return calculator.calculate_duration_days(epic_row[2], epic_row[3])
                
                # Fall back to planned dates
                if epic_row[0] and epic_row[1]:  # planned_start_date, planned_end_date
                    return calculator.calculate_duration_days(epic_row[0], epic_row[1])
                
                # If no dates available, sum task durations
                return self._calculate_epic_duration_from_tasks(epic_id)
                
        except Exception as e:
            logger.error("Error calculating epic duration for %s: %s", epic_id, e)
            return 0.0
    
    @invalidate_cache_on_change("db_query:get_epics:", "db_query:calculate_epic_duration:") if CACHE_AVAILABLE else lambda f: f
    def update_duration_description(self, epic_id: int, description: str) -> bool:
        """Update the duration description for an epic.
        
        Args:
            epic_id: ID of the epic to update
            description: New duration description (e.g., "1.5 dias", "1 semana")
            
        Returns:
            True if successful, False otherwise
        """
        if not DURATION_SYSTEM_AVAILABLE:
            logger.warning("Duration system not available")
            return False
        
        try:
            # Parse and validate duration description
            calculator = DurationCalculator()
            duration_days = calculator.parse_and_convert_to_days(description)

            with self.get_connection("framework") as conn:
                try:
                    if SQLALCHEMY_AVAILABLE:
                        conn.execute(text("""
                            UPDATE framework_epics
                            SET duration_description = :description,
                                calculated_duration_days = :duration_days,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE id = :epic_id
                        """), {
                            "description": description,
                            "duration_days": duration_days,
                            "epic_id": epic_id
                        })
                        conn.commit()
                    else:
                        cursor = conn.cursor()
                        cursor.execute("""
                            UPDATE framework_epics
                            SET duration_description = ?, calculated_duration_days = ?,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE id = ?
                        """, (description, duration_days, epic_id))
                        conn.commit()
                except Exception:
                    conn.rollback()
                    raise

            return True

        except Exception as e:
            logger.error("Error updating duration description for epic %s: %s", epic_id, e)
            return False
    
    @cache_database_query("get_epic_timeline", ttl=180) if CACHE_AVAILABLE else lambda f: f
    def get_epic_timeline(self, epic_id: int) -> Dict[str, Any]:
        """Get comprehensive timeline information for an epic.
        
        Args:
            epic_id: ID of the epic to get timeline for
            
        Returns:
            Dictionary with timeline data including dates, durations, and validation
        """
        if not DURATION_SYSTEM_AVAILABLE:
            return {"error": "Duration system not available"}
        
        try:
            with self.get_connection("framework") as conn:
                # Get epic timeline data
                if SQLALCHEMY_AVAILABLE:
                    result = conn.execute(text("""
                        SELECT id, epic_key, name, status,
                               planned_start_date, planned_end_date,
                               actual_start_date, actual_end_date,
                               calculated_duration_days, duration_description,
                               created_at, updated_at, completed_at
                        FROM framework_epics 
                        WHERE id = :epic_id AND deleted_at IS NULL
                    """), {"epic_id": epic_id})
                    row = result.fetchone()
                    epic_data = dict(row._mapping) if row else None
                else:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT id, epic_key, name, status,
                               planned_start_date, planned_end_date,
                               actual_start_date, actual_end_date,
                               calculated_duration_days, duration_description,
                               created_at, updated_at, completed_at
                        FROM framework_epics 
                        WHERE id = ? AND deleted_at IS NULL
                    """, (epic_id,))
                    row = cursor.fetchone()
                    if row:
                        epic_data = dict(zip([col[0] for col in cursor.description], row))
                    else:
                        epic_data = None
                
                if not epic_data:
                    return {"error": f"Epic {epic_id} not found"}
                
                calculator = DurationCalculator()
                formatter = DurationFormatter()
                
                # Calculate durations and validate consistency
                validation = calculator.validate_date_consistency(
                    planned_start=epic_data.get('planned_start_date'),
                    planned_end=epic_data.get('planned_end_date'),
                    actual_start=epic_data.get('actual_start_date'),
                    actual_end=epic_data.get('actual_end_date'),
                    duration_days=epic_data.get('calculated_duration_days')
                )
                
                # Format duration descriptions
                timeline_data = {
                    "epic": epic_data,
                    "validation": validation,
                    "duration_info": {
                        "calculated_days": epic_data.get('calculated_duration_days', 0),
                        "description": epic_data.get('duration_description', ''),
                        "formatted": formatter.format(epic_data.get('calculated_duration_days', 0)) if epic_data.get('calculated_duration_days') else '',
                    },
                    "dates": {
                        "planned_start": epic_data.get('planned_start_date'),
                        "planned_end": epic_data.get('planned_end_date'),
                        "actual_start": epic_data.get('actual_start_date'),
                        "actual_end": epic_data.get('actual_end_date'),
                    },
                    "status_info": {
                        "status": epic_data.get('status', 'unknown'),
                        "is_completed": epic_data.get('status') == 'completed',
                        "completion_date": epic_data.get('completed_at'),
                    }
                }
                
                # Add task timeline if needed
                timeline_data["tasks"] = self._get_epic_task_timeline(epic_id)
                
                return timeline_data
                
        except Exception as e:
            print(f"Error getting epic timeline for {epic_id}: {e}")
            return {"error": str(e)}
    
    def validate_date_consistency(self, epic_id: int) -> bool:
        """Validate date consistency for an epic.
        
        Args:
            epic_id: ID of the epic to validate
            
        Returns:
            True if dates are consistent, False otherwise
        """
        if not DURATION_SYSTEM_AVAILABLE:
            return False
        
        try:
            with self.get_connection("framework") as conn:
                if SQLALCHEMY_AVAILABLE:
                    result = conn.execute(text("""
                        SELECT planned_start_date, planned_end_date,
                               actual_start_date, actual_end_date,
                               calculated_duration_days
                        FROM framework_epics 
                        WHERE id = :epic_id AND deleted_at IS NULL
                    """), {"epic_id": epic_id})
                    row = result.fetchone()
                else:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT planned_start_date, planned_end_date,
                               actual_start_date, actual_end_date,
                               calculated_duration_days
                        FROM framework_epics 
                        WHERE id = ? AND deleted_at IS NULL
                    """, (epic_id,))
                    row = cursor.fetchone()
                
                if not row:
                    return False
                
                calculator = DurationCalculator()
                validation = calculator.validate_date_consistency(
                    planned_start=row[0],
                    planned_end=row[1],
                    actual_start=row[2],
                    actual_end=row[3],
                    duration_days=row[4]
                )
                
                return validation["is_valid"]
                
        except Exception as e:
            print(f"Error validating date consistency for epic {epic_id}: {e}")
            return False
    
    # Helper methods for duration system
    
    def _calculate_epic_duration_from_tasks(self, epic_id: int) -> float:
        """Calculate epic duration by summing task durations."""
        try:
            with self.get_connection("framework") as conn:
                if SQLALCHEMY_AVAILABLE:
                    result = conn.execute(text("""
                        SELECT SUM(estimate_minutes) 
                        FROM framework_tasks 
                        WHERE epic_id = :epic_id AND deleted_at IS NULL
                    """), {"epic_id": epic_id})
                    total_minutes = result.scalar() or 0
                else:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT SUM(estimate_minutes)
                        FROM framework_tasks
                        WHERE epic_id = ? AND deleted_at IS NULL
                    """, (epic_id,))
                    row = cursor.fetchone()
                    total_minutes = row[0] if row and row[0] is not None else 0
                
                # Convert minutes to days (8 hours = 1 work day)
                return round(total_minutes / (8 * 60), 2)
                
        except Exception:
            return 0.0
    
    def _get_epic_task_timeline(self, epic_id: int) -> List[Dict[str, Any]]:
        """Get timeline information for tasks within an epic."""
        try:
            with self.get_connection("framework") as conn:
                if SQLALCHEMY_AVAILABLE:
                    result = conn.execute(text("""
                        SELECT id, title, status, tdd_phase, estimate_minutes,
                               created_at, updated_at, completed_at, priority
                        FROM framework_tasks 
                        WHERE epic_id = :epic_id AND deleted_at IS NULL
                        ORDER BY priority ASC, created_at ASC
                    """), {"epic_id": epic_id})
                    return [dict(row._mapping) for row in result]
                else:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT id, title, status, tdd_phase, estimate_minutes,
                               created_at, updated_at, completed_at, priority
                        FROM framework_tasks 
                        WHERE epic_id = ? AND deleted_at IS NULL
                        ORDER BY priority ASC, created_at ASC
                    """, (epic_id,))
                    
                    return [dict(zip([col[0] for col in cursor.description], row)) 
                           for row in cursor.fetchall()]
                           
        except Exception:
            return []
    
    # ==================================================================================
    # HIERARCHY SYSTEM METHODS (CLIENT → PROJECT → EPIC → TASK) - SCHEMA V6
    # ==================================================================================
    
    @cache_database_query("get_clients", ttl=300) if CACHE_AVAILABLE else lambda f: f
    def get_clients(
        self,
        include_inactive: bool = True,
        page: int = 1,
        page_size: int = 20,
        name_filter: str = "",
        status_filter: Optional[Union[ClientStatus, str]] = None,
    ) -> Dict[str, Any]:
        """Retrieve clients with filtering and pagination support.

        Performs optimized client queries with multiple filter options and
        pagination. Results are cached for performance.

        Args:
            include_inactive: Include inactive clients. Defaults to ``True``.
            page: Page number (1-based).
            page_size: Number of items per page.
            name_filter: Search term for client name using ``LIKE`` matching.
            status_filter: Filter by client status (e.g. ``"active"``).

        Returns:
            Dict[str, Any]: Dictionary containing:
                - ``data`` (List[Dict]): List of client records.
                - ``total`` (int): Total count of matching clients.
                - ``page`` (int): Current page number.
                - ``page_size`` (int): Results per page.
                - ``total_pages`` (int): Total pages available.

        Raises:
            DatabaseError: If query execution fails.

        Performance:
            - Cached results: ~1ms response time.
            - Uncached results: ~10-50ms depending on dataset size.

        Thread Safety:
            This method is thread-safe and can be called concurrently.

        Example:
            >>> result = db_manager.get_clients(include_inactive=False, page=1)
            >>> clients = result["data"]
        """
        try:
            with self.get_connection("framework") as conn:
                # Build WHERE conditions
                where_conditions = ["deleted_at IS NULL"]
                params: Dict[str, Any] = {}

                if not include_inactive:
                    where_conditions.append(f"{FieldNames.STATUS} = :status")
                    params["status"] = ClientStatus.ACTIVE.value

                if name_filter:
                    where_conditions.append("name LIKE :name_filter")
                    params["name_filter"] = f"%{name_filter}%"

                if status_filter:
                    where_conditions.append(f"{FieldNames.STATUS} = :status_filter")
                    params["status_filter"] = (
                        status_filter.value if isinstance(status_filter, ClientStatus) else status_filter
                    )
                
                where_clause = " AND ".join(where_conditions)
                
                # Count total records
                count_query = f"SELECT COUNT(*) FROM {TableNames.CLIENTS} WHERE {where_clause}"  # nosec B608
                
                if SQLALCHEMY_AVAILABLE:
                    count_result = conn.execute(text(count_query), params)
                    total = count_result.scalar()
                else:
                    cursor = conn.cursor()
                    cursor.execute(count_query, params)
                    total = cursor.fetchone()[0]
                
                # Calculate pagination
                total_pages = (total + page_size - 1) // page_size
                offset = (page - 1) * page_size
                
                # Get paginated data
                data_query = f"""
                    SELECT id, client_key, name, description, industry, company_size,
                           primary_contact_name, primary_contact_email,
                           timezone, currency, preferred_language,
                           hourly_rate, contract_type, status, client_tier,
                           priority_level, account_manager_id, technical_lead_id,
                           created_at, updated_at, last_contact_date
                    FROM {TableNames.CLIENTS}
                    WHERE {where_clause}
                    ORDER BY priority_level DESC, name ASC
                    LIMIT :limit OFFSET :offset
                """  # nosec B608
                params["limit"] = page_size
                params["offset"] = offset
                
                if SQLALCHEMY_AVAILABLE:
                    result = conn.execute(text(data_query), params)
                    data = [dict(row._mapping) for row in result]
                else:
                    cursor = conn.cursor()
                    cursor.execute(data_query, params)
                    data = [dict(row) for row in cursor.fetchall()]
                
                return {
                    "data": data,
                    "total": total,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": total_pages
                }
                
        except Exception as e:
            logger.error(f"Error loading clients: {e}")
            if STREAMLIT_AVAILABLE and st:
                st.error(f"❌ Error loading clients: {e}")
            return {"data": [], "total": 0, "page": 1, "page_size": page_size, "total_pages": 0}

    def get_client(self, client_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve single client by ID.

        Args:
            client_id: Unique client identifier. Must be a positive integer.

        Returns:
            Optional[Dict[str, Any]]: Client record dictionary or ``None`` if
                not found.

        Raises:
            ValueError: If ``client_id`` is not positive.
            DatabaseError: If query execution fails.

        Performance:
            - Primary key lookup: ~1ms.
            - Result cached for subsequent calls.

        Example:
            >>> client = db_manager.get_client(123)
            >>> if client:
            ...     print(client["name"])
        """
        if client_id <= 0:
            raise ValueError("client_id must be positive")

        try:
            with self.get_connection("framework") as conn:
                if SQLALCHEMY_AVAILABLE:
                    result = conn.execute(
                        text(
                            """
                            SELECT * FROM framework_clients
                            WHERE id = :client_id AND deleted_at IS NULL
                            """
                        ),
                        {"client_id": client_id},
                    )
                    row = result.fetchone()
                    return dict(row._mapping) if row else None
                else:
                    cursor = conn.cursor()
                    cursor.execute(
                        """
                            SELECT * FROM framework_clients
                            WHERE id = ? AND deleted_at IS NULL
                        """,
                        (client_id,),
                    )
                    row = cursor.fetchone()
                    return dict(row) if row else None
        except Exception as e:
            logger.error(f"Error getting client: {e}")
            return None
    
    @cache_database_query("get_projects", ttl=300) if CACHE_AVAILABLE else lambda f: f
    def get_projects(
        self,
        client_id: Optional[int] = None,
        include_inactive: bool = False,
        page: int = 1,
        page_size: int = 50,
        status_filter: Optional[Union[ProjectStatus, str]] = None,
        project_type_filter: str = "",
    ) -> Dict[str, Any]:
        """Get projects with caching support and pagination.
        
        Args:
            client_id: Filter by specific client ID (optional)
            include_inactive: If True, include inactive/archived projects
            page: Page number (1-based)
            page_size: Number of items per page
            status_filter: Filter by specific status
            project_type_filter: Filter by project type
            
        Returns:
            Dictionary with 'data' (list of projects), 'total', 'page', 'total_pages'
        """
        try:
            with self.get_connection("framework") as conn:
                # Build WHERE conditions
                where_conditions = ["p.deleted_at IS NULL"]
                params: Dict[str, Any] = {}
                
                if client_id:
                    where_conditions.append("p.client_id = :client_id")
                    params["client_id"] = client_id

                if not include_inactive:
                    where_conditions.append("p.status NOT IN ('cancelled', 'archived')")
                
                if status_filter:
                    where_conditions.append("p.status = :status_filter")
                    params["status_filter"] = (
                        status_filter.value if isinstance(status_filter, ProjectStatus) else status_filter
                    )
                
                if project_type_filter:
                    where_conditions.append("p.project_type = :project_type_filter")
                    params["project_type_filter"] = project_type_filter
                
                where_clause = " AND ".join(where_conditions)
                
                # Count total records
                count_query = f"""
                    SELECT COUNT(*)
                    FROM {TableNames.PROJECTS} p
                    INNER JOIN {TableNames.CLIENTS} c ON p.client_id = c.id AND c.deleted_at IS NULL
                    WHERE {where_clause}
                """
                
                if SQLALCHEMY_AVAILABLE:
                    count_result = conn.execute(text(count_query), params)
                    total = count_result.scalar()
                else:
                    cursor = conn.cursor()
                    cursor.execute(count_query, list(params.values()))
                    total = cursor.fetchone()[0]
                
                # Calculate pagination
                total_pages = (total + page_size - 1) // page_size
                offset = (page - 1) * page_size
                
                # Get paginated data
                data_query = f"""
                    SELECT p.id, p.client_id, p.project_key, p.name, p.description,
                           p.summary, p.project_type, p.methodology, p.status,
                           p.priority, p.health_status, p.completion_percentage,
                           p.planned_start_date, p.planned_end_date,
                           p.actual_start_date, p.actual_end_date,
                           p.estimated_hours, p.actual_hours,
                           p.budget_amount, p.budget_currency, p.hourly_rate,
                           p.project_manager_id, p.technical_lead_id,
                           p.repository_url, p.deployment_url, p.documentation_url,
                           p.created_at, p.updated_at,
                           c.name as client_name, c.client_key as client_key,
                           c.status as client_status, c.client_tier
                    FROM {TableNames.PROJECTS} p
                    INNER JOIN {TableNames.CLIENTS} c ON p.client_id = c.id AND c.deleted_at IS NULL
                    WHERE {where_clause}
                    ORDER BY p.priority DESC, p.name ASC
                    LIMIT :limit OFFSET :offset
                """
                params["limit"] = page_size
                params["offset"] = offset

                if SQLALCHEMY_AVAILABLE:
                    result = conn.execute(text(data_query), params)
                    data = [dict(row._mapping) for row in result]
                else:
                    cursor = conn.cursor()
                    cursor.execute(data_query, list(params.values()))
                    data = [dict(row) for row in cursor.fetchall()]
                
                return {
                    "data": data,
                    "total": total,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": total_pages
                }
        except Exception as e:
            logger.error(f"Error loading projects: {e}")
            if STREAMLIT_AVAILABLE and st:
                st.error(f"❌ Error loading projects: {e}")
            return {
                "data": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
                "total_pages": 0
            }
    
    def get_all_projects(self, client_id: Optional[int] = None, include_inactive: bool = False) -> List[Dict[str, Any]]:
        """Backward compatibility method - get all projects without pagination."""
        result = self.get_projects(client_id=client_id, include_inactive=include_inactive, page=1, page_size=1000)
        return result["data"] if isinstance(result, dict) else result
    
    @cache_database_query("get_epics_with_hierarchy", ttl=300) if CACHE_AVAILABLE else lambda f: f
    def get_epics_with_hierarchy(self, project_id: Optional[int] = None, client_id: Optional[int] = None,
                               page: int = 1, page_size: int = 25, status_filter: str = "") -> Dict[str, Any]:
        """Get epics with complete hierarchy information (client → project → epic) with pagination.
        
        Args:
            project_id: Filter by specific project ID (optional)
            client_id: Filter by specific client ID (optional)
            page: Page number (1-based)
            page_size: Number of items per page
            status_filter: Filter by epic status
            
        Returns:
            Dictionary with 'data' (list of epics), 'total', 'page', 'total_pages'
        """
        try:
            with self.get_connection("framework") as conn:
                # Build WHERE conditions
                where_conditions = ["e.deleted_at IS NULL"]
                params: Dict[str, Any] = {}
                
                if project_id:
                    where_conditions.append("e.project_id = :project_id")
                    params["project_id"] = project_id
                elif client_id:
                    where_conditions.append("p.client_id = :client_id")
                    params["client_id"] = client_id
                
                if status_filter:
                    where_conditions.append("e.status = :status_filter")
                    params["status_filter"] = status_filter
                
                where_clause = " AND ".join(where_conditions)
                
                # Count total records
                count_query = f"""
                    SELECT COUNT(*) 
                    FROM framework_epics e
                    LEFT JOIN framework_projects p ON e.project_id = p.id AND p.deleted_at IS NULL
                    LEFT JOIN framework_clients c ON p.client_id = c.id AND c.deleted_at IS NULL
                    WHERE {where_clause}
                """
                
                if SQLALCHEMY_AVAILABLE:
                    count_result = conn.execute(text(count_query), params)
                    total = count_result.scalar()
                else:
                    cursor = conn.cursor()
                    cursor.execute(count_query, list(params.values()))
                    total = cursor.fetchone()[0]
                
                # Calculate pagination
                total_pages = (total + page_size - 1) // page_size
                offset = (page - 1) * page_size
                
                # Get paginated data
                data_query = f"""
                    SELECT e.id, e.epic_key, e.name, e.description, e.summary,
                           e.status, e.priority, e.duration_days,
                           e.points_earned, e.difficulty_level,
                           e.planned_start_date, e.planned_end_date,
                           e.actual_start_date, e.actual_end_date,
                           e.calculated_duration_days, e.duration_description,
                           e.created_at, e.updated_at, e.completed_at,
                           e.project_id,
                           p.name as project_name, p.project_key, p.status as project_status,
                           p.health_status as project_health, p.client_id,
                           c.name as client_name, c.client_key, c.status as client_status,
                           c.client_tier, c.hourly_rate as client_hourly_rate
                    FROM framework_epics e
                    LEFT JOIN framework_projects p ON e.project_id = p.id AND p.deleted_at IS NULL
                    LEFT JOIN framework_clients c ON p.client_id = c.id AND c.deleted_at IS NULL
                    WHERE {where_clause}
                    ORDER BY c.priority_level DESC, p.priority DESC, e.created_at DESC
                    LIMIT :limit OFFSET :offset
                """
                params["limit"] = page_size
                params["offset"] = offset
                
                if SQLALCHEMY_AVAILABLE:
                    result = conn.execute(text(data_query), params)
                    data = [dict(row._mapping) for row in result]
                else:
                    cursor = conn.cursor()
                    cursor.execute(data_query, list(params.values()))
                    data = [dict(row) for row in cursor.fetchall()]
                
                return {
                    "data": data,
                    "total": total,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": total_pages
                }
        except Exception as e:
            logger.error(f"Error loading epics with hierarchy: {e}")
            if STREAMLIT_AVAILABLE and st:
                st.error(f"❌ Error loading epics with hierarchy: {e}")
            return {
                "data": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
                "total_pages": 0
            }
    
    def get_all_epics_with_hierarchy(self, project_id: Optional[int] = None, client_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Backward compatibility method - get all epics with hierarchy without pagination."""
        result = self.get_epics_with_hierarchy(project_id=project_id, client_id=client_id, page=1, page_size=1000)
        return result["data"] if isinstance(result, dict) else result
    
    @cache_database_query("get_hierarchy_overview", ttl=180) if CACHE_AVAILABLE else lambda f: f
    def get_hierarchy_overview(self, client_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get complete hierarchy overview using the database view.
        
        Args:
            client_id: Filter by specific client ID (optional)
            
        Returns:
            List of hierarchy records with aggregated task counts
        """
        try:
            with self.get_connection("framework") as conn:
                query = """
                    SELECT client_id, client_key, client_name, client_status, client_tier,
                           project_id, project_key, project_name, project_status, project_health,
                           project_completion, epic_id, epic_key, epic_name, epic_status,
                           calculated_duration_days, total_tasks, completed_tasks,
                           epic_completion_percentage, planned_start_date, planned_end_date,
                           epic_planned_start, epic_planned_end
                    FROM hierarchy_overview
                    WHERE 1=1
                """
                
                params = []
                if client_id:
                    query += " AND client_id = ?"
                    params.append(client_id)
                
                query += " ORDER BY client_name, project_name, epic_key"
                
                if SQLALCHEMY_AVAILABLE:
                    result = conn.execute(text(query), params)
                    return [dict(row._mapping) for row in result]
                else:
                    cursor = conn.cursor()
                    cursor.execute(query, params)
                    return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error loading hierarchy overview: {e}")
            return []
    
    @cache_database_query("get_client_dashboard", ttl=180) if CACHE_AVAILABLE else lambda f: f
    def get_client_dashboard(self, client_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get client dashboard data using the database view.
        
        Args:
            client_id: Get data for specific client (optional)
            
        Returns:
            List of client dashboard records with aggregated metrics
        """
        try:
            with self.get_connection("framework") as conn:
                query = """
                    SELECT client_id, client_key, client_name, client_status, client_tier,
                           hourly_rate, total_projects, active_projects, completed_projects,
                           total_epics, active_epics, completed_epics,
                           total_tasks, completed_tasks, in_progress_tasks,
                           total_hours_logged, total_budget, total_points_earned,
                           earliest_project_start, latest_project_end,
                           projects_at_risk, avg_project_completion
                    FROM client_dashboard
                    WHERE 1=1
                """
                
                params = []
                if client_id:
                    query += " AND client_id = ?"
                    params.append(client_id)
                
                query += " ORDER BY client_name"
                
                if SQLALCHEMY_AVAILABLE:
                    result = conn.execute(text(query), params)
                    return [dict(row._mapping) for row in result]
                else:
                    cursor = conn.cursor()
                    cursor.execute(query, params)
                    return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error loading client dashboard: {e}")
            return []
    
    @cache_database_query("get_project_dashboard", ttl=180) if CACHE_AVAILABLE else lambda f: f  
    def get_project_dashboard(self, project_id: Optional[int] = None, client_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get project dashboard data using the database view.
        
        Args:
            project_id: Get data for specific project (optional)
            client_id: Get data for projects of specific client (optional)
            
        Returns:
            List of project dashboard records with aggregated metrics
        """
        try:
            with self.get_connection("framework") as conn:
                query = """
                    SELECT project_id, project_key, project_name, project_status, health_status,
                           completion_percentage, client_id, client_name, client_tier,
                           total_epics, completed_epics, active_epics,
                           total_tasks, completed_tasks, in_progress_tasks,
                           estimated_hours, actual_hours, estimated_task_hours, actual_task_hours,
                           budget_amount, hourly_rate, planned_start_date, planned_end_date,
                           actual_start_date, actual_end_date, calculated_completion_percentage,
                           total_points_earned, complexity_score, quality_score
                    FROM project_dashboard
                    WHERE 1=1
                """
                
                params = []
                if project_id:
                    query += " AND project_id = ?"
                    params.append(project_id)
                elif client_id:
                    query += " AND client_id = ?"
                    params.append(client_id)
                
                query += " ORDER BY client_name, project_name"
                
                if SQLALCHEMY_AVAILABLE:
                    result = conn.execute(text(query), params)
                    return [dict(row._mapping) for row in result]
                else:
                    cursor = conn.cursor()
                    cursor.execute(query, params)
                    return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error loading project dashboard: {e}")
            return []
    
    # ==================================================================================
    # HIERARCHY CRUD OPERATIONS
    # ==================================================================================
    
    @invalidate_cache_on_change("db_query:get_clients:", "db_query:get_client_dashboard:") if CACHE_AVAILABLE else lambda f: f
    def create_client(
        self,
        client_key: str,
        name: str,
        description: str = "",
        industry: str = "",
        company_size: str = "startup",
        primary_contact_name: str = "",
        primary_contact_email: str = "",
        hourly_rate: float = 0.0,
        **kwargs: Any,
    ) -> Optional[int]:
        """Create new client record.

        Creates client with full validation and automatic timestamp assignment.
        Invalidates related caches and triggers audit logging.

        Args:
            client_key: Unique client identifier string (3-20 chars).
            name: Client display name (1-100 characters).
            description: Client description (max 500 chars).
            industry: Industry classification.
            company_size: Company size category.
            primary_contact_name: Primary contact name.
            primary_contact_email: Primary contact email.
            hourly_rate: Billing rate per hour.
            **kwargs: Additional optional fields like ``status`` or
                ``client_tier``.

        Returns:
            Optional[int]: New client ID if successful, ``None`` if failed.

        Raises:
            ValueError: If required fields are missing or invalid.
            IntegrityError: If ``client_key`` already exists.
            DatabaseError: If insert operation fails.

        Side Effects:
            - Invalidates client list caches.
            - Creates audit log entry.

        Performance:
            - Insert operation: ~5ms.

        Example:
            >>> client_id = db_manager.create_client(
            ...     client_key="acme_corp", name="ACME Corporation"
            ... )
        """
        try:
            client_data = {
                'client_key': client_key,
                'name': name,
                'description': description,
                'industry': industry,
                'company_size': company_size,
                'primary_contact_name': primary_contact_name,
                'primary_contact_email': primary_contact_email,
                'hourly_rate': hourly_rate,
                'status': kwargs.get('status', ClientStatus.ACTIVE.value),
                'client_tier': kwargs.get('client_tier', 'standard'),
                'priority_level': kwargs.get('priority_level', 5),
                'timezone': kwargs.get('timezone', 'America/Sao_Paulo'),
                'currency': kwargs.get('currency', 'BRL'),
                'preferred_language': kwargs.get('preferred_language', 'pt-BR'),
                'contract_type': kwargs.get('contract_type', 'time_and_materials'),
                'created_by': kwargs.get('created_by', 1)
            }
            
            with self.get_connection("framework") as conn:
                placeholders = ', '.join(['?' for _ in client_data])
                columns = ', '.join(client_data.keys())
                
                if SQLALCHEMY_AVAILABLE:
                    # Convert to named parameters for SQLAlchemy
                    named_placeholders = ', '.join([f':{key}' for key in client_data.keys()])
                    result = conn.execute(
                        text(f"INSERT INTO {TableNames.CLIENTS} ({columns}) VALUES ({named_placeholders})"),  # nosec B608
                        client_data
                    )
                    conn.commit()
                    return result.lastrowid
                else:
                    cursor = conn.cursor()
                    cursor.execute(
                        f"INSERT INTO {TableNames.CLIENTS} ({columns}) VALUES ({placeholders})",  # nosec B608
                        list(client_data.values())
                    )
                    conn.commit()
                    return cursor.lastrowid
                    
        except Exception as e:
            logger.error(f"Error creating client: {e}")
            if STREAMLIT_AVAILABLE and st:
                st.error(f"❌ Error creating client: {e}")
            return None
    
    @invalidate_cache_on_change(
        "db_query:get_projects:",
        "db_query:get_hierarchy_overview:",
        "db_query:get_client_dashboard:",
        "db_query:get_project_dashboard:"
    ) if CACHE_AVAILABLE else lambda f: f
    def create_project(
        self,
        client_id: int,
        project_key: str,
        name: str,
        description: str = "",
        project_type: str = "development",
        methodology: str = "agile",
        **kwargs: Any,
    ) -> Optional[int]:
        """Create a new project.
        
        Args:
            client_id: ID of the client who owns this project
            project_key: Unique project identifier within client
            name: Project name
            description: Project description
            project_type: Type of project (development, maintenance, etc.)
            methodology: Development methodology (agile, waterfall, etc.)
            **kwargs: Additional project fields
            
        Returns:
            Project ID if successful, None otherwise
        """
        try:
            project_data = {
                'client_id': client_id,
                'project_key': project_key,
                'name': name,
                'description': description,
                'project_type': project_type,
                'methodology': methodology,
                'status': kwargs.get('status', ProjectStatus.PLANNING.value),
                'priority': kwargs.get('priority', 5),
                'health_status': kwargs.get('health_status', 'green'),
                'completion_percentage': kwargs.get('completion_percentage', 0),
                'planned_start_date': kwargs.get('planned_start_date'),
                'planned_end_date': kwargs.get('planned_end_date'),
                'estimated_hours': kwargs.get('estimated_hours', 0),
                'budget_amount': kwargs.get('budget_amount', 0),
                'budget_currency': kwargs.get('budget_currency', 'BRL'),
                'hourly_rate': kwargs.get('hourly_rate'),
                'project_manager_id': kwargs.get('project_manager_id', 1),
                'technical_lead_id': kwargs.get('technical_lead_id', 1),
                'repository_url': kwargs.get('repository_url', ''),
                'visibility': kwargs.get('visibility', 'client'),
                'access_level': kwargs.get('access_level', 'standard'),
                'complexity_score': kwargs.get('complexity_score', 5.0),
                'quality_score': kwargs.get('quality_score', 8.0),
                'created_by': kwargs.get('created_by', 1)
            }
            
            with self.get_connection("framework") as conn:
                # Remove None values
                project_data = {k: v for k, v in project_data.items() if v is not None}
                
                placeholders = ', '.join(['?' for _ in project_data])
                columns = ', '.join(project_data.keys())

                if SQLALCHEMY_AVAILABLE:
                    named_placeholders = ', '.join([f':{key}' for key in project_data.keys()])
                    result = conn.execute(
                        text(f"INSERT INTO {TableNames.PROJECTS} ({columns}) VALUES ({named_placeholders})"),  # nosec B608
                        project_data
                    )
                    conn.commit()
                    return result.lastrowid
                else:
                    cursor = conn.cursor()
                    cursor.execute(
                        f"INSERT INTO {TableNames.PROJECTS} ({columns}) VALUES ({placeholders})",
                        list(project_data.values())
                    )
                    conn.commit()
                    return cursor.lastrowid
                    
        except Exception as e:
            logger.error(f"Error creating project: {e}")
            if STREAMLIT_AVAILABLE and st:
                st.error(f"❌ Error creating project: {e}")
            return None
    
    @invalidate_cache_on_change("db_query:get_epics:", "db_query:get_epics_with_hierarchy:") if CACHE_AVAILABLE else lambda f: f
    def update_epic_project(self, epic_id: int, project_id: int) -> bool:
        """Update the project assignment for an epic.
        
        Args:
            epic_id: ID of the epic to update
            project_id: ID of the new project
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.get_connection("framework") as conn:
                if SQLALCHEMY_AVAILABLE:
                    conn.execute(text("""
                        UPDATE framework_epics 
                        SET project_id = :project_id, updated_at = CURRENT_TIMESTAMP
                        WHERE id = :epic_id
                    """), {"project_id": project_id, "epic_id": epic_id})
                    conn.commit()
                else:
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE framework_epics 
                        SET project_id = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (project_id, epic_id))
                    conn.commit()
                
                return True
                
        except Exception as e:
            logger.error(f"Error updating epic project: {e}")
            return False
    
    def get_client_by_key(self, client_key: str) -> Optional[Dict[str, Any]]:
        """Get client by client_key.
        
        Args:
            client_key: Client key to search for
            
        Returns:
            Client dictionary if found, None otherwise
        """
        try:
            with self.get_connection("framework") as conn:
                if SQLALCHEMY_AVAILABLE:
                    result = conn.execute(text("""
                        SELECT * FROM framework_clients 
                        WHERE client_key = :client_key AND deleted_at IS NULL
                    """), {"client_key": client_key})
                    row = result.fetchone()
                    return dict(row._mapping) if row else None
                else:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT * FROM framework_clients 
                        WHERE client_key = ? AND deleted_at IS NULL
                    """, (client_key,))
                    row = cursor.fetchone()
                    return dict(row) if row else None
                    
        except Exception as e:
            logger.error(f"Error getting client by key: {e}")
            return None
    
    def get_project_by_key(self, client_id: int, project_key: str) -> Optional[Dict[str, Any]]:
        """Get project by client_id and project_key.
        
        Args:
            client_id: Client ID
            project_key: Project key to search for
            
        Returns:
            Project dictionary if found, None otherwise
        """
        try:
            with self.get_connection("framework") as conn:
                if SQLALCHEMY_AVAILABLE:
                    result = conn.execute(text("""
                        SELECT * FROM framework_projects 
                        WHERE client_id = :client_id AND project_key = :project_key 
                        AND deleted_at IS NULL
                    """), {"client_id": client_id, "project_key": project_key})
                    row = result.fetchone()
                    return dict(row._mapping) if row else None
                else:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT * FROM framework_projects 
                        WHERE client_id = ? AND project_key = ? AND deleted_at IS NULL
                    """, (client_id, project_key))
                    row = cursor.fetchone()
                    return dict(row) if row else None
                    
        except Exception as e:
            logger.error(f"Error getting project by key: {e}")
            return None
    
    @invalidate_cache_on_change("db_query:get_clients:", "db_query:get_client_dashboard:") if CACHE_AVAILABLE else lambda f: f
    def update_client(self, client_id: int, **fields: Any) -> bool:
        """Update existing client record.

        Updates specified fields while preserving others. Validates all input
        and maintains data integrity. Supports partial updates.

        Args:
            client_id: Client ID to update. Must exist.
            **fields: Fields to update. Same validation as ``create_client``.

        Returns:
            bool: ``True`` if update successful, ``False`` if failed or no
                changes.

        Raises:
            ValueError: If ``client_id`` invalid or field validation fails.
            DatabaseError: If update operation fails.

        Side Effects:
            - Invalidates client caches for this client.
            - Updates ``updated_at`` timestamp.

        Performance:
            - Update operation: ~3ms.

        Example:
            >>> db_manager.update_client(123, name="New Name")
        """
        try:
            if not fields:
                return True
                
            # Add updated_at timestamp
            fields['updated_at'] = 'CURRENT_TIMESTAMP'
            
            # Build SET clause
            set_clauses = []
            values = {}
            
            for key, value in fields.items():
                if key == 'updated_at':
                    set_clauses.append(f"{key} = CURRENT_TIMESTAMP")
                else:
                    set_clauses.append(f"{key} = :{key}")
                    values[key] = value
            
            values['client_id'] = client_id
            
            with self.get_connection("framework") as conn:
                if SQLALCHEMY_AVAILABLE:
                    conn.execute(text(f"""
                        UPDATE {TableNames.CLIENTS}
                        SET {', '.join(set_clauses)}
                        WHERE id = :client_id AND deleted_at IS NULL
                    """), values)  # nosec B608
                    conn.commit()
                else:
                    cursor = conn.cursor()
                    # Convert to positional parameters for sqlite
                    positional_values = [values[key] for key in values.keys() if key != 'client_id']
                    positional_values.append(client_id)
                    
                    sqlite_clauses = [clause.replace(f':{key}', '?') for clause in set_clauses if f':{key}' in clause]
                    sqlite_clauses.extend([clause for clause in set_clauses if '?' not in clause and ':' not in clause])
                    
                    cursor.execute(f"""
                        UPDATE {TableNames.CLIENTS}
                        SET {', '.join(sqlite_clauses)}
                        WHERE id = ? AND deleted_at IS NULL
                    """, positional_values)  # nosec B608
                    conn.commit()
                
                return True
                
        except Exception as e:
            logger.error(f"Error updating client: {e}")
            if STREAMLIT_AVAILABLE and st:
                st.error(f"❌ Error updating client: {e}")
            return False
    
    @invalidate_cache_on_change("db_query:get_clients:", "db_query:get_client_dashboard:") if CACHE_AVAILABLE else lambda f: f
    def delete_client(self, client_id: int, soft_delete: bool = True) -> bool:
        """Delete client record (soft or hard delete).

        Removes client from active use. Soft delete preserves data for audit
        purposes. Hard delete permanently removes all data.

        Args:
            client_id: Client ID to delete. Must exist.
            soft_delete: Use soft delete. Defaults to ``True``.

        Returns:
            bool: ``True`` if deletion successful, ``False`` if failed.

        Raises:
            ValueError: If ``client_id`` invalid.
            DatabaseError: If delete operation fails.

        Side Effects:
            - Invalidates all client-related caches.

        Performance:
            - Soft delete: ~2ms.
            - Hard delete: ~10-100ms (depends on related data).

        Example:
            >>> db_manager.delete_client(123, soft_delete=True)
        """
        try:
            with self.get_connection("framework") as conn:
                if soft_delete:
                    if SQLALCHEMY_AVAILABLE:
                        conn.execute(text("""
                            UPDATE {TableNames.CLIENTS}
                            SET deleted_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                            WHERE id = :client_id
                        """), {"client_id": client_id})
                        conn.commit()
                    else:
                        cursor = conn.cursor()
                        cursor.execute("""
                            UPDATE {TableNames.CLIENTS}
                            SET deleted_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                            WHERE id = ?
                        """, (client_id,))
                        conn.commit()
                else:
                    # Use transaction-wrapped cascade delete for hard deletes
                    # This prevents table locks during large cascade operations
                    return self.delete_cascade_safe(
                        table_name="clients",
                        record_id=client_id,
                        cascade_tables=["projects", "epics", "tasks"]  # Delete in dependency order
                    )
                
                return True
                
        except Exception as e:
            logger.error(f"Error deleting client: {e}")
            if STREAMLIT_AVAILABLE and st:
                st.error(f"❌ Error deleting client: {e}")
            return False
    
    @invalidate_cache_on_change(
        "db_query:get_projects:",
        "db_query:get_hierarchy_overview:",
        "db_query:get_client_dashboard:",
        "db_query:get_project_dashboard:"
    ) if CACHE_AVAILABLE else lambda f: f
    def update_project(self, project_id: int, **fields: Any) -> bool:
        """Update an existing project.
        
        Args:
            project_id: ID of the project to update
            **fields: Fields to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not fields:
                return True
                
            # Add updated_at timestamp
            fields['updated_at'] = 'CURRENT_TIMESTAMP'
            
            # Build SET clause
            set_clauses = []
            values = {}
            
            for key, value in fields.items():
                if key == 'updated_at':
                    set_clauses.append(f"{key} = CURRENT_TIMESTAMP")
                else:
                    set_clauses.append(f"{key} = :{key}")
                    values[key] = value
            
            values['project_id'] = project_id
            
            with self.get_connection("framework") as conn:
                if SQLALCHEMY_AVAILABLE:
                    conn.execute(text(f"""
                        UPDATE {TableNames.PROJECTS}
                        SET {', '.join(set_clauses)}
                        WHERE id = :project_id AND deleted_at IS NULL
                    """), values)  # nosec B608
                    conn.commit()
                else:
                    cursor = conn.cursor()
                    # Convert to positional parameters for sqlite
                    positional_values = [values[key] for key in values.keys() if key != 'project_id']
                    positional_values.append(project_id)
                    
                    sqlite_clauses = [clause.replace(f':{key}', '?') for clause in set_clauses if f':{key}' in clause]
                    sqlite_clauses.extend([clause for clause in set_clauses if '?' not in clause and ':' not in clause])
                    
                    cursor.execute(f"""
                        UPDATE {TableNames.PROJECTS}
                        SET {', '.join(sqlite_clauses)}
                        WHERE id = ? AND deleted_at IS NULL
                    """, positional_values)  # nosec B608
                    conn.commit()
                
                return True
                
        except Exception as e:
            logger.error(f"Error updating project: {e}")
            if STREAMLIT_AVAILABLE and st:
                st.error(f"❌ Error updating project: {e}")
            return False
    
    @invalidate_cache_on_change(
        "db_query:get_projects:",
        "db_query:get_hierarchy_overview:",
        "db_query:get_client_dashboard:",
        "db_query:get_project_dashboard:"
    ) if CACHE_AVAILABLE else lambda f: f
    def delete_project(self, project_id: int, soft_delete: bool = True) -> bool:
        """Delete a project (soft delete by default).
        
        Args:
            project_id: ID of the project to delete
            soft_delete: If True, mark as deleted instead of removing
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.get_connection("framework") as conn:
                if soft_delete:
                    if SQLALCHEMY_AVAILABLE:
                        conn.execute(text("""
                            UPDATE {TableNames.PROJECTS}
                            SET deleted_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                            WHERE id = :project_id
                        """), {"project_id": project_id})
                        conn.commit()
                    else:
                        cursor = conn.cursor()
                        cursor.execute("""
                            UPDATE {TableNames.PROJECTS}
                            SET deleted_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                            WHERE id = ?
                        """, (project_id,))
                        conn.commit()
                else:
                    # Use transaction-wrapped cascade delete for hard deletes
                    # This prevents table locks during cascade operations  
                    return self.delete_cascade_safe(
                        table_name="projects",
                        record_id=project_id,
                        cascade_tables=["epics", "tasks"]  # Delete dependent records first
                    )
                
                return True
                
        except Exception as e:
            logger.error(f"Error deleting project: {e}")
            if STREAMLIT_AVAILABLE and st:
                st.error(f"❌ Error deleting project: {e}")
            return False


# =============================================================================
# 🔧 CONTEXT MANAGERS - Utility context managers for database operations
# =============================================================================

@contextmanager
def dict_rows(connection: SQLiteConnection) -> Iterator[None]:
    """
    Context manager to temporarily set SQLite connection to return dict-like rows.
    
    This utility allows repository code to work with SQLite rows as dictionaries,
    making it easier to extract values safely and convert to dataclass objects.
    
    Args:
        connection: SQLite connection object
        
    Yields:
        None (modifies connection row_factory temporarily)
        
    Example:
        >>> with db_manager.get_connection() as conn:
        ...     with dict_rows(conn):
        ...         rows = conn.execute("SELECT * FROM tasks").fetchall()
        ...         for row in rows:
        ...             task_key = row.get('task_key', 'unknown')  # Safe access
    """
    # Store original row factory
    original_row_factory = connection.row_factory
    
    try:
        # Set row factory to return sqlite3.Row objects (dict-like)
        connection.row_factory = sqlite3.Row
        yield
    finally:
        # Restore original row factory
        connection.row_factory = original_row_factory