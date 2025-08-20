"""
🔧 Streamlit Helpers

Consolidated utility functions and helpers for Streamlit applications.
This is now a facade module that imports from specialized modules.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)

# === IMPORTS FROM SPECIALIZED MODULES ======================================

# UI Operations
from .ui_operations import (
    is_ui,
    is_headless,
    safe_ui,
    safe_streamlit_write,
    safe_streamlit_error, 
    safe_streamlit_info,
    safe_streamlit_success,
    safe_streamlit_warning,
    set_page_config_once,
    create_columns,
    create_tabs,
    create_expander,
)

# Cache Management
from .cache_utils import (
    cache_data,
    cache_resource,
    clear_all_caches,
    clear_cache_by_function,
    is_debug_mode,
)

# Data Normalization
from .data_utils import (
    ensure_list,
    ensure_dict,
    safe_get,
    safe_int,
    safe_float, 
    safe_str,
)

# Project Path Helpers
from .path_utils import (
    get_project_root,
    add_project_to_path,
    get_relative_path,
)

# === SESSION STATE HELPERS ================================================

def get_session_state() -> Any:
    """
    Get Streamlit session state safely.
    
    Returns:
        Session state object or None if unavailable
    """
    if is_ui():
        try:
            import streamlit as st
            return st.session_state
        except ImportError:
            return None
    return None

def session_get(key: str, default: Any = None) -> Any:
    """
    Get value from session state safely.
    
    Args:
        key: Session state key
        default: Default value if key not found
        
    Returns:
        Value from session state or default
    """
    session_state = get_session_state()
    if session_state is not None:
        return session_state.get(key, default)
    return default

def session_set(key: str, value: Any) -> None:
    """
    Set value in session state safely.
    
    Args:
        key: Session state key
        value: Value to set
    """
    session_state = get_session_state()
    if session_state is not None:
        session_state[key] = value

# === HEALTH CHECK =========================================================

def check_streamlit_helpers_health() -> Dict[str, Any]:
    """Check health of Streamlit helpers."""
    return {
        "streamlit_available": is_ui(),
        "ui_available": is_ui(),
        "headless_mode": is_headless(),
        "project_root": str(get_project_root()),
        "debug_mode": is_debug_mode(),
        "session_state_available": get_session_state() is not None,
        "cache_available": is_ui(),
        "status": "healthy" if is_ui() else "degraded"
    }

# === EXPORTS ==============================================================

__all__ = [
    # Availability checks (from ui_operations)
    "is_ui",
    "is_headless",
    
    # Safe UI operations (from ui_operations)
    "safe_ui",
    "safe_streamlit_write",
    "safe_streamlit_error", 
    "safe_streamlit_info",
    "safe_streamlit_success",
    "safe_streamlit_warning",
    
    # Page configuration (from ui_operations)
    "set_page_config_once",
    
    # UI layout helpers (from ui_operations)
    "create_columns",
    "create_tabs",
    "create_expander",
    
    # Cache management (from cache_utils)
    "cache_data",
    "cache_resource",
    "clear_all_caches",
    "clear_cache_by_function",
    "is_debug_mode",
    
    # Data normalization (from data_utils)
    "ensure_list",
    "ensure_dict",
    "safe_get",
    "safe_int",
    "safe_float", 
    "safe_str",
    
    # Project path helpers (from path_utils)
    "get_project_root",
    "add_project_to_path",
    "get_relative_path",
    
    # Session state helpers (local)
    "get_session_state",
    "session_get",
    "session_set",
    
    # Health check (local)
    "check_streamlit_helpers_health",
]