"""
🛠️ Debug Widgets

Debug and development tools for the application.
Provides telemetry, error statistics, and development utilities.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import logging
import traceback
from datetime import datetime

# Safe streamlit import
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False
    st = None

# Exception handling
try:
    from ..utils.exception_handler import get_error_statistics, safe_streamlit_operation
    EXCEPTION_HANDLER_AVAILABLE = True
except ImportError:
    EXCEPTION_HANDLER_AVAILABLE = False
    def get_error_statistics() -> Dict[str, Any]:
        return {"total_errors": 0, "error_types": {}}
    def safe_streamlit_operation(func, *args, default_return=None, operation_name=None, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception:
            return default_return

# Session manager
try:
    from ..utils.session_manager import (
        get_session_state_summary, 
        validate_session_state,
        get_session_value,
        set_session_value,
        clear_all_session_state
    )
    SESSION_MANAGER_AVAILABLE = True
except ImportError:
    SESSION_MANAGER_AVAILABLE = False
    def get_session_state_summary():
        return {"status": "unavailable"}
    def validate_session_state():
        return {"valid": False, "issues": ["session_manager not available"]}
    # get_session_value, set_session_value, clear_all_session_state removed - import from session_manager

# Data providers health
try:
    from ..components.data_providers import check_data_provider_health
    DATA_PROVIDERS_HEALTH_AVAILABLE = True
except ImportError:
    DATA_PROVIDERS_HEALTH_AVAILABLE = False
    def check_data_provider_health():
        return {"status": "unavailable"}

# Service container health
try:
    from ..services.service_container import check_service_health
    SERVICE_HEALTH_AVAILABLE = True
except ImportError:
    SERVICE_HEALTH_AVAILABLE = False
    def check_service_health():
        return {"overall_health": "unavailable"}

logger = logging.getLogger(__name__)

# === DEBUG PANEL COMPONENTS ===================================================

def render_debug_panel() -> None:
    """
    Render comprehensive debug panel with telemetry and system information.
    This is an expanded version of the original render_debug_panel from streamlit_app.py
    """
    if not STREAMLIT_AVAILABLE:
        return

    try:
        with st.expander("🛠️ Debug / Telemetria", expanded=False):
            # Basic debug tabs
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "🏥 Health", 
                "📊 Session", 
                "❌ Errors", 
                "🔧 System", 
                "📋 Raw Data"
            ])
            
            with tab1:
                _render_health_debug()
            
            with tab2:
                _render_session_debug()
            
            with tab3:
                _render_error_debug()
            
            with tab4:
                _render_system_debug()
            
            with tab5:
                _render_raw_data_debug()

    except Exception as e:
        logger.error(f"Error rendering debug panel: {e}")
        if STREAMLIT_AVAILABLE:
            st.error(f"⚠️ Debug panel error: {str(e)}")

def _render_health_debug() -> None:
    """Render health status debugging information."""
    st.markdown("#### 🏥 System Health")
    
    # Overall health status
    health = get_session_value("health", {})
    
    if health:
        overall = health.get("overall", {})
        status = overall.get("status", "unknown")
        healthy = overall.get("healthy", False)
        
        status_emoji = "🟢" if healthy else "🔴"
        st.metric("Overall Status", f"{status_emoji} {status.title()}")
        
        # Component health
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Database:**")
            db_health = health.get("database", {})
            db_status = db_health.get("status", "unknown")
            st.write(f"Status: {db_status}")
            
        with col2:
            st.markdown("**Services:**")
            svc_health = health.get("services", {})
            svc_status = svc_health.get("status", "unknown")
            st.write(f"Status: {svc_status}")
    else:
        st.warning("No health data available")

    # Module health checks
    st.markdown("#### 🔧 Module Health")
    
    if DATA_PROVIDERS_HEALTH_AVAILABLE:
        dp_health = check_data_provider_health()
        st.json(dp_health)
    
    if SERVICE_HEALTH_AVAILABLE:
        svc_health = check_service_health()
        st.json(svc_health)

def _render_session_debug() -> None:
    """Render session state debugging information."""
    st.markdown("#### 📊 Session State")
    
    if SESSION_MANAGER_AVAILABLE:
        # Session summary
        summary = get_session_state_summary()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Keys", summary.get("key_count", 0))
        with col2:
            st.metric("Services Ready", "✅" if summary.get("services_ready") else "❌")
        with col3:
            st.metric("User Logged In", "✅" if summary.get("user_logged_in") else "❌")
        
        # Session validation
        st.markdown("**Session Validation:**")
        validation = validate_session_state()
        
        if validation.get("valid"):
            st.success("✅ Session state is valid")
        else:
            st.error("❌ Session state has issues")
            issues = validation.get("issues", [])
            for issue in issues:
                st.write(f"• {issue}")
        
        # Key details
        with st.expander("Session Keys Details"):
            keys = summary.get("keys", [])
            for key in sorted(keys):
                value = get_session_value(key)
                value_type = type(value).__name__
                st.write(f"**{key}**: {value_type}")

def _render_error_debug() -> None:
    """Render error debugging information."""
    st.markdown("#### ❌ Error Statistics")
    
    if EXCEPTION_HANDLER_AVAILABLE:
        error_stats = safe_streamlit_operation(get_error_statistics, default_return={})
        
        if error_stats:
            total_errors = error_stats.get("total_errors", 0)
            st.metric("Total Errors", total_errors)
            
            error_types = error_stats.get("error_types", {})
            if error_types:
                st.markdown("**Error Types:**")
                for error_type, count in error_types.items():
                    st.write(f"• {error_type}: {count}")
            
            # Recent errors
            recent_errors = error_stats.get("recent_errors", [])
            if recent_errors:
                with st.expander("Recent Errors"):
                    for i, error in enumerate(recent_errors[-5:], 1):
                        st.write(f"**Error {i}:**")
                        st.code(error.get("message", "No message"))
                        st.caption(f"Time: {error.get('timestamp', 'Unknown')}")
        else:
            st.info("No error statistics available")
    else:
        st.warning("Exception handler not available")

def _render_system_debug() -> None:
    """Render system debugging information."""
    st.markdown("#### 🔧 System Information")
    
    # Python and environment info
    import sys
    import platform
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Python:**")
        st.write(f"Version: {sys.version}")
        st.write(f"Platform: {platform.system()}")
        
    with col2:
        st.markdown("**Streamlit:**")
        if STREAMLIT_AVAILABLE:
            st.write(f"Available: ✅")
            try:
                st.write(f"Version: {st.__version__}")
            except:
                st.write("Version: Unknown")
        else:
            st.write("Available: ❌")
    
    # Memory usage (if available)
    try:
        import psutil
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        st.metric("Memory Usage", f"{memory_mb:.1f} MB")
    except ImportError:
        st.info("Memory info unavailable (psutil not installed)")

def _render_raw_data_debug() -> None:
    """Render raw data for advanced debugging."""
    st.markdown("#### 📋 Raw Debug Data")
    
    debug_data = {
        "health": get_session_value("health"),
        "error_stats": safe_streamlit_operation(get_error_statistics, default_return={}),
        "timestamp": datetime.now().isoformat(),
        "session_summary": get_session_state_summary() if SESSION_MANAGER_AVAILABLE else {}
    }
    
    st.json(debug_data)

# === PERFORMANCE MONITORING ===================================================

def render_performance_metrics() -> None:
    """Render performance monitoring metrics."""
    if not STREAMLIT_AVAILABLE:
        return
    
    try:
        st.markdown("#### ⚡ Performance Metrics")
        
        # Cache statistics
        if hasattr(st, "cache_data"):
            with st.expander("Cache Information"):
                st.info("Cache data decorator is available")
                if st.button("Clear All Caches"):
                    st.cache_data.clear()
                    if hasattr(st, "cache_resource"):
                        st.cache_resource.clear()
                    st.success("Caches cleared!")
                    st.rerun()
        
        # Session state size estimation
        try:
            import sys
            session_size = sys.getsizeof(st.session_state)
            st.metric("Session State Size", f"{session_size} bytes")
        except:
            st.info("Session state size unavailable")
            
    except Exception as e:
        logger.error(f"Error rendering performance metrics: {e}")
        st.error("Performance metrics temporarily unavailable")

# === DEVELOPMENT UTILITIES ====================================================

def render_development_tools() -> None:
    """Render development tools and utilities."""
    if not STREAMLIT_AVAILABLE:
        return
    
    try:
        st.markdown("#### 🔨 Development Tools")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Reload Session"):
                clear_all_session_state()
                st.success("Session cleared! Page will reload.")
                st.rerun()
        
        with col2:
            if st.button("🧹 Clear Caches"):
                if hasattr(st, "cache_data"):
                    st.cache_data.clear()
                if hasattr(st, "cache_resource"):
                    st.cache_resource.clear()
                st.success("Caches cleared!")
        
        # Debug toggles
        debug_mode = get_session_value("show_debug_info", False)
        new_debug_mode = st.checkbox("Enable Debug Mode", value=debug_mode)
        if new_debug_mode != debug_mode:
            set_session_value("show_debug_info", new_debug_mode)
            st.rerun()
            
    except Exception as e:
        logger.error(f"Error rendering development tools: {e}")
        st.error("Development tools temporarily unavailable")

def render_log_viewer() -> None:
    """Render log viewer for recent application logs."""
    if not STREAMLIT_AVAILABLE:
        return
    
    try:
        st.markdown("#### 📝 Log Viewer")
        
        # This is a placeholder for log viewing functionality
        # In a full implementation, you would read from log files or log handlers
        
        st.info("Log viewer functionality can be implemented to show:")
        st.write("• Recent application logs")
        st.write("• Filtered log levels")
        st.write("• Search functionality")
        st.write("• Export capabilities")
        
    except Exception as e:
        logger.error(f"Error rendering log viewer: {e}")
        st.error("Log viewer temporarily unavailable")

# === COMPREHENSIVE DEBUG DASHBOARD ============================================

def render_full_debug_dashboard() -> None:
    """Render comprehensive debug dashboard with all tools."""
    if not STREAMLIT_AVAILABLE:
        return
    
    try:
        st.markdown("## 🛠️ Debug Dashboard")
        
        # Main debug sections
        render_debug_panel()
        
        st.markdown("---")
        
        # Performance section
        render_performance_metrics()
        
        st.markdown("---")
        
        # Development tools
        render_development_tools()
        
        st.markdown("---")
        
        # Log viewer
        render_log_viewer()
        
    except Exception as e:
        logger.error(f"Error rendering full debug dashboard: {e}")
        if STREAMLIT_AVAILABLE:
            st.error("Debug dashboard partially unavailable")

# === DEBUG WIDGET HEALTH CHECK ================================================

def check_debug_widgets_health() -> Dict[str, Any]:
    """Check health of debug widgets dependencies."""
    return {
        "streamlit_available": STREAMLIT_AVAILABLE,
        "exception_handler_available": EXCEPTION_HANDLER_AVAILABLE,
        "session_manager_available": SESSION_MANAGER_AVAILABLE,
        "data_providers_health_available": DATA_PROVIDERS_HEALTH_AVAILABLE,
        "service_health_available": SERVICE_HEALTH_AVAILABLE,
        "status": "healthy" if all([
            STREAMLIT_AVAILABLE,
            EXCEPTION_HANDLER_AVAILABLE,
            SESSION_MANAGER_AVAILABLE
        ]) else "degraded"
    }

# === EXPORTS ==================================================================

__all__ = [
    # Main debug components
    "render_debug_panel",
    "render_performance_metrics",
    "render_development_tools",
    "render_log_viewer",
    "render_full_debug_dashboard",
    
    # Health check
    "check_debug_widgets_health",
]