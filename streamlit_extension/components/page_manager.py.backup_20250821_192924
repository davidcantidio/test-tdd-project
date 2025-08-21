"""
🗂️ Page Manager

Page routing and content management for the application.
Handles navigation between different pages and dashboard content rendering.
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

# Component imports with fallbacks
try:
    from .analytics_cards import render_analytics_cards
    ANALYTICS_CARDS_AVAILABLE = True
except ImportError:
    ANALYTICS_CARDS_AVAILABLE = False
    def render_analytics_cards(stats=None):
        if STREAMLIT_AVAILABLE:
            st.info("📊 Analytics temporarily unavailable")

try:
    from .layout_renderers import render_heatmap_and_tasks, render_timer_and_notifications
    LAYOUT_RENDERERS_AVAILABLE = True
except ImportError:
    LAYOUT_RENDERERS_AVAILABLE = False
    def render_heatmap_and_tasks(epics, selected_epic_id):
        if STREAMLIT_AVAILABLE:
            st.info("📊 Heatmap and tasks temporarily unavailable")
    def render_timer_and_notifications():
        if STREAMLIT_AVAILABLE:
            st.info("⏱️ Timer and notifications temporarily unavailable")

# Data providers
try:
    from .data_providers import fetch_user_stats, fetch_epics
    DATA_PROVIDERS_AVAILABLE = True
except ImportError:
    DATA_PROVIDERS_AVAILABLE = False
    def fetch_user_stats(user_id=None):
        return {}
    def fetch_epics():
        return []

# Navigation system
try:
    from ..pages import render_page, get_available_pages, PAGE_REGISTRY
    PAGES_AVAILABLE = True
except ImportError:
    PAGES_AVAILABLE = False
    def render_page(page_id: str):
        return {"error": f"Page system not available"}
    def get_available_pages():
        return {}

# Exception handling
try:
    from ..utils.exception_handler import streamlit_error_boundary
    EXCEPTION_HANDLER_AVAILABLE = True
except ImportError:
    EXCEPTION_HANDLER_AVAILABLE = False
    
    class streamlit_error_boundary:
        def __init__(self, operation_name: str):
            self.name = operation_name
        def __enter__(self): 
            return self
        def __exit__(self, exc_type, exc, tb): 
            return False

# Session manager
try:
    from ..utils.session_manager import (
        get_session_value,
        set_session_value,
        get_selected_epic_id,
        set_current_page,
        get_current_page,
        initialize_page_state
    )
    SESSION_MANAGER_AVAILABLE = True
except ImportError:
    SESSION_MANAGER_AVAILABLE = False
    # All session functions removed - import from session_manager instead

logger = logging.getLogger(__name__)

# === PAGE ROUTING =============================================================

def render_current_page(user: Dict[str, Any]) -> None:
    """
    Render the current page based on session state navigation.
    
    Args:
        user: Current authenticated user information
    """
    if not STREAMLIT_AVAILABLE:
        return
    
    try:
        current_page = get_current_page()
        
        if current_page == "Dashboard":
            # Render default dashboard
            render_dashboard_content(user)
        elif PAGES_AVAILABLE:
            # Use the pages system for CRUD pages
            _render_pages_system_page(current_page)
        else:
            # Fallback for unknown pages
            _render_page_not_found(current_page)
    
    except Exception as e:
        logger.error(f"Error rendering current page: {e}")
        if STREAMLIT_AVAILABLE:
            st.error("⚠️ Page rendering temporarily unavailable")
            _render_return_to_dashboard()

def _render_pages_system_page(current_page: str) -> None:
    """
    Render a page using the pages system.
    
    Args:
        current_page: Name of the page to render
    """
    page_id = current_page.lower()  # Convert "Clients" -> "clients"
    
    with streamlit_error_boundary(f"render_page_{page_id}"):
        page_result = render_page(page_id)
        
        if isinstance(page_result, dict) and "error" in page_result:
            st.error(f"❌ Error loading {current_page}: {page_result['error']}")
            st.info("Returning to Dashboard...")
            set_current_page("Dashboard")
            if st.button("🔄 Return to Dashboard"):
                st.rerun()

def _render_page_not_found(current_page: str) -> None:
    """
    Render page not found error.
    
    Args:
        current_page: Name of the page that was not found
    """
    st.error(f"❌ Page '{current_page}' is not available")
    st.info("Available pages: Dashboard")
    if st.button("🏠 Return to Dashboard"):
        set_current_page("Dashboard")
        st.rerun()

def _render_return_to_dashboard() -> None:
    """Render a return to dashboard button."""
    if st.button("🏠 Return to Dashboard"):
        set_current_page("Dashboard")
        st.rerun()

# === DASHBOARD CONTENT ========================================================

def render_dashboard_content(user: Dict[str, Any]) -> None:
    """
    Render the default dashboard content.
    
    Args:
        user: Current authenticated user information
    """
    if not STREAMLIT_AVAILABLE:
        return
    
    try:
        # Analytics row
        with streamlit_error_boundary("analytics_row"):
            _render_analytics_section(user)

        # Heatmap and tasks row
        with streamlit_error_boundary("heatmap_tasks"):
            _render_heatmap_tasks_section()

        # Timer and notifications row
        with streamlit_error_boundary("timer_notifications"):
            render_timer_and_notifications()
    
    except Exception as e:
        logger.error(f"Error rendering dashboard content: {e}")
        if STREAMLIT_AVAILABLE:
            st.error("⚠️ Dashboard content temporarily unavailable")

def _render_analytics_section(user: Dict[str, Any]) -> None:
    """
    Render the analytics cards section.
    
    Args:
        user: Current authenticated user information
    """
    stats = fetch_user_stats(user.get("id") if isinstance(user, dict) else None)
    render_analytics_cards(stats or {})

def _render_heatmap_tasks_section() -> None:
    """Render the heatmap and tasks section."""
    epics = fetch_epics()
    selected_epic_id = get_selected_epic_id()
    render_heatmap_and_tasks(epics, selected_epic_id)

# === PAGE NAVIGATION HELPERS ==================================================
# set_current_page and get_current_page are imported from session_manager

def navigate_to_page(page_name: str, rerun: bool = True) -> None:
    """
    Navigate to a specific page.
    
    Args:
        page_name: Name of the page to navigate to
        rerun: Whether to trigger a Streamlit rerun
    """
    if not STREAMLIT_AVAILABLE:
        return
    
    set_current_page(page_name)
    if rerun:
        st.rerun()

def get_available_page_names() -> List[str]:
    """
    Get list of available page names.
    
    Returns:
        List of available page names
    """
    if PAGES_AVAILABLE:
        try:
            available_pages = get_available_pages()
            page_names = list(available_pages.keys())
            # Add Dashboard if not already included
            if "Dashboard" not in page_names:
                page_names.insert(0, "Dashboard")
            return page_names
        except Exception as e:
            logger.warning(f"Error getting available pages: {e}")
    
    return ["Dashboard"]

# === PAGE STATE MANAGEMENT ====================================================

# initialize_page_state() removed - imported from session_manager

def add_to_page_history(page_name: str) -> None:
    """
    Add a page to navigation history.
    
    Args:
        page_name: Name of the page to add to history
    """
    if not STREAMLIT_AVAILABLE:
        return
    
    history = get_session_value("page_history", [])
    
    # Remove if already in history
    if page_name in history:
        history.remove(page_name)
    
    # Add to front
    history.insert(0, page_name)
    
    # Keep only last 10 pages
    set_session_value("page_history", history[:10])

def get_page_history() -> List[str]:
    """
    Get page navigation history.
    
    Returns:
        List of page names in navigation history
    """
    return get_session_value("page_history", [])

def go_back() -> None:
    """Navigate to the previous page in history."""
    if not STREAMLIT_AVAILABLE:
        return
    
    history = get_page_history()
    if len(history) > 1:
        previous_page = history[1]
        navigate_to_page(previous_page)

# === BREADCRUMB NAVIGATION ====================================================

def render_breadcrumb_navigation() -> None:
    """Render breadcrumb navigation based on current page."""
    if not STREAMLIT_AVAILABLE:
        return
    
    try:
        current_page = get_current_page()
        
        # Build breadcrumb trail
        breadcrumbs = ["🏠 Home"]
        if current_page != "Dashboard":
            breadcrumbs.append(f"📄 {current_page}")
        
        # Render breadcrumbs
        breadcrumb_text = " → ".join(breadcrumbs)
        st.caption(breadcrumb_text)
        
    except Exception as e:
        logger.warning(f"Error rendering breadcrumbs: {e}")

# === PAGE MANAGER HEALTH CHECK ================================================

def check_page_manager_health() -> Dict[str, Any]:
    """Check health of page manager dependencies."""
    return {
        "streamlit_available": STREAMLIT_AVAILABLE,
        "analytics_cards_available": ANALYTICS_CARDS_AVAILABLE,
        "layout_renderers_available": LAYOUT_RENDERERS_AVAILABLE,
        "data_providers_available": DATA_PROVIDERS_AVAILABLE,
        "pages_available": PAGES_AVAILABLE,
        "exception_handler_available": EXCEPTION_HANDLER_AVAILABLE,
        "available_pages": get_available_page_names(),
        "current_page": get_current_page(),
        "status": "healthy" if all([
            STREAMLIT_AVAILABLE,
            ANALYTICS_CARDS_AVAILABLE,
            LAYOUT_RENDERERS_AVAILABLE,
            DATA_PROVIDERS_AVAILABLE
        ]) else "degraded"
    }

# === EXPORTS ==================================================================

__all__ = [
    # Page routing
    "render_current_page",
    "render_dashboard_content",
    
    # Navigation helpers
    "set_current_page",
    "get_current_page", 
    "navigate_to_page",
    "get_available_page_names",
    
    # Page state management
    "initialize_page_state",
    "add_to_page_history",
    "get_page_history",
    "go_back",
    
    # UI helpers
    "render_breadcrumb_navigation",
    
    # Health check
    "check_page_manager_health",
]