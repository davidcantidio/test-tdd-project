"""
🗄️ Cached Database Manager - High-Performance Integration

Wrapper around existing DatabaseManager with intelligent Redis caching.
Resolves performance bottlenecks from report.md:

- Heavy SQL queries without pagination (cached aggregations)
- Expensive joins beyond per-function decorators (cached results)
- Streamlit reruns causing repeated DB hits (cached operations)
- Large dataset operations causing UI lag (cached with pagination)

Integration Strategy:
- Transparent caching layer over existing DatabaseManager
- Smart cache invalidation on data modifications
- Fallback to direct DB operations when cache unavailable
- Performance metrics and monitoring
- Thread-safe operations
"""

import sys
import time
import threading
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple, Iterable, Callable
from functools import wraps
from contextlib import contextmanager

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent.parent))


class CachedDatabase:
    """SQLite helper with row_factory, thread-safety and context management."""

    def __init__(self, path: str, init_pragmas: Optional[Iterable[str]] = None):
        self.path = path
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._lock = threading.RLock()
        for pragma in (init_pragmas or ("PRAGMA journal_mode=WAL;", "PRAGMA synchronous=NORMAL;")):
            try:
                self._conn.execute(pragma)
            except Exception:
                pass

    @contextmanager
    def _cursor(self):
        with self._lock:
            cur = self._conn.cursor()
            try:
                yield cur
            finally:
                cur.close()

    def query(self, sql: str, params: Tuple[Any, ...] = ()) -> List[Dict[str, Any]]:
        with self._cursor() as cur:
            cur.execute(sql, params)
            return [dict(row) for row in cur.fetchall()]

# Modular database imports - complete migration from DatabaseManager
from streamlit_extension.database import (
    get_connection, transaction, list_epics, list_tasks, list_projects,
    execute_cached_query, get_connection_context
)
from streamlit_extension.services import ServiceContainer
# Cache integration imports
from functools import lru_cache

# No more DatabaseManager dependency - fully modular
DATABASE_MANAGER_AVAILABLE = False  # Migrated to modular API

try:
    from .redis_cache import (
        get_cache_manager, cached, invalidate_cache, 
        CacheStrategy, get_cache_stats
    )
    REDIS_CACHE_AVAILABLE = True
except ImportError:
    REDIS_CACHE_AVAILABLE = False
    get_cache_manager = cached = invalidate_cache = None
    CacheStrategy = get_cache_stats = None

try:
    from log_sanitization import create_secure_logger
    LOG_SANITIZATION_AVAILABLE = True
except ImportError:
    LOG_SANITIZATION_AVAILABLE = False
    import logging


class CachedDatabaseManager:
    """
    High-performance database manager with intelligent Redis caching.
    
    Wraps existing DatabaseManager with transparent caching layer that:
    - Caches expensive queries (aggregations, joins, searches)
    - Invalidates cache on data modifications
    - Provides fallback to direct DB when cache unavailable
    - Tracks performance metrics
    - Maintains data consistency
    """
    
    def __init__(self, 
                 framework_db_path: str, 
                 timer_db_path: Optional[str] = None,
                 enable_cache: bool = True,
                 cache_debug: bool = False):
        """
        Initialize cached database manager.
        
        Args:
            framework_db_path: Path to framework database
            timer_db_path: Path to timer database (optional)
            enable_cache: Whether to enable caching
            cache_debug: Enable cache debug logging
        """
        # Initialize with modular database API instead of DatabaseManager
        self.framework_db_path = framework_db_path
        self.timer_db_path = timer_db_path
        self.connection_context = get_connection_context(framework_db_path)
        
        # Cache configuration
        self.enable_cache = enable_cache and REDIS_CACHE_AVAILABLE
        self.cache_debug = cache_debug
        
        # Performance tracking
        self.performance_stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "db_direct_calls": 0,
            "total_operations": 0,
            "avg_response_time": 0.0,
            "last_reset": time.time()
        }
        self._stats_lock = threading.Lock()
        
        # Setup logging
        self._setup_logging()
        
        # Cache manager
        self.cache_manager = get_cache_manager() if self.enable_cache else None
        
        if self.enable_cache:
            self.logger.info("Cached database manager initialized with Redis caching")
        else:
            self.logger.info("Cached database manager initialized without caching (fallback mode)")
    
    def _setup_logging(self):
        """Setup secure logging."""
        if LOG_SANITIZATION_AVAILABLE:
            self.logger = create_secure_logger('cached_database')
        else:
            self.logger = logging.getLogger('cached_database')
            self.logger.setLevel(logging.INFO)
            
            if not self.logger.handlers:
                handler = logging.StreamHandler()
                formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
                handler.setFormatter(formatter)
                self.logger.addHandler(handler)
    
    def _record_operation(self, operation_type: str, response_time: float):
        """Record operation statistics."""
        with self._stats_lock:
            self.performance_stats["total_operations"] += 1
            self.performance_stats[operation_type] += 1
            
            # Update average response time
            current_avg = self.performance_stats["avg_response_time"]
            total_ops = self.performance_stats["total_operations"]
            self.performance_stats["avg_response_time"] = (
                (current_avg * (total_ops - 1) + response_time) / total_ops
            )
    
    def _invalidate_related_cache(self, entity_type: str, entity_id: Optional[int] = None, **kwargs):
        """
        Invalidate cache entries related to data modification.
        
        Args:
            entity_type: Type of entity (project, epic, task)
            entity_id: Specific entity ID (if applicable)
            **kwargs: Additional parameters for cache invalidation
        """
        if not self.enable_cache:
            return
        
        try:
            # Invalidate specific entity cache
            if entity_id:
                invalidate_cache(entity_type, entity_id)
            
            # Invalidate list caches
            invalidate_cache(f"{entity_type}_list")
            invalidate_cache(f"{entity_type}_search")
            
            # Invalidate analytics caches
            invalidate_cache("analytics")
            invalidate_cache("aggregation")
            
            # Entity-specific invalidations
            if entity_type == "project":
                # Project changes affect epics
                invalidate_cache("epic_list")
                invalidate_cache("project_epics")
            elif entity_type == "epic":
                # Epic changes affect tasks
                invalidate_cache("task_list")
                invalidate_cache("epic_tasks")
            elif entity_type == "task":
                # Task changes affect epic progress
                if "epic_id" in kwargs:
                    invalidate_cache("epic", kwargs["epic_id"])
                    invalidate_cache("epic_progress")
            
            if self.cache_debug:
                self.logger.debug(f"Cache invalidated for {entity_type} operations")
                
        except Exception as e:
            self.logger.error(f"Cache invalidation error: {e}")
    
    # =============================================================================
    # PROJECT OPERATIONS WITH CACHING
    # =============================================================================
    
    @cached("project_list", operation_type="quick")
    def get_projects(self,
                    include_inactive: bool = False,
                    search_name: Optional[str] = None,
                    status_filter: Optional[str] = None,
                    limit: Optional[int] = None,
                    offset: int = 0) -> Dict[str, Any]:
        """Get projects with caching support."""
        start_time = time.time()
        
        try:
            # Use modular API for project queries
            result = list_projects(
                include_inactive=include_inactive,
                search_name=search_name,
                status_filter=status_filter,
                limit=limit,
                offset=offset
            )
            
            response_time = time.time() - start_time
            operation_type = "cache_hits" if hasattr(self, '_from_cache') else "db_direct_calls"
            self._record_operation(operation_type, response_time)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error getting projects: {e}")
            self._record_operation("db_direct_calls", time.time() - start_time)
            raise
    
    @cached("project", operation_type="quick")
    def get_project(self, project_id: int) -> Optional[Dict[str, Any]]:
        """Get single project with caching."""
        start_time = time.time()
        
        try:
            # Use modular API for single project query
            with get_connection() as conn:
                result = execute_cached_query(
                    "SELECT * FROM framework_projects WHERE id = ?",
                    (project_id,),
                    conn
                )
                # Convert to expected format
                result = result[0] if result else None
            
            response_time = time.time() - start_time
            operation_type = "cache_hits" if hasattr(self, '_from_cache') else "db_direct_calls"
            self._record_operation(operation_type, response_time)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error getting project {project_id}: {e}")
            self._record_operation("db_direct_calls", time.time() - start_time)
            raise
    
    def create_project(self, **kwargs) -> Optional[int]:
        """Create project and invalidate related cache."""
        try:
            # Use modular API for project creation
            with transaction() as conn:
                cursor = conn.execute(
                    "INSERT INTO framework_projects (project_key, name, description, status) VALUES (?, ?, ?, 'active')",
                    (kwargs.get('project_key'), kwargs.get('name'), kwargs.get('description', ''))
                )
                result = cursor.lastrowid
            
            if result:
                self._invalidate_related_cache("project")
                self.logger.debug(f"Project created: {result}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error creating project: {e}")
            raise
    
    def update_project(self, project_id: int, **kwargs) -> bool:
        """Update project and invalidate related cache."""
        try:
            # Use modular API for project update
            with transaction() as conn:
                # Build dynamic update query
                set_clauses = []
                params = []
                for key, value in kwargs.items():
                    if key in ['name', 'description', 'status', 'project_key']:
                        set_clauses.append(f"{key} = ?")
                        params.append(value)
                
                if set_clauses:
                    params.append(project_id)
                    query = f"UPDATE framework_projects SET {', '.join(set_clauses)} WHERE id = ?"
                    cursor = conn.execute(query, params)
                    result = cursor.rowcount > 0
                else:
                    result = False
            
            if result:
                self._invalidate_related_cache("project", project_id)
                self.logger.debug(f"Project updated: {project_id}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error updating project {project_id}: {e}")
            raise
    
    def delete_project(self, project_id: int, soft_delete: bool = True) -> bool:
        """Delete project and invalidate related cache."""
        try:
            # Use modular API for project deletion
            with transaction() as conn:
                if soft_delete:
                    cursor = conn.execute(
                        "UPDATE framework_projects SET status = 'deleted' WHERE id = ?",
                        (project_id,)
                    )
                else:
                    cursor = conn.execute(
                        "DELETE FROM framework_projects WHERE id = ?",
                        (project_id,)
                    )
                result = cursor.rowcount > 0
            
            if result:
                self._invalidate_related_cache("project", project_id)
                # Also invalidate epics related to this project
                invalidate_cache("epic_list")
                self.logger.debug(f"Project deleted: {project_id}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error deleting project {project_id}: {e}")
            raise
    
    # =============================================================================
    # EPIC OPERATIONS WITH CACHING
    # =============================================================================
    
    @cached("epic_list", operation_type="medium")
    def get_epics(self,
                 project_id: Optional[int] = None,
                 include_inactive: bool = False,
                 search_name: Optional[str] = None,
                 status_filter: Optional[str] = None,
                 limit: Optional[int] = None,
                 offset: int = 0) -> List[Dict[str, Any]]:
        """Get epics with caching support."""
        start_time = time.time()
        
        try:
            # Use modular API for epic queries
            if project_id:
                # Filter by project_id using SQL
                with get_connection() as conn:
                    query = "SELECT * FROM framework_epics WHERE project_id = ?"
                    params = [project_id]
                    
                    if not include_inactive:
                        query += " AND status != 'inactive'"
                    if search_name:
                        query += " AND name LIKE ?"
                        params.append(f"%{search_name}%")
                    if status_filter:
                        query += " AND status = ?"
                        params.append(status_filter)
                    if limit:
                        query += " LIMIT ?"
                        params.append(limit)
                    if offset:
                        query += " OFFSET ?"
                        params.append(offset)
                    
                    result = execute_cached_query(query, params, conn)
            else:
                # Use list_epics for general epic queries
                result = list_epics()
            
            response_time = time.time() - start_time
            operation_type = "cache_hits" if hasattr(self, '_from_cache') else "db_direct_calls"
            self._record_operation(operation_type, response_time)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error getting epics: {e}")
            self._record_operation("db_direct_calls", time.time() - start_time)
            # Fallback opcional (comentado) para modular API
            # with get_connection() as conn:
            #     result = list_epics()
            raise
    
    @cached("epic", operation_type="medium")
    def get_epic(self, epic_id: int) -> Optional[Dict[str, Any]]:
        """Get single epic with caching."""
        start_time = time.time()
        
        try:
            # Use modular API for single epic query
            with get_connection() as conn:
                result = execute_cached_query(
                    "SELECT * FROM framework_epics WHERE id = ?",
                    (epic_id,),
                    conn
                )
                result = result[0] if result else None
            
            response_time = time.time() - start_time
            operation_type = "cache_hits" if hasattr(self, '_from_cache') else "db_direct_calls"
            self._record_operation(operation_type, response_time)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error getting epic {epic_id}: {e}")
            self._record_operation("db_direct_calls", time.time() - start_time)
            raise
    
    # =============================================================================
    # TASK OPERATIONS WITH CACHING  
    # =============================================================================
    
    @cached("task_list", operation_type="medium")
    def get_tasks(self,
                 epic_id: Optional[int] = None,
                 include_completed: bool = True,
                 search_title: Optional[str] = None,
                 status_filter: Optional[str] = None,
                 tdd_phase_filter: Optional[str] = None,
                 limit: Optional[int] = None,
                 offset: int = 0) -> List[Dict[str, Any]]:
        """Get tasks with caching support."""
        start_time = time.time()
        
        try:
            # Use modular API for task queries
            if epic_id:
                result = list_tasks(epic_id)
                # Apply filters if needed
                if not include_completed:
                    result = [t for t in result if t.get('status') != 'completed']
                if search_title:
                    result = [t for t in result if search_title.lower() in t.get('title', '').lower()]
                if status_filter:
                    result = [t for t in result if t.get('status') == status_filter]
                if tdd_phase_filter:
                    result = [t for t in result if t.get('tdd_phase') == tdd_phase_filter]
                # Apply pagination
                if offset:
                    result = result[offset:]
                if limit:
                    result = result[:limit]
            else:
                # Get all tasks using modular API
                with get_connection() as conn:
                    query = "SELECT * FROM framework_tasks"
                    params = []
                    
                    conditions = []
                    if not include_completed:
                        conditions.append("status != 'completed'")
                    if search_title:
                        conditions.append("title LIKE ?")
                        params.append(f"%{search_title}%")
                    if status_filter:
                        conditions.append("status = ?")
                        params.append(status_filter)
                    if tdd_phase_filter:
                        conditions.append("tdd_phase = ?")
                        params.append(tdd_phase_filter)
                    
                    if conditions:
                        query += " WHERE " + " AND ".join(conditions)
                    
                    if limit:
                        query += " LIMIT ?"
                        params.append(limit)
                    if offset:
                        query += " OFFSET ?"
                        params.append(offset)
                    
                    result = execute_cached_query(query, params, conn)
            
            response_time = time.time() - start_time
            operation_type = "cache_hits" if hasattr(self, '_from_cache') else "db_direct_calls"
            self._record_operation(operation_type, response_time)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error getting tasks: {e}")
            self._record_operation("db_direct_calls", time.time() - start_time)
            raise
    
    @cached("task", operation_type="medium")
    def get_task(self, task_id: int) -> Optional[Dict[str, Any]]:
        """Get single task with caching."""
        start_time = time.time()
        
        try:
            # Use modular API for single task query
            with get_connection() as conn:
                result = execute_cached_query(
                    "SELECT * FROM framework_tasks WHERE id = ?",
                    (task_id,),
                    conn
                )
                result = result[0] if result else None
            
            response_time = time.time() - start_time
            operation_type = "cache_hits" if hasattr(self, '_from_cache') else "db_direct_calls"
            self._record_operation(operation_type, response_time)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error getting task {task_id}: {e}")
            self._record_operation("db_direct_calls", time.time() - start_time)
            raise
    
    # =============================================================================
    # ANALYTICS AND AGGREGATIONS WITH HEAVY CACHING
    # =============================================================================
    
    @cached("analytics_dashboard", operation_type="heavy")
    def get_dashboard_analytics(self) -> Dict[str, Any]:
        """Get dashboard analytics with heavy caching."""
        start_time = time.time()
        
        try:
            # This would be a heavy aggregation query
            result = {
                "total_projects": len(self.get_projects().get("data", [])),
                "total_epics": len(self.get_epics()),
                "total_tasks": len(self.get_tasks()),
                "completed_tasks": len([t for t in self.get_tasks() if t.get("status") == "completed"]),
                "in_progress_tasks": len([t for t in self.get_tasks() if t.get("status") == "in_progress"]),
                "cache_info": self.get_performance_stats()
            }
            
            response_time = time.time() - start_time
            operation_type = "cache_hits" if hasattr(self, '_from_cache') else "db_direct_calls"
            self._record_operation(operation_type, response_time)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error getting dashboard analytics: {e}")
            self._record_operation("db_direct_calls", time.time() - start_time)
            raise
    
    # =============================================================================
    # CACHE MANAGEMENT AND MONITORING
    # =============================================================================
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        with self._stats_lock:
            stats = self.performance_stats.copy()
            
            # Calculate hit rate
            total_cache_ops = stats["cache_hits"] + stats["cache_misses"]
            if total_cache_ops > 0:
                stats["cache_hit_rate"] = (stats["cache_hits"] / total_cache_ops) * 100
            else:
                stats["cache_hit_rate"] = 0.0
            
            # Add cache manager stats if available
            if self.enable_cache:
                stats["redis_stats"] = get_cache_stats()
            
            return stats
    
    def reset_performance_stats(self):
        """Reset performance statistics."""
        with self._stats_lock:
            self.performance_stats = {
                "cache_hits": 0,
                "cache_misses": 0,
                "db_direct_calls": 0,
                "total_operations": 0,
                "avg_response_time": 0.0,
                "last_reset": time.time()
            }
    
    def flush_cache(self) -> bool:
        """Flush all cache data."""
        if not self.enable_cache:
            return False
        
        try:
            from .redis_cache import flush_cache
            result = flush_cache()
            self.logger.info("Cache flushed successfully")
            return result
        except Exception as e:
            self.logger.error(f"Error flushing cache: {e}")
            return False
    
    def get_cache_status(self) -> Dict[str, Any]:
        """Get comprehensive cache status."""
        return {
            "enabled": self.enable_cache,
            "available": self.cache_manager.is_available if self.cache_manager else False,
            "performance": self.get_performance_stats(),
            "redis_info": get_cache_stats() if self.enable_cache else None
        }
    
    # =============================================================================
    # DIRECT DATABASE OPERATIONS (NO CACHE)
    # =============================================================================
    
    def execute_direct_query(self, query: str, params: Optional[Tuple] = None) -> Any:
        """Execute direct database query without caching."""
        with get_connection() as conn:
            cursor = conn.execute(query, params or ())
            if query.strip().upper().startswith('SELECT'):
                return cursor.fetchall()
            else:
                return cursor.rowcount
    
    def check_database_health(self) -> Dict[str, Any]:
        """Check database health (no caching)."""
        try:
            with get_connection() as conn:
                cursor = conn.execute("SELECT 1")
                result = cursor.fetchone()
                return {
                    "status": "healthy" if result else "unhealthy",
                    "connection": "ok",
                    "query_test": "passed" if result else "failed"
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "connection": "failed",
                "error": str(e)
            }
    
    # =============================================================================
    # PASSTHROUGH METHODS FOR COMPATIBILITY
    # =============================================================================
    
    def __getattr__(self, name):
        """Fallback for any methods not explicitly implemented."""
        # Instead of DatabaseManager passthrough, provide helpful error
        if name in ['db_manager', 'get_connection', 'execute_query']:
            raise AttributeError(
                f"'{name}' not available - CachedDatabaseManager has been migrated to modular API. "
                "Use direct modular database functions instead."
            )
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")


class HybridCachedDatabase:
    """Cached database with hybrid API support."""

    def __init__(self):
        # Modular database integration
        self.connection_context = get_connection_context()

        # Service layer setup  
        self.service_container = ServiceContainer()

        # Cache parameters (simples e local)
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes

    @lru_cache(maxsize=1000)
    def get_cached_epics(self):
        """Get epics with caching via modular API."""
        try:
            # Use only modular API - no more legacy fallback
            return list_epics()
        except Exception as e:
            # Log error but don't fallback to legacy
            if hasattr(self, 'logger'):
                self.logger.error(f"Failed to get epics from modular API: {e}")
            return []

    def get_cached_connection(self):
        """Get cached database connection."""
        try:
            return get_connection()  # Direct modular API only
        except Exception as e:
            # Log error but don't fallback to legacy
            if hasattr(self, 'logger'):
                self.logger.error(f"Failed to get connection from modular API: {e}")
            raise RuntimeError(f"Database connection failed: {e}")


# Export main class
__all__ = ["CachedDatabaseManager"]
