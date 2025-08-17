"""
🚀 Application Setup Utilities

Centralized setup and initialization for the Streamlit application.
Handles service container initialization, database setup, and application state.
"""

import logging
from typing import Optional, Tuple, Dict, Any
from pathlib import Path

try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False
    st = None

from .database import DatabaseManager
from ..services import (
    ServiceContainer, 
    initialize_service_container, 
    get_service_container,
    shutdown_service_container,
    ServiceError
)
from .exception_handler import safe_streamlit_operation

# Global variables for caching
_db_manager: Optional[DatabaseManager] = None
_service_container: Optional[ServiceContainer] = None

logger = logging.getLogger(__name__)


def get_database_manager(force_new: bool = False) -> Optional[DatabaseManager]:
    """
    Get or create a database manager instance.
    
    Args:
        force_new: If True, creates a new instance regardless of cache
        
    Returns:
        DatabaseManager instance or None if creation fails
    """
    global _db_manager
    
    if _db_manager is None or force_new:
        try:
            # Use default database paths relative to project root
            _db_manager = DatabaseManager()
            logger.info("Database manager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database manager: {e}")
            if STREAMLIT_AVAILABLE:
                st.error(f"❌ Database initialization failed: {e}")
            return None
    
    return _db_manager


def get_app_service_container(force_new: bool = False) -> Optional[ServiceContainer]:
    """
    Get or create the application service container.
    
    Args:
        force_new: If True, creates a new container regardless of cache
        
    Returns:
        ServiceContainer instance or None if creation fails
    """
    global _service_container
    
    if _service_container is None or force_new:
        try:
            # Get database manager
            db_manager = get_database_manager()
            if db_manager is None:
                return None
            
            # Initialize service container
            _service_container = initialize_service_container(
                db_manager=db_manager,
                lazy_loading=True
            )
            logger.info("Service container initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize service container: {e}")
            if STREAMLIT_AVAILABLE:
                st.error(f"❌ Service initialization failed: {e}")
            return None
    
    return _service_container


def initialize_streamlit_session():
    """
    Initialize Streamlit session state with application services.
    
    This should be called early in the Streamlit app lifecycle.
    """
    if not STREAMLIT_AVAILABLE:
        return
    
    # Initialize session state keys
    if "services_initialized" not in st.session_state:
        st.session_state.services_initialized = False
    
    if "db_manager" not in st.session_state:
        st.session_state.db_manager = None
    
    if "service_container" not in st.session_state:
        st.session_state.service_container = None
    
    # Initialize services if not already done
    if not st.session_state.services_initialized:
        with st.spinner("🔧 Initializing application services..."):
            # Initialize database manager
            db_manager = get_database_manager()
            if db_manager:
                st.session_state.db_manager = db_manager
                
                # Initialize service container
                service_container = get_app_service_container()
                if service_container:
                    st.session_state.service_container = service_container
                    st.session_state.services_initialized = True
                    logger.info("Streamlit session services initialized")
                else:
                    st.error("❌ Failed to initialize service container")
            else:
                st.error("❌ Failed to initialize database manager")


def get_session_services() -> Tuple[Optional[DatabaseManager], Optional[ServiceContainer]]:
    """
    Get database manager and service container from session state.
    
    Returns:
        Tuple of (DatabaseManager, ServiceContainer) or (None, None) if not available
    """
    if not STREAMLIT_AVAILABLE:
        return None, None
    
    # Ensure services are initialized
    if not st.session_state.get("services_initialized", False):
        initialize_streamlit_session()
    
    db_manager = st.session_state.get("db_manager")
    service_container = st.session_state.get("service_container")
    
    return db_manager, service_container


def check_services_health() -> Dict[str, Any]:
    """
    Check the health of all application services.
    
    Returns:
        Health status dictionary
    """
    health_status = {
        "database": {"status": "unknown", "message": ""},
        "services": {"status": "unknown", "message": ""},
        "overall": {"status": "unknown", "healthy": False}
    }
    
    try:
        # Check database manager
        db_manager = get_database_manager()
        if db_manager:
            # Simple database test
            result = safe_streamlit_operation(
                lambda: db_manager.execute_query("SELECT 1"),
                default_return=None,
                operation_name="health_check_db"
            )
            if result:
                health_status["database"] = {"status": "healthy", "message": "Database accessible"}
            else:
                health_status["database"] = {"status": "error", "message": "Database query failed"}
        else:
            health_status["database"] = {"status": "error", "message": "Database manager not available"}
        
        # Check service container
        service_container = get_app_service_container()
        if service_container:
            # Get service health from container
            from ..services.service_container import check_service_health
            service_health = check_service_health()
            
            if service_health.get("overall_health") == "healthy":
                health_status["services"] = {"status": "healthy", "message": "All services operational"}
            else:
                health_status["services"] = {"status": "error", "message": service_health.get("error", "Service issues detected")}
        else:
            health_status["services"] = {"status": "error", "message": "Service container not available"}
        
        # Overall health
        db_healthy = health_status["database"]["status"] == "healthy"
        services_healthy = health_status["services"]["status"] == "healthy"
        
        if db_healthy and services_healthy:
            health_status["overall"] = {"status": "healthy", "healthy": True}
        else:
            health_status["overall"] = {"status": "degraded", "healthy": False}
            
    except Exception as e:
        health_status["overall"] = {"status": "error", "healthy": False, "error": str(e)}
        logger.error(f"Health check failed: {e}")
    
    return health_status


def cleanup_application():
    """
    Cleanup application resources.
    
    Should be called when the application is shutting down.
    """
    global _db_manager, _service_container
    
    try:
        # Shutdown service container
        if _service_container:
            shutdown_service_container()
            _service_container = None
        
        # Close database connections
        if _db_manager:
            # DatabaseManager cleanup would go here if implemented
            _db_manager = None
        
        # Clear session state if available
        if STREAMLIT_AVAILABLE and hasattr(st, 'session_state'):
            if "db_manager" in st.session_state:
                del st.session_state.db_manager
            if "service_container" in st.session_state:
                del st.session_state.service_container
            if "services_initialized" in st.session_state:
                del st.session_state.services_initialized
        
        logger.info("Application cleanup completed")
        
    except Exception as e:
        logger.error(f"Error during application cleanup: {e}")


def setup_application():
    """
    Complete application setup for Streamlit.
    
    This is the main entry point for application initialization.
    """
    if not STREAMLIT_AVAILABLE:
        logger.warning("Streamlit not available - skipping UI setup")
        return
    
    try:
        # Initialize logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Initialize session services
        initialize_streamlit_session()
        
        # Check if everything is working
        health = check_services_health()
        
        if not health["overall"]["healthy"]:
            st.error("⚠️ Application services not fully operational")
            with st.expander("🔍 Service Health Details"):
                st.json(health)
        else:
            logger.info("Application setup completed successfully")
            
    except Exception as e:
        logger.error(f"Application setup failed: {e}")
        if STREAMLIT_AVAILABLE:
            st.error(f"❌ Application setup failed: {e}")


# Convenience functions for accessing services
def get_client_service():
    """Get client service from the current session."""
    _, container = get_session_services()
    if container:
        return container.get_client_service()
    return None


def get_project_service():
    """Get project service from the current session."""
    _, container = get_session_services()
    if container:
        return container.get_project_service()
    return None


def get_epic_service():
    """Get epic service from the current session."""
    _, container = get_session_services()
    if container:
        return container.get_epic_service()
    return None


def get_task_service():
    """Get task service from the current session."""
    _, container = get_session_services()
    if container:
        return container.get_task_service()
    return None


def get_analytics_service():
    """Get analytics service from the current session."""
    _, container = get_session_services()
    if container:
        return container.get_analytics_service()
    return None


def get_timer_service():
    """Get timer service from the current session."""
    _, container = get_session_services()
    if container:
        return container.get_timer_service()
    return None


# Development and testing utilities
def reset_services(force: bool = False):
    """
    Reset all services (useful for development/testing).
    
    Args:
        force: If True, force reset even in production
    """
    if not force:
        logger.warning("Service reset requested - use force=True to confirm")
        return
    
    global _db_manager, _service_container
    
    logger.info("Resetting all application services")
    
    # Cleanup existing services
    cleanup_application()
    
    # Clear cache
    _db_manager = None
    _service_container = None
    
    # Re-initialize if in Streamlit context
    if STREAMLIT_AVAILABLE and hasattr(st, 'session_state'):
        st.session_state.services_initialized = False
        initialize_streamlit_session()


if __name__ == "__main__":
    # Test the setup utilities
    print("🧪 Testing application setup utilities...")
    
    # Test database manager
    db_manager = get_database_manager()
    print(f"Database manager: {'✅ OK' if db_manager else '❌ Failed'}")
    
    # Test service container
    container = get_app_service_container()
    print(f"Service container: {'✅ OK' if container else '❌ Failed'}")
    
    # Test health check
    health = check_services_health()
    print(f"Overall health: {'✅ Healthy' if health['overall']['healthy'] else '❌ Issues detected'}")
    
    # Cleanup
    cleanup_application()
    print("🧹 Cleanup completed")