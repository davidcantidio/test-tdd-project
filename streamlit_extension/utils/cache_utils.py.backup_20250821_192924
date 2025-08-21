"""
🗄️ Cache Management Utilities

Streamlit cache decorators and cache management operations.
Extracted from streamlit_helpers.py for better modularity.
"""

from __future__ import annotations

from typing import Any, Callable
import logging

logger = logging.getLogger(__name__)

# === STREAMLIT AVAILABILITY CHECK ===========================================

# SEMANTIC DEDUPLICATION: Import from ui_operations instead of duplicate implementation
from .ui_operations import is_ui

# Safe streamlit import (still needed for other functions)
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False
    st = None

# === CACHE MANAGEMENT =======================================================

def cache_data(*dargs, **dkwargs):
    """
    Cache data decorator with Streamlit integration.
    
    Args:
        *dargs: Decorator arguments
        **dkwargs: Decorator keyword arguments
        
    Returns:
        Cache decorator or passthrough decorator
    """
    if is_ui() and hasattr(st, "cache_data"):
        return st.cache_data(*dargs, **dkwargs)
    
    # Passthrough decorator for non-UI environments
    def deco(fn):
        return fn
    return deco

def cache_resource(*dargs, **dkwargs):
    """
    Cache resource decorator with Streamlit integration.
    
    Args:
        *dargs: Decorator arguments
        **dkwargs: Decorator keyword arguments
        
    Returns:
        Cache decorator or passthrough decorator
    """
    if is_ui() and hasattr(st, "cache_resource"):
        return st.cache_resource(*dargs, **dkwargs)
    
    # Passthrough decorator for non-UI environments
    def deco(fn):
        return fn
    return deco

def clear_all_caches() -> None:
    """Clear all Streamlit caches."""
    if not is_ui():
        return
    
    try:
        if hasattr(st, "cache_data"):
            st.cache_data.clear()
        if hasattr(st, "cache_resource"):
            st.cache_resource.clear()
        
        logger.info("All caches cleared")
        
        # Show debug message if in debug mode
        if is_debug_mode():
            print("🧹 caches limpos")
    
    except Exception as e:
        logger.warning(f"Error clearing caches: {e}")

def clear_cache_by_function(func: Callable) -> None:
    """
    Clear cache for a specific function.
    
    Args:
        func: Function whose cache to clear
    """
    if not is_ui():
        return
    
    try:
        if hasattr(func, "clear"):
            func.clear()
            logger.info(f"Cache cleared for function: {func.__name__}")
        else:
            logger.warning(f"Function {func.__name__} does not have cache to clear")
    
    except Exception as e:
        logger.warning(f"Error clearing cache for {func.__name__}: {e}")

def is_debug_mode() -> bool:
    """
    Check if debug mode is enabled.
    
    Returns:
        True if debug mode enabled, False otherwise
    """
    # Import session_manager to avoid circular imports
    try:
        from .session_manager import get_session_value
        config = get_session_value("config")
        if config and hasattr(config, "debug_mode"):
            return bool(config.debug_mode)
        return get_session_value("show_debug_info", False)
    except ImportError:
        return False

# === EXPORTS ==============================================================

__all__ = [
    # Cache management
    "cache_data",
    "cache_resource", 
    "clear_all_caches",
    "clear_cache_by_function",
    
    # Debug utilities
    "is_debug_mode",
]