"""
🎨 UI Operations

Streamlit UI availability checks and safe UI operations.
Extracted from streamlit_helpers.py for better modularity.
"""

from __future__ import annotations

from typing import Any, Callable, List
import logging

logger = logging.getLogger(__name__)

# === STREAMLIT AVAILABILITY CHECK ===========================================

# Safe streamlit import
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False
    st = None

def is_ui() -> bool:
    """
    Check if Streamlit UI is available and operational.
    
    Returns:
        True if Streamlit is available, False otherwise
    """
    return STREAMLIT_AVAILABLE and st is not None

def is_headless() -> bool:
    """
    Check if running in headless mode (without Streamlit UI).
    
    Returns:
        True if headless, False if UI available
    """
    return not is_ui()

# === SAFE UI OPERATIONS =====================================================

def safe_ui(fn: Callable[..., Any], *args, **kwargs) -> Any:
    """
    Execute a UI operation safely, with error handling.
    
    Args:
        fn: Function to execute
        *args: Function arguments
        **kwargs: Function keyword arguments
        
    Returns:
        Function result or None if error/unavailable
    """
    if not is_ui():
        return None
    
    try:
        return fn(*args, **kwargs)
    except Exception as e:
        # Avoid crashing the page on UI errors
        logger.warning(f"UI error in {getattr(fn, '__name__', 'unknown')}: {e}")
        return None

def safe_streamlit_write(content: Any, container: Any = None) -> None:
    """
    Safely write content to Streamlit.
    
    Args:
        content: Content to write
        container: Optional container to write to
    """
    def _write():
        if container:
            container.write(content)
        else:
            st.write(content)
    
    safe_ui(_write)

def safe_streamlit_error(message: str, container: Any = None) -> None:
    """
    Safely display error message in Streamlit.
    
    Args:
        message: Error message to display
        container: Optional container to write to
    """
    def _error():
        if container:
            container.error(message)
        else:
            st.error(message)
    
    safe_ui(_error)

def safe_streamlit_info(message: str, container: Any = None) -> None:
    """
    Safely display info message in Streamlit.
    
    Args:
        message: Info message to display
        container: Optional container to write to
    """
    def _info():
        if container:
            container.info(message)
        else:
            st.info(message)
    
    safe_ui(_info)

def safe_streamlit_success(message: str, container: Any = None) -> None:
    """
    Safely display success message in Streamlit.
    
    Args:
        message: Success message to display
        container: Optional container to write to
    """
    def _success():
        if container:
            container.success(message)
        else:
            st.success(message)
    
    safe_ui(_success)

def safe_streamlit_warning(message: str, container: Any = None) -> None:
    """
    Safely display warning message in Streamlit.
    
    Args:
        message: Warning message to display
        container: Optional container to write to
    """
    def _warning():
        if container:
            container.warning(message)
        else:
            st.warning(message)
    
    safe_ui(_warning)

# === PAGE CONFIGURATION ====================================================

def set_page_config_once(**config_kwargs) -> None:
    """
    Set Streamlit page configuration safely (only once).
    
    Args:
        **config_kwargs: Configuration parameters for st.set_page_config
    """
    if not is_ui():
        return
    
    try:
        # Default configuration
        default_config = {
            "page_title": "TDD Framework Dashboard",
            "page_icon": "🚀",
            "layout": "wide",
            "initial_sidebar_state": "expanded",
            "menu_items": {
                "Report a bug": "https://github.com/davidcantidio/test-tdd-project/issues",
                "About": """
                # TDD Framework - Advanced Dashboard
                - ⏱️ Timer com suporte a TDAH
                - 📋 Kanban de tarefas
                - 📊 Analytics e produtividade
                - 🎮 Gamification
                - 🐙 Integração GitHub
                **Version:** 1.3.3
                """,
            },
        }
        
        # Merge with provided config
        final_config = {**default_config, **config_kwargs}
        
        st.set_page_config(**final_config)
        
    except Exception:
        # Already configured in rerun or conflicts
        pass

# === UI LAYOUT HELPERS ====================================================

def create_columns(ratios: List[float]) -> List[Any]:
    """
    Create Streamlit columns with specified ratios.
    
    Args:
        ratios: List of column width ratios
        
    Returns:
        List of column objects or empty list if unavailable
    """
    if not is_ui():
        return []
    
    try:
        return list(st.columns(ratios))
    except Exception as e:
        logger.error(f"Error creating columns: {e}")
        return []

def create_tabs(tab_names: List[str]) -> List[Any]:
    """
    Create Streamlit tabs with specified names.
    
    Args:
        tab_names: List of tab names
        
    Returns:
        List of tab objects or empty list if unavailable
    """
    if not is_ui():
        return []
    
    try:
        return list(st.tabs(tab_names))
    except Exception as e:
        logger.error(f"Error creating tabs: {e}")
        return []

def create_expander(title: str, expanded: bool = False) -> Any:
    """
    Create Streamlit expander safely.
    
    Args:
        title: Expander title
        expanded: Whether to start expanded
        
    Returns:
        Expander object or None if unavailable
    """
    if not is_ui():
        return None
    
    try:
        return st.expander(title, expanded=expanded)
    except Exception as e:
        logger.error(f"Error creating expander: {e}")
        return None

# === EXPORTS ==============================================================

__all__ = [
    # Availability checks
    "is_ui",
    "is_headless",
    
    # Safe UI operations
    "safe_ui",
    "safe_streamlit_write",
    "safe_streamlit_error", 
    "safe_streamlit_info",
    "safe_streamlit_success",
    "safe_streamlit_warning",
    
    # Page configuration
    "set_page_config_once",
    
    # UI layout helpers
    "create_columns",
    "create_tabs",
    "create_expander",
]