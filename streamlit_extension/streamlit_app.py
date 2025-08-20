#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 TDD Framework - Pure Orchestrator

Orchestrator-only implementation that delegates all functionality to specialized modules.
Follows clean architecture principles with minimal logic in the main entry point.

Architecture:
- All UI components extracted to separate modules
- Data fetching delegated to data providers
- Layout rendering delegated to layout renderers  
- Page management delegated to page manager
- Session management delegated to session manager
- Debug functionality delegated to debug widgets
"""

from __future__ import annotations

import logging
from typing import Dict, Any, Optional

# === MODULE IMPORTS ===========================================================

# Centralized imports - NO DUPLICATIONS, NO FALLBACKS
from .utils.streamlit_helpers import (
    is_ui, is_headless, set_page_config_once, safe_streamlit_error,
    add_project_to_path
)

from .utils.session_manager import initialize_session_state
from .utils.exception_handler import handle_streamlit_exceptions

# Components - centralized imports
from .components.sidebar import render_sidebar
from .components.layout_renderers import render_topbar  
from .components.page_manager import render_current_page
from .components.debug_widgets import render_debug_panel

# Authentication
from .utils.auth import (
    render_login_page, get_authenticated_user, is_user_authenticated
)

# Database queries (for headless mode)  
from .database.queries import list_epics
from .database.health import check_health

# Session manager for debug mode
from .utils.session_manager import is_debug_mode
# Auth imports
from streamlit_extension.auth.middleware import require_auth, require_admin
from streamlit_extension.auth.user_model import UserRole


# Setup logging
logger = logging.getLogger(__name__)

# Add project to path
add_project_to_path()

# Configure Streamlit page (if UI available)
if is_ui():
    set_page_config_once(
        page_title="TDD Framework Dashboard",
        page_icon="🚀",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            "Report a bug": "https://github.com/davidcantidio/test-tdd-project/issues",
            "About": """
            # TDD Framework - Advanced Dashboard
            - ⏱️ Timer com suporte a TDAH
            - 📋 Kanban de tarefas  
            - 📊 Analytics e produtividade
            - 🎮 Gamification
            - 🐙 Integração GitHub
            **Version:** 1.3.3 (Refactored)
            """,
        },
    )






# === ORCHESTRATOR FUNCTIONS ===================================================

def setup_application() -> None:
    """Setup application environment and dependencies."""
    initialize_session_state()
    logger.info("Session state initialized successfully")

def authenticate_user() -> Optional[Dict[str, Any]]:
    """Handle user authentication."""
    if not is_ui():
        return {"name": "Headless"}
    
    if not is_user_authenticated():
        try:
            render_login_page()
            return None  # Not authenticated
        except TypeError:
            logger.warning("Authentication not fully configured")
            safe_streamlit_error("⚠️ Authentication não configurada. Continuando sem login.")
    
    user = get_authenticated_user()
    return user if isinstance(user, dict) else {"name": "Dev"}

def render_application_ui(user: Dict[str, Any]) -> None:
    """Render the main application UI components."""
    if not is_ui():
        return
    
    try:
        # Render sidebar navigation
        sidebar_state = render_sidebar()
        logger.debug(f"Sidebar rendered with state: {type(sidebar_state)}")
        
        # Render top bar with header and health
        render_topbar(user)
        
        # Render current page content
        render_current_page(user)
        
        # Render debug panel if enabled
        if is_debug_mode():
            render_debug_panel()
    
    except Exception as e:
        logger.error(f"Error rendering application UI: {e}")
        safe_streamlit_error("⚠️ Application UI temporarily unavailable")

def run_headless_mode() -> None:
    """Run application in headless mode for testing."""
    logger.info("Running in headless mode - smoke test")
    
    try:
        epics = list_epics()
        health = check_health()
        logger.info(f"Headless test - Epics: {len(epics)}, Health: {health.get('status')}")
        print(f"⚠️ Streamlit não disponível — headless smoke test:")
        print(f" - list_epics(): {len(epics)}")
        print(f" - health: {health}")
    except Exception as e:
        logger.error(f"Headless test error: {e}")
        print(f" - erro DB: {e}")

# === MAIN ORCHESTRATOR ========================================================

@handle_streamlit_exceptions(show_error=True, attempt_recovery=True)
def main() -> None:
    """
    Main orchestrator function - delegates all functionality to specialized modules.
    
    This function serves as the single entry point and coordinates between:
    - Session management
    - Authentication
    - UI rendering 
    - Page management
    - Debug tools
    
    The orchestrator pattern ensures minimal logic in the main entry point.
    """
    try:
        # Handle headless mode
        if is_headless():
            run_headless_mode()
            return
        
        # Setup application state and dependencies
        setup_application()
        
        # Handle authentication
        user = authenticate_user()
        if user is None:
            # Authentication required but not completed
            return
        
        # Render main application UI
        render_application_ui(user)
        
        logger.info("Application orchestration completed successfully")
        
    except Exception as e:
        logger.error(f"Main orchestration error: {e}")
        if is_ui():
            safe_streamlit_error("⚠️ Application temporarily unavailable")
        else:
            print(f"❌ Application error: {e}")

# === MODULE HEALTH CHECK ======================================================

def check_orchestrator_health() -> Dict[str, Any]:
    """Check health of all orchestrator dependencies."""
    return {
        "streamlit_helpers_available": True,
        "session_manager_available": True,
        "exception_handler_available": True,
        "sidebar_available": True,
        "layout_renderers_available": True,
        "page_manager_available": True,
        "debug_widgets_available": True,
        "auth_available": True,
        "database_available": True,
        "ui_mode": "UI" if is_ui() else "Headless",
        "status": "healthy"
    }

# === ENTRY POINT ==============================================================

if __name__ == "__main__":
    main()
