#!/usr/bin/env python3
"""
🗂️ Page Manager

Page routing and content management for the application.
Handles navigation between different pages and dashboard content rendering.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Safe Streamlit import
# ──────────────────────────────────────────────────────────────────────────────
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:  # pragma: no cover - ambiente sem Streamlit
    STREAMLIT_AVAILABLE = False
    st = None  # type: ignore

# ──────────────────────────────────────────────────────────────────────────────
# Optional component imports (with graceful fallbacks)
# ──────────────────────────────────────────────────────────────────────────────
try:
    from .analytics_cards import render_analytics_cards
    ANALYTICS_CARDS_AVAILABLE = True
except ImportError:
    ANALYTICS_CARDS_AVAILABLE = False

    def render_analytics_cards(stats: Optional[Dict[str, Any]] = None) -> None:
        if STREAMLIT_AVAILABLE:
            st.info("📊 Analytics temporarily unavailable")

try:
    from .layout_renderers import render_heatmap_and_tasks, render_timer_and_notifications
    LAYOUT_RENDERERS_AVAILABLE = True
except ImportError:
    LAYOUT_RENDERERS_AVAILABLE = False

    def render_heatmap_and_tasks(epics: List[Dict[str, Any]], selected_epic_id: Optional[int]) -> None:
        if STREAMLIT_AVAILABLE:
            st.info("📊 Heatmap and tasks temporarily unavailable")

    def render_timer_and_notifications() -> None:
        if STREAMLIT_AVAILABLE:
            st.info("⏱️ Timer and notifications temporarily unavailable")

# ──────────────────────────────────────────────────────────────────────────────
# Data providers
# ──────────────────────────────────────────────────────────────────────────────
try:
    from .data_providers import fetch_user_stats, fetch_epics
    DATA_PROVIDERS_AVAILABLE = True
except ImportError:
    DATA_PROVIDERS_AVAILABLE = False

    def fetch_user_stats(user_id: Optional[int] = None) -> Dict[str, Any]:
        return {}

    def fetch_epics() -> List[Dict[str, Any]]:
        return []

# ──────────────────────────────────────────────────────────────────────────────
# Pages system
# ──────────────────────────────────────────────────────────────────────────────
try:
    from ..pages import render_page, get_available_pages
    PAGES_AVAILABLE = True
except ImportError:
    PAGES_AVAILABLE = False

    def render_page(page_id: str) -> Dict[str, Any]:
        return {"error": "Page system not available"}

    def get_available_pages() -> Dict[str, Any]:
        return {}

# ──────────────────────────────────────────────────────────────────────────────
# Exception handling boundary
# ──────────────────────────────────────────────────────────────────────────────
try:
    from ..utils.exception_handler import streamlit_error_boundary
    EXCEPTION_HANDLER_AVAILABLE = True
except ImportError:
    EXCEPTION_HANDLER_AVAILABLE = False

    class streamlit_error_boundary:  # type: ignore
        def __init__(self, operation_name: str) -> None:
            self.name = operation_name

        def __enter__(self) -> "streamlit_error_boundary":
            return self

        def __exit__(self, exc_type, exc, tb) -> bool:
            # False → deixa a exceção propagar; mantemos consistente
            return False

# ──────────────────────────────────────────────────────────────────────────────
# Session manager (fallbacks completos e seguros)
# ──────────────────────────────────────────────────────────────────────────────
try:
    from ..utils.session_manager import (
        get_session_value,
        set_session_value,
        get_selected_epic_id,
        set_current_page,
        get_current_page,
        initialize_page_state,
    )
    SESSION_MANAGER_AVAILABLE = True
except ImportError:
    SESSION_MANAGER_AVAILABLE = False

    # Memória efêmera por processo como fallback (não persiste entre execuções)
    _FALLBACK_SS: Dict[str, Any] = {"current_page": "Dashboard", "page_history": []}

    def get_session_value(key: str, default: Any = None) -> Any:
        return _FALLBACK_SS.get(key, default)

    def set_session_value(key: str, value: Any) -> None:
        _FALLBACK_SS[key] = value

    def get_selected_epic_id() -> Optional[int]:
        return _FALLBACK_SS.get("selected_epic_id")

    def set_current_page(page_name: str) -> None:
        _FALLBACK_SS["current_page"] = page_name

    def get_current_page() -> str:
        return _FALLBACK_SS.get("current_page", "Dashboard")

    def initialize_page_state() -> None:
        _FALLBACK_SS.setdefault("current_page", "Dashboard")
        _FALLBACK_SS.setdefault("page_history", [])

# ══════════════════════════════════════════════════════════════════════════════
# Page routing
# ══════════════════════════════════════════════════════════════════════════════

def render_current_page(user: Dict[str, Any]) -> None:
    """
    Render the current page based on session state navigation.
    Falls back to Dashboard when page system is unavailable or page is None.
    """
    if not STREAMLIT_AVAILABLE:
        return

    try:
        # Check for login page via query params first
        query_params = st.query_params or {}
        if query_params.get("page") == "login":
            _render_login_page()
            return
        
        current_page = (get_current_page() or "Dashboard").strip()  # robusto a None/"" 
        add_to_page_history(current_page)

        if current_page == "Dashboard":
            render_dashboard_content(user)
            return

        if PAGES_AVAILABLE:
            _render_pages_system_page(current_page)
        else:
            _render_page_not_found(current_page)

    except Exception as e:
        logger.error("Error rendering current page: %s", e)
        st.error("⚠️ Page rendering temporarily unavailable")
        _render_return_to_dashboard()

def _render_pages_system_page(current_page: str) -> None:
    """Render a page using the pages system."""
    if not STREAMLIT_AVAILABLE:
        return

    page_id = current_page.lower()  # "Clients" -> "clients"
    with streamlit_error_boundary(f"render_page_{page_id}"):
        result = render_page(page_id)
        if isinstance(result, dict) and result.get("error"):
            st.error(f"❌ Error loading {current_page}: {result['error']}")
            st.info("Returning to Dashboard...")
            set_current_page("Dashboard")
            if st.button("🔄 Return to Dashboard"):
                st.rerun()

def _render_page_not_found(current_page: str) -> None:
    """Render page not found error."""
    if not STREAMLIT_AVAILABLE:
        return

    st.error(f"❌ Page '{current_page}' is not available")
    st.info("Available pages: Dashboard")
    if st.button("🏠 Return to Dashboard"):
        set_current_page("Dashboard")
        st.rerun()

def _render_return_to_dashboard() -> None:
    """Render a return to dashboard button."""
    if not STREAMLIT_AVAILABLE:
        return
    if st.button("🏠 Return to Dashboard"):
        set_current_page("Dashboard")
        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# Dashboard content
# ══════════════════════════════════════════════════════════════════════════════

def render_dashboard_content(user: Dict[str, Any]) -> None:
    """Render the default dashboard content."""
    if not STREAMLIT_AVAILABLE:
        return

    try:
        with streamlit_error_boundary("quick_actions"):
            _render_quick_actions_section()

        with streamlit_error_boundary("analytics_row"):
            _render_analytics_section(user)

        with streamlit_error_boundary("heatmap_tasks"):
            _render_heatmap_tasks_section()

        with streamlit_error_boundary("timer_notifications"):
            render_timer_and_notifications()

    except Exception as e:
        logger.error("Error rendering dashboard content: %s", e)
        st.error("⚠️ Dashboard content temporarily unavailable")

def _render_analytics_section(user: Dict[str, Any]) -> None:
    """Render the analytics cards section."""
    user_id = user.get("id") if isinstance(user, dict) else None
    stats = fetch_user_stats(user_id)
    render_analytics_cards(stats or {})

def _render_heatmap_tasks_section() -> None:
    """Render the heatmap and tasks section."""
    epics = fetch_epics()
    selected_epic_id = get_selected_epic_id()
    render_heatmap_and_tasks(epics, selected_epic_id)

# ══════════════════════════════════════════════════════════════════════════════
# Navigation helpers
# ══════════════════════════════════════════════════════════════════════════════

def navigate_to_page(page_name: str, rerun: bool = True) -> None:
    """Navigate to a specific page."""
    if not STREAMLIT_AVAILABLE:
        return
    set_current_page(page_name)
    add_to_page_history(page_name)
    if rerun:
        st.rerun()


def redirect_to_login() -> None:
    """Redirect to login page with TDAH-friendly messaging."""
    if not STREAMLIT_AVAILABLE:
        return
    
    # Clear interface and show login
    st.empty()
    st.info("🔐 **Please log in to continue.** You'll return to your previous page after authentication.")
    
    # Navigate to login page
    set_current_page("login")
    st.rerun()

def get_available_page_names() -> List[str]:
    """Return list of available page names (always includes Dashboard)."""
    if PAGES_AVAILABLE:
        try:
            names = list(get_available_pages().keys())
            if "Dashboard" not in names:
                names.insert(0, "Dashboard")
            return names
        except Exception as e:
            logger.warning("Error getting available pages: %s", e)
    return ["Dashboard"]

# ══════════════════════════════════════════════════════════════════════════════
# Page state management
# ══════════════════════════════════════════════════════════════════════════════

def add_to_page_history(page_name: str) -> None:
    """Add a page to navigation history (MRU up to 10)."""
    history: List[str] = list(get_session_value("page_history", []))
    if page_name in history:
        history.remove(page_name)
    history.insert(0, page_name)
    set_session_value("page_history", history[:10])

def get_page_history() -> List[str]:
    """Get page navigation history."""
    return list(get_session_value("page_history", []))

def go_back() -> None:
    """Navigate to the previous page in history."""
    if not STREAMLIT_AVAILABLE:
        return
    history = get_page_history()
    if len(history) > 1:
        navigate_to_page(history[1])

# ══════════════════════════════════════════════════════════════════════════════
# Breadcrumbs
# ══════════════════════════════════════════════════════════════════════════════

def render_breadcrumb_navigation() -> None:
    """Render breadcrumb navigation based on current page."""
    if not STREAMLIT_AVAILABLE:
        return
    try:
        current_page = (get_current_page() or "Dashboard").strip()
        crumbs = ["🏠 Home"]
        if current_page != "Dashboard":
            crumbs.append(f"📄 {current_page}")
        st.caption(" → ".join(crumbs))
    except Exception as e:
        logger.warning("Error rendering breadcrumbs: %s", e)

# ══════════════════════════════════════════════════════════════════════════════
# Health check
# ══════════════════════════════════════════════════════════════════════════════

def check_page_manager_health() -> Dict[str, Any]:
    """Check health of page manager dependencies."""
    current = None
    try:
        current = (get_current_page() or "Dashboard")
    except Exception:
        current = "Dashboard"

    return {
        "streamlit_available": STREAMLIT_AVAILABLE,
        "analytics_cards_available": ANALYTICS_CARDS_AVAILABLE,
        "layout_renderers_available": LAYOUT_RENDERERS_AVAILABLE,
        "data_providers_available": DATA_PROVIDERS_AVAILABLE,
        "pages_available": PAGES_AVAILABLE,
        "exception_handler_available": EXCEPTION_HANDLER_AVAILABLE,
        "available_pages": get_available_page_names(),
        "current_page": current,
        "status": "healthy" if all([
            STREAMLIT_AVAILABLE,
            ANALYTICS_CARDS_AVAILABLE,
            LAYOUT_RENDERERS_AVAILABLE,
            DATA_PROVIDERS_AVAILABLE,
        ]) else "degraded",
    }

# ══════════════════════════════════════════════════════════════════════════════
# Quick actions
# ══════════════════════════════════════════════════════════════════════════════

def _render_quick_actions_section() -> None:
    """Render quick actions section with prominent wizard access."""
    if not STREAMLIT_AVAILABLE:
        return

    st.markdown("### 🚀 Quick Actions")
    col1, col2, col3 = st.columns([2, 1, 2])

    with col2:
        if st.button(
            "📝 Create New Project",
            use_container_width=True,
            type="primary",
            help="Launch the project wizard with AI assistance",
        ):
            set_current_page("projeto_wizard")
            st.rerun()

    st.markdown(
        """
        <div style='text-align: center; font-size: 0.8em; color: #666; margin-top: 10px;'>
        ✨ <strong>AI-Powered Wizard:</strong> Create complete projects with Epics, User Stories, and Tasks
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("---")

# ──────────────────────────────────────────────────────────────────────────────
# Public exports
# ──────────────────────────────────────────────────────────────────────────────
__all__ = [
    # Page routing
    "render_current_page",
    "render_dashboard_content",

    # Navigation helpers
    "set_current_page",
    "get_current_page",
    "navigate_to_page",
    "redirect_to_login",
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
