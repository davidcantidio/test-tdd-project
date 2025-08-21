"""
📊 Data Providers

Centralized data fetching layer for the application.
Handles caching, error recovery, and data normalization.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import logging

# Safe streamlit import
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False
    st = None

# Import centralized cache decorator - NO FALLBACK NEEDED
from ..utils.streamlit_helpers import cache_data

# Database imports with fallbacks
try:
    from ..database.queries import list_epics, list_tasks, get_user_stats
    from ..database.health import check_health
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False
    def list_epics() -> List[Dict[str, Any]]:
        return []
    def list_tasks(epic_id: Any) -> List[Dict[str, Any]]:
        return []
    def get_user_stats(*args, **kwargs) -> Dict[str, Any]:
        return {}
    def check_health() -> Dict[str, Any]:
        return {"status": "unknown"}

# Service health check
try:
    from ..utils.app_setup import check_services_health
    SERVICES_HEALTH_AVAILABLE = True
except ImportError:
    SERVICES_HEALTH_AVAILABLE = False
    def check_services_health() -> Dict[str, Any]:
        return {
            "database": {"status": "unknown", "message": ""},
            "services": {"status": "unknown", "message": ""},
            "overall": {"status": "unknown", "healthy": False},
        }

# Exception handling
try:
    from ..utils.exception_handler import safe_streamlit_operation
    EXCEPTION_HANDLER_AVAILABLE = True
except ImportError:
    EXCEPTION_HANDLER_AVAILABLE = False
    def safe_streamlit_operation(func, *args, default_return=None, operation_name=None, **kwargs):
        """Fallback safe operation wrapper."""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.info(f"🚨 OPERATION ERROR ({operation_name or 'unknown'}): {e}")
            return default_return

logger = logging.getLogger(__name__)

# Data normalization helpers
def _ensure_list(value: Any) -> List[Any]:
    """Ensure value is a list, handling various data formats."""
    if isinstance(value, list):
        return value
    if isinstance(value, dict) and "data" in value:
        data = value.get("data") or []
        return data if isinstance(data, list) else []
    return []

# === DATA PROVIDERS ===========================================================

@cache_data(ttl=30)
def fetch_user_stats(user_id: Optional[int] = None) -> Dict[str, Any]:
    """Fetch user statistics using AnalyticsService with fallbacks."""
    def _call():
        try:
            # Use AnalyticsService instead of direct database queries
            from ..services.service_container import ServiceContainer
            
            container = ServiceContainer()
            analytics = container.get_analytics_service()
            
            # Get dashboard summary with 30-day window
            result = analytics.get_dashboard_summary(days=30)
            
            if result.success:
                # Map AnalyticsService data to format expected by analytics_cards
                dashboard_data = result.data
                overview = dashboard_data.get('overview', {})
                productivity = dashboard_data.get('productivity', {})
                tdd_effectiveness = dashboard_data.get('tdd_effectiveness', {})
                
                return {
                    # Map to expected keys for analytics_cards compatibility
                    'completed_tasks': overview.get('total_tasks', 0),
                    'weekly_completion': productivity.get('weekly_completion_rate', 0.0),
                    'focus_series': productivity.get('daily_focus_hours', []),
                    'total_tasks': overview.get('total_tasks', 0),
                    'focus_time_hours': productivity.get('total_focus_time', 0.0),
                    'productivity_score': tdd_effectiveness.get('productivity_score', 0.0),
                    'current_streak': productivity.get('current_streak', 0),
                    # Include raw dashboard data for advanced components
                    '_dashboard_summary': dashboard_data
                }
            else:
                # Fallback to legacy approach on service failure
                return get_user_stats(user_id=user_id or 1)
                
        except Exception:
            # Ultimate fallback to legacy system
            try:
                return get_user_stats(user_id=user_id or 1)
            except Exception:
                return {}
    
    return safe_streamlit_operation(_call, default_return={}, operation_name="user_stats")

@cache_data(ttl=30)
def fetch_epics() -> List[Dict[str, Any]]:
    """Fetch list of epics with error handling and normalization."""
    result = safe_streamlit_operation(
        list_epics, 
        default_return=[], 
        operation_name="list_epics"
    )
    return _ensure_list(result)

@cache_data(ttl=30)
def fetch_tasks(epic_id: Any) -> List[Dict[str, Any]]:
    """Fetch tasks for a specific epic with error handling."""
    def _call():
        return list_tasks(epic_id)
    
    result = safe_streamlit_operation(
        _call, 
        default_return=[], 
        operation_name=f"list_tasks_{epic_id}"
    )
    return _ensure_list(result)

@cache_data(ttl=20)
def fetch_health() -> Dict[str, Any]:
    """Fetch system health status from available sources."""
    if SERVICES_HEALTH_AVAILABLE:
        return check_services_health()
    return {
        "database": check_health(),
        "services": {"status": "unknown"},
        "overall": {"status": "unknown", "healthy": False},
    }

# === CACHE MANAGEMENT =========================================================

def clear_all_caches() -> None:
    """Clear all data provider caches."""
    if not STREAMLIT_AVAILABLE:
        return
        
    try:
        if hasattr(st, "cache_data"):
            st.cache_data.clear()
        if hasattr(st, "cache_resource"):
            st.cache_resource.clear()
        logger.info("Data provider caches cleared")
    except Exception as e:
        logger.warning(f"Error clearing caches: {e}")

def clear_specific_cache(cache_key: str) -> None:
    """Clear specific cache by key pattern."""
    if not STREAMLIT_AVAILABLE:
        return
        
    try:
        # Clear specific function caches
        if cache_key == "user_stats":
            fetch_user_stats.clear()
        elif cache_key == "epics":
            fetch_epics.clear()
        elif cache_key == "health":
            fetch_health.clear()
        elif cache_key.startswith("tasks_"):
            # Clear all task caches - Streamlit doesn't support selective clearing
            fetch_tasks.clear()
        
        logger.info(f"Cache cleared for: {cache_key}")
    except Exception as e:
        logger.warning(f"Error clearing cache {cache_key}: {e}")

# === DATA REFRESH UTILITIES ===================================================

def refresh_user_data(user_id: Optional[int] = None) -> Dict[str, Any]:
    """Force refresh user statistics by clearing cache first."""
    clear_specific_cache("user_stats")
    return fetch_user_stats(user_id)

def refresh_epic_data() -> List[Dict[str, Any]]:
    """Force refresh epic data by clearing cache first."""
    clear_specific_cache("epics")
    return fetch_epics()

def refresh_task_data(epic_id: Any) -> List[Dict[str, Any]]:
    """Force refresh task data for specific epic."""
    clear_specific_cache(f"tasks_{epic_id}")
    return fetch_tasks(epic_id)

def refresh_health_data() -> Dict[str, Any]:
    """Force refresh health status."""
    clear_specific_cache("health")
    return fetch_health()

def refresh_all_data() -> Dict[str, Any]:
    """Force refresh all data by clearing all caches."""
    clear_all_caches()
    return {
        "user_stats": fetch_user_stats(),
        "epics": fetch_epics(),
        "health": fetch_health(),
        "refreshed_at": "now"
    }

# === MODULE HEALTH CHECK ======================================================

def check_data_provider_health() -> Dict[str, Any]:
    """Check health of data provider dependencies."""
    return {
        "streamlit_available": STREAMLIT_AVAILABLE,
        "database_available": DATABASE_AVAILABLE,
        "services_health_available": SERVICES_HEALTH_AVAILABLE,
        "exception_handler_available": EXCEPTION_HANDLER_AVAILABLE,
        "cache_functional": STREAMLIT_AVAILABLE and hasattr(st, "cache_data") if st else False,
        "status": "healthy" if all([
            STREAMLIT_AVAILABLE, 
            DATABASE_AVAILABLE, 
            EXCEPTION_HANDLER_AVAILABLE
        ]) else "degraded"
    }

# === EXPORTS ==================================================================

__all__ = [
    # Core data fetchers
    "fetch_user_stats",
    "fetch_epics", 
    "fetch_tasks",
    "fetch_health",
    
    # Cache management
    "clear_all_caches",
    "clear_specific_cache",
    
    # Data refresh utilities
    "refresh_user_data",
    "refresh_epic_data", 
    "refresh_task_data",
    "refresh_health_data",
    "refresh_all_data",
    
    # Health check
    "check_data_provider_health",
]