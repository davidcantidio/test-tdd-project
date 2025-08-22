"""
🗃️ Session Manager

Centralized session state management for the Streamlit application.
Handles initialization, configuration, and state management.
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

# Configuration
try:
    from ..config import load_config
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False
    def load_config() -> Any:
        # Simple object with expected attributes
        return type("Cfg", (), {"debug_mode": False, "app_name": "TDD Framework"})()

# App setup
try:
    from ..utils.app_setup import setup_application
    SETUP_AVAILABLE = True
except ImportError:
    SETUP_AVAILABLE = False
    def setup_application():
        return None

# Exception handling
try:
    from ..utils.exception_handler import (
        install_global_exception_handler, 
        handle_streamlit_exceptions,
        streamlit_error_boundary
    )
    EXCEPTION_HANDLER_AVAILABLE = True
except ImportError:
    EXCEPTION_HANDLER_AVAILABLE = False
    
    def install_global_exception_handler(): 
        return None
    
    def handle_streamlit_exceptions(show_error=True, attempt_recovery=True):
        def decorator(fn):
            return fn
        return decorator
    
    class streamlit_error_boundary:
        def __init__(self, operation_name: str):
            self.name = operation_name
        def __enter__(self): 
            return self
        def __exit__(self, exc_type, exc, tb): 
            return False

# Timer component
try:
    from ..components.timer import TimerComponent
    TIMER_AVAILABLE = True
except ImportError:
    TIMER_AVAILABLE = False
    class TimerComponent:
        def render(self):
            if STREAMLIT_AVAILABLE:
                st.info("⏱️ Timer indisponível (fallback).")

# Auth imports

# Data providers
try:
    from ..components.data_providers import fetch_epics, fetch_health
    DATA_PROVIDERS_AVAILABLE = True
except ImportError:
    DATA_PROVIDERS_AVAILABLE = False
    def fetch_epics():
        return []
    def fetch_health():
        return {"status": "unknown", "healthy": False}

# Page manager check (removed circular import)
PAGE_MANAGER_AVAILABLE = True  # Assuming page_manager is available

logger = logging.getLogger(__name__)

# === SESSION STATE INITIALIZATION ============================================

@handle_streamlit_exceptions(show_error=True, attempt_recovery=True)
def initialize_session_state() -> None:
    """
    Initialize all session state variables and application setup.
    This function replaces the initialize_session_state from streamlit_app.py
    """
    if not STREAMLIT_AVAILABLE:
        return

    try:
        # Exception handler setup
        _initialize_exception_handler()
        
        # Configuration setup
        _initialize_configuration()
        
        # Services and database setup
        _initialize_services()
        
        # Timer component setup
        _initialize_timer()
        
        # User preferences setup
        _initialize_user_preferences()
        
        # Navigation setup
        _initialize_navigation()
        
        # Epic selection setup
        _initialize_epic_selection()
        
        # Health status setup
        _initialize_health_status()
        
        logger.info("Session state initialized successfully")
        
    except Exception as e:
        logger.error(f"Error initializing session state: {e}")
        if STREAMLIT_AVAILABLE:
            st.error("⚠️ Session initialization partially failed")

def _initialize_exception_handler() -> None:
    """Initialize global exception handler."""
    if EXCEPTION_HANDLER_AVAILABLE and not st.session_state.get("exception_handler_installed"):
        install_global_exception_handler()
        st.session_state.exception_handler_installed = True

def _initialize_configuration() -> None:
    """Initialize application configuration."""
    if CONFIG_AVAILABLE and "config" not in st.session_state:
        with streamlit_error_boundary("load_config"):
            st.session_state.config = load_config()

def _initialize_services() -> None:
    """Initialize services and database."""
    if SETUP_AVAILABLE and not st.session_state.get("services_ready"):
        with streamlit_error_boundary("setup_application"):
            setup_application()
            st.session_state.services_ready = True

def _initialize_timer() -> None:
    """Initialize timer component."""
    if "timer" not in st.session_state:
        st.session_state.timer = TimerComponent()

def _initialize_user_preferences() -> None:
    """Initialize user preferences and debug settings."""
    if "show_debug_info" not in st.session_state:
        cfg = st.session_state.get("config", None)
        st.session_state.show_debug_info = bool(getattr(cfg, "debug_mode", False))

def _initialize_navigation() -> None:
    """Initialize navigation and page state."""
    initialize_page_state()

def _initialize_epic_selection() -> None:
    """Initialize epic selection with default values."""
    epics = fetch_epics() if DATA_PROVIDERS_AVAILABLE else []
    default_epic_id = None
    
    if epics and len(epics) > 0 and isinstance(epics[0], dict):
        default_epic_id = epics[0].get("id")
    
    st.session_state.setdefault("selected_epic_id", default_epic_id)

def _initialize_health_status() -> None:
    """Initialize health status monitoring."""
    if DATA_PROVIDERS_AVAILABLE:
        st.session_state["health"] = fetch_health()
    else:
        st.session_state["health"] = {"status": "unknown", "healthy": False}

# === SESSION STATE MANAGEMENT =================================================

def get_session_value(key: str, default: Any = None) -> Any:
    """
    Get a value from session state safely.
    
    Args:
        key: Session state key
        default: Default value if key doesn't exist
        
    Returns:
        Value from session state or default
    """
    if not STREAMLIT_AVAILABLE:
        return default
    
    return st.session_state.get(key, default)

def set_session_value(key: str, value: Any) -> None:
    """
    Set a value in session state safely.
    
    Args:
        key: Session state key
        value: Value to set
    """
    if STREAMLIT_AVAILABLE:
        st.session_state[key] = value

def clear_session_value(key: str) -> None:
    """
    Clear a specific session state value.
    
    Args:
        key: Session state key to clear
    """
    if STREAMLIT_AVAILABLE and key in st.session_state:
        del st.session_state[key]

def clear_all_session_state() -> None:
    """Clear all session state (use with caution)."""
    if STREAMLIT_AVAILABLE:
        st.session_state.clear()

def session_has_key(key: str) -> bool:
    """
    Check if session state has a specific key.
    
    Args:
        key: Key to check
        
    Returns:
        True if key exists, False otherwise
    """
    if not STREAMLIT_AVAILABLE:
        return False
    
    return key in st.session_state

# === CONFIGURATION HELPERS ====================================================

def get_config() -> Any:
    """Get the application configuration object."""
    return get_session_value("config")

def is_debug_mode() -> bool:
    """Check if debug mode is enabled."""
    config = get_config()
    if config:
        return bool(getattr(config, "debug_mode", False))
    return get_session_value("show_debug_info", False)

def get_app_name() -> str:
    """Get the application name from config."""
    config = get_config()
    if config:
        return getattr(config, "app_name", "TDD Framework")
    return "TDD Framework"

def toggle_debug_mode() -> None:
    """Toggle debug mode on/off."""
    current = is_debug_mode()
    set_session_value("show_debug_info", not current)

# === USER STATE HELPERS =======================================================

def get_current_user() -> Optional[Dict[str, Any]]:
    """Get current user from session state."""
    return get_session_value("current_user")

def set_current_user(user: Dict[str, Any]) -> None:
    """Set current user in session state."""
    set_session_value("current_user", user)

def clear_current_user() -> None:
    """Clear current user from session state."""
    clear_session_value("current_user")

def is_user_logged_in() -> bool:
    """Check if user is logged in."""
    user = get_current_user()
    return user is not None and isinstance(user, dict)

# === APPLICATION STATE HELPERS ================================================

def are_services_ready() -> bool:
    """Check if services are initialized and ready."""
    return get_session_value("services_ready", False)

def mark_services_ready() -> None:
    """Mark services as ready."""
    set_session_value("services_ready", True)

def get_selected_epic_id() -> Any:
    """Get currently selected epic ID."""
    return get_session_value("selected_epic_id")

def set_selected_epic_id(epic_id: Any) -> None:
    """Set selected epic ID."""
    set_session_value("selected_epic_id", epic_id)

def get_timer_component() -> Any:
    """Get timer component from session state."""
    return get_session_value("timer")

def get_health_status() -> Dict[str, Any]:
    """Get current health status."""
    return get_session_value("health", {"status": "unknown", "healthy": False})

def update_health_status(health: Dict[str, Any]) -> None:
    """Update health status in session state."""
    set_session_value("health", health)

def initialize_page_state() -> None:
    """Initialize page-related session state - CANONICAL IMPLEMENTATION."""
    if not STREAMLIT_AVAILABLE:
        return
    
    # Set default page if not exists
    if not get_session_value("current_page"):
        set_session_value("current_page", "Dashboard")
    
    # Initialize page history
    if not get_session_value("page_history"):
        set_session_value("page_history", ["Dashboard"])

def get_current_page() -> str:
    """Get the current page from session state."""
    return get_session_value("current_page", "Dashboard")

def set_current_page(page_name: str) -> None:
    """Set the current page in session state."""
    set_session_value("current_page", page_name)

# === SESSION STATE INSPECTION =================================================

def get_session_state_summary() -> Dict[str, Any]:
    """Get a summary of current session state."""
    if not STREAMLIT_AVAILABLE:
        return {"status": "streamlit_unavailable"}
    
    return {
        "keys": list(st.session_state.keys()),
        "key_count": len(st.session_state.keys()),
        "config_loaded": "config" in st.session_state,
        "services_ready": are_services_ready(),
        "user_logged_in": is_user_logged_in(),
        "debug_mode": is_debug_mode(),
        "current_page": get_session_value("current_page"),
        "exception_handler_installed": get_session_value("exception_handler_installed", False)
    }

def validate_session_state() -> Dict[str, Any]:
    """Validate session state integrity."""
    issues = []
    
    # Check required keys
    required_keys = ["config", "timer", "current_page"]
    for key in required_keys:
        if not session_has_key(key):
            issues.append(f"Missing required session key: {key}")
    
    # Check timer component
    timer = get_timer_component()
    if timer is None or not hasattr(timer, "render"):
        issues.append("Timer component not properly initialized")
    
    # Check configuration
    config = get_config()
    if config is None:
        issues.append("Configuration not loaded")
    
    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "issue_count": len(issues)
    }

# === SESSION MANAGER HEALTH CHECK ============================================

def check_session_manager_health() -> Dict[str, Any]:
    """Check health of session manager dependencies."""
    return {
        "streamlit_available": STREAMLIT_AVAILABLE,
        "config_available": CONFIG_AVAILABLE,
        "setup_available": SETUP_AVAILABLE,
        "exception_handler_available": EXCEPTION_HANDLER_AVAILABLE,
        "timer_available": TIMER_AVAILABLE,
        "data_providers_available": DATA_PROVIDERS_AVAILABLE,
        "page_manager_available": PAGE_MANAGER_AVAILABLE,
        "session_state_summary": get_session_state_summary(),
        "session_validation": validate_session_state(),
        "status": "healthy" if all([
            STREAMLIT_AVAILABLE,
            CONFIG_AVAILABLE,
            SETUP_AVAILABLE
        ]) else "degraded"
    }

# === EXPORTS ==================================================================

__all__ = [
    # Main initialization
    "initialize_session_state",
    
    # Session state management
    "get_session_value",
    "set_session_value", 
    "clear_session_value",
    "clear_all_session_state",
    "session_has_key",
    
    # Configuration helpers
    "get_config",
    "is_debug_mode",
    "get_app_name",
    "toggle_debug_mode",
    
    # User state helpers
    "get_current_user",
    "set_current_user",
    "clear_current_user", 
    "is_user_logged_in",
    
    # Application state helpers
    "are_services_ready",
    "mark_services_ready",
    "get_selected_epic_id",
    "set_selected_epic_id",
    "get_timer_component",
    "get_health_status",
    "update_health_status",
    "initialize_page_state",
    "get_current_page",
    "set_current_page",
    
    # Session state inspection
    "get_session_state_summary",
    "validate_session_state",
    
    # Health check
    "check_session_manager_health",
]