"""
🎛️ Streamlit Sidebar Components

Modular sidebar with timer controls, navigation, and gamification.
Refactored from single sidebar.py into specialized modules for better maintainability.
"""

from .layout import render_sidebar, render_timer_controls
# Auth imports
from streamlit_extension.auth.middleware import require_auth, require_admin
from streamlit_extension.auth.user_model import UserRole


# Public exports - maintain compatibility
__all__ = ["render_sidebar", "render_timer_controls"]