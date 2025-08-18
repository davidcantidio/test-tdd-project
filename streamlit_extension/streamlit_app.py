#!/usr/bin/env python3
"""
🚀 TDD Framework - Enhanced Streamlit Dashboard

Advanced dashboard with:
- Dynamic welcome header with time-based greetings
- Productivity overview with heatmaps and metrics
- Enhanced epic progress cards with visualizations
- Real-time notifications system
- Gamification widgets
- Interactive timer with TDAH support
"""

import sys
import time
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

# Add parent directory to path for imports (ensure precedence)
project_root = str(Path(__file__).parent.parent.resolve())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Graceful imports
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    # Graceful fallback for testing and development
    print("⚠️ Streamlit not available - running in headless mode")
    print("To run the dashboard: pip install streamlit")
    STREAMLIT_AVAILABLE = False

    # Mock streamlit module for testing/headless environments
    class _MockSessionState(dict):
        """Simple dict-backed session_state mock."""
        pass

    class MockStreamlit:
        def __init__(self):
            self.session_state = _MockSessionState()
            # emulate Streamlit query params as a dict-like with .get/.clear
            self.query_params = {}

        # Basic UI no-ops
        def set_page_config(self, *args, **kwargs): return None
        def columns(self, spec): return [self] * (spec if isinstance(spec, int) else len(spec))
        def expander(self, *args, **kwargs):
            class _NoOpCtx:
                def __enter__(self_inner): return self
                def __exit__(self_inner, *exc): return False
            return _NoOpCtx()
        def container(self): return self
        def button(self, *args, **kwargs): return False
        def progress(self, *args, **kwargs): return None
        def metric(self, *args, **kwargs): return None
        def json(self, *args, **kwargs): return None
        def code(self, *args, **kwargs): return None
        def write(self, *args, **kwargs): return None
        def markdown(self, *args, **kwargs): return None
        def caption(self, *args, **kwargs): return None
        def error(self, *args, **kwargs): return None
        def warning(self, *args, **kwargs): return None
        def info(self, *args, **kwargs): return None
        def success(self, *args, **kwargs): return None
        def stop(self): return None
        def spinner(self, *args, **kwargs):
            class _NoOpCtx:
                def __enter__(self_inner): return self
                def __exit__(self_inner, *exc): return False
            return _NoOpCtx()
        def rerun(self): return None
        def selectbox(self, *args, **kwargs): return kwargs.get("index_label", "Select a task...") if "index_label" in kwargs else "Select a task..."

    st = MockStreamlit()

# Configure page (only if Streamlit is available)
if STREAMLIT_AVAILABLE:
    st.set_page_config(
        page_title="TDD Framework Dashboard",
        page_icon="🚀",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            'Get Help': None,
            'Report a bug': 'https://github.com/davidcantidio/test-tdd-project/issues',
            'About': """
            # TDD Framework - Advanced Dashboard

            Interactive development environment for TDD workflow with:
            - ⏱️ Focus timer with TDAH support
            - 📋 Task management with Kanban
            - 📊 Analytics and productivity tracking
            - 🎮 Gamification system
            - 🐙 GitHub integration

            **Version:** 1.2.1
            **Phase:** Enhanced Dashboard
            """
        }
    )

# Import components
try:
    from streamlit_extension.components.sidebar import render_sidebar
    from streamlit_extension.components.timer import TimerComponent
    from streamlit_extension.components.dashboard_widgets import (
        WelcomeHeader, DailyStats, ProductivityHeatmap,
        ProgressRing, SparklineChart, AchievementCard,
        NotificationToast, NotificationData, QuickActionButton
    )
    from streamlit_extension.utils.database import DatabaseManager
    from streamlit_extension.utils.auth import (
        GoogleOAuthManager,
        render_login_page,
        get_authenticated_user,
        is_user_authenticated
    )
    from streamlit_extension.config import load_config

    # Import service layer and application setup
    from streamlit_extension.utils.app_setup import (
        setup_application, get_session_services, check_services_health,
        get_client_service, get_project_service, get_analytics_service
    )

    # Import global exception handler
    from streamlit_extension.utils.exception_handler import (
        install_global_exception_handler, handle_streamlit_exceptions,
        streamlit_error_boundary, safe_streamlit_operation,
        show_error_dashboard, get_error_statistics
    )
    EXCEPTION_HANDLER_AVAILABLE = True
except ImportError as e:
    EXCEPTION_HANDLER_AVAILABLE = False

    # Create a no-op decorator for testing environments
    def handle_streamlit_exceptions(show_error=True, attempt_recovery=True):
        def decorator(func):
            return func
        return decorator

    # Create no-op functions for other missing imports
    def streamlit_error_boundary(operation_name):
        class NoOpContext:
            def __enter__(self): return self
            def __exit__(self, *args): pass
        return NoOpContext()

    def safe_streamlit_operation(func, *args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception:
            return kwargs.get('default_return')

    if STREAMLIT_AVAILABLE:
        st.error(f"❌ Import Error: {e}")
        st.error("Make sure to run from the project root directory")
        st.stop()


# Use decorator conditionally - available in both success and failure cases now
@handle_streamlit_exceptions(show_error=True, attempt_recovery=True)
def initialize_session_state():
    """Initialize Streamlit session state variables."""

    # Install global exception handler on first run
    if EXCEPTION_HANDLER_AVAILABLE and "exception_handler_installed" not in st.session_state:
        install_global_exception_handler()
        st.session_state.exception_handler_installed = True

    # Core app state
    if "config" not in st.session_state:
        with streamlit_error_boundary("configuration_loading"):
            st.session_state.config = load_config()

    # Initialize application services (database + service layer)
    if "services_ready" not in st.session_state:
        with streamlit_error_boundary("application_setup"):
            setup_application()
            st.session_state.services_ready = True

    # Legacy database manager support (for backward compatibility)
    if "db_manager" not in st.session_state:
        db_manager, _ = get_session_services()
        if db_manager:
            st.session_state.db_manager = db_manager

    # Timer component
    if "timer_component" not in st.session_state:
        st.session_state.timer_component = TimerComponent()

    # Navigation state
    if "current_page" not in st.session_state:
        st.session_state.current_page = "Dashboard"

    # User preferences
    if "show_debug_info" not in st.session_state:
        st.session_state.show_debug_info = st.session_state.config.debug_mode

    # Database health
    if "db_health_check" not in st.session_state:
        with streamlit_error_boundary("database_health_check"):
            st.session_state_
