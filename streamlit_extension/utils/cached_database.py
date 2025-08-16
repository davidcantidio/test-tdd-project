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
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
from functools import wraps

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    from streamlit_extension.utils.database import DatabaseManager
    DATABASE_MANAGER_AVAILABLE = True
except ImportError:
    DATABASE_MANAGER_AVAILABLE = False
    DatabaseManager = None

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
        if not DATABASE_MANAGER_AVAILABLE:
            raise ImportError("DatabaseManager not available")
        
        # Initialize underlying database manager
        self.db_manager = DatabaseManager(
            framework_db_path=framework_db_path,
            timer_db_path=timer_db_path
        )
        
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
            entity_type: Type of entity (client, project, epic, task)
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
            if entity_type == "client":
                # Client changes affect projects
                invalidate_cache("project_list")
                invalidate_cache("client_projects")
            elif entity_type == "project":
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
    # CLIENT OPERATIONS WITH CACHING
    # =============================================================================
    
    @cached("client_list", operation_type="quick")
    def get_clients(self, 
                   include_inactive: bool = False,
                   search_name: Optional[str] = None,
                   status_filter: Optional[str] = None,
                   tier_filter: Optional[str] = None,
                   limit: Optional[int] = None,
                   offset: int = 0) -> Dict[str, Any]:
        """Get clients with caching support."""
        start_time = time.time()
        
        try:
            result = self.db_manager.get_clients(
                include_inactive=include_inactive,
                search_name=search_name,
                status_filter=status_filter,
                tier_filter=tier_filter,
                limit=limit,
                offset=offset
            )
            
            response_time = time.time() - start_time
            operation_type = "cache_hits" if hasattr(self, '_from_cache') else "db_direct_calls"
            self._record_operation(operation_type, response_time)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error getting clients: {e}")
            self._record_operation("db_direct_calls", time.time() - start_time)
            raise
    
    @cached("client", operation_type="quick")
    def get_client(self, client_id: int) -> Optional[Dict[str, Any]]:
        """Get single client with caching."""
        start_time = time.time()
        
        try:
            result = self.db_manager.get_client(client_id)
            
            response_time = time.time() - start_time
            operation_type = "cache_hits" if hasattr(self, '_from_cache') else "db_direct_calls"
            self._record_operation(operation_type, response_time)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error getting client {client_id}: {e}")
            self._record_operation("db_direct_calls", time.time() - start_time)
            raise
    
    def create_client(self, **kwargs) -> Optional[int]:
        """Create client and invalidate related cache."""
        try:
            result = self.db_manager.create_client(**kwargs)
            
            if result:
                self._invalidate_related_cache("client")
                self.logger.debug(f"Client created: {result}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error creating client: {e}")
            raise
    
    def update_client(self, client_id: int, **kwargs) -> bool:
        """Update client and invalidate related cache."""
        try:
            result = self.db_manager.update_client(client_id, **kwargs)
            
            if result:
                self._invalidate_related_cache("client", client_id)
                self.logger.debug(f"Client updated: {client_id}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error updating client {client_id}: {e}")
            raise
    
    def delete_client(self, client_id: int, soft_delete: bool = True) -> bool:
        """Delete client and invalidate related cache."""
        try:
            result = self.db_manager.delete_client(client_id, soft_delete=soft_delete)
            
            if result:
                self._invalidate_related_cache("client", client_id)
                # Also invalidate projects related to this client
                invalidate_cache("project_list")
                self.logger.debug(f"Client deleted: {client_id}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error deleting client {client_id}: {e}")
            raise
    
    # =============================================================================
    # PROJECT OPERATIONS WITH CACHING
    # =============================================================================
    
    @cached("project_list", operation_type="quick")
    def get_projects(self,
                    client_id: Optional[int] = None,
                    include_inactive: bool = False,
                    search_name: Optional[str] = None,
                    status_filter: Optional[str] = None,
                    limit: Optional[int] = None,
                    offset: int = 0) -> Dict[str, Any]:
        """Get projects with caching support."""
        start_time = time.time()
        
        try:
            result = self.db_manager.get_projects(
                client_id=client_id,
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
            result = self.db_manager.get_project(project_id)
            
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
            result = self.db_manager.create_project(**kwargs)
            
            if result:
                self._invalidate_related_cache("project")
                # Invalidate client-related caches if client_id provided
                if "client_id" in kwargs:
                    invalidate_cache("client_projects", kwargs["client_id"])
                self.logger.debug(f"Project created: {result}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error creating project: {e}")
            raise
    
    def update_project(self, project_id: int, **kwargs) -> bool:
        """Update project and invalidate related cache."""
        try:
            result = self.db_manager.update_project(project_id, **kwargs)
            
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
            result = self.db_manager.delete_project(project_id, soft_delete=soft_delete)
            
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
            result = self.db_manager.get_epics(
                project_id=project_id,
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
            self.logger.error(f"Error getting epics: {e}")
            self._record_operation("db_direct_calls", time.time() - start_time)
            raise
    
    @cached("epic", operation_type="medium")
    def get_epic(self, epic_id: int) -> Optional[Dict[str, Any]]:
        """Get single epic with caching."""
        start_time = time.time()
        
        try:
            result = self.db_manager.get_epic(epic_id)
            
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
            result = self.db_manager.get_tasks(
                epic_id=epic_id,
                include_completed=include_completed,
                search_title=search_title,
                status_filter=status_filter,
                tdd_phase_filter=tdd_phase_filter,
                limit=limit,
                offset=offset
            )
            
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
            result = self.db_manager.get_task(task_id)
            
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
                "total_clients": len(self.get_clients().get("data", [])),
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
        return self.db_manager.execute_query(query, params)
    
    def check_database_health(self) -> Dict[str, Any]:
        """Check database health (no caching)."""
        return self.db_manager.check_database_health()
    
    # =============================================================================
    # PASSTHROUGH METHODS FOR COMPATIBILITY
    # =============================================================================
    
    def __getattr__(self, name):
        """Passthrough for any methods not explicitly cached."""
        if hasattr(self.db_manager, name):
            attr = getattr(self.db_manager, name)
            if callable(attr):
                def wrapper(*args, **kwargs):
                    result = attr(*args, **kwargs)
                    # Record as direct DB call
                    self._record_operation("db_direct_calls", 0.0)
                    return result
                return wrapper
            return attr
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")


# Export main class
__all__ = ["CachedDatabaseManager"]