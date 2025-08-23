"""
🏗️ Sidebar Layout Module

Main sidebar rendering functions importing from specialized modules.
Contains render_sidebar() and render_timer_controls() as entry points.
"""

from typing import Optional, Dict, Any

# Local module imports
from .timer import (
    initialize_timer_state, start_timer, pause_timer, stop_timer, 
    get_elapsed_time, get_timer_state, set_current_task
)
from .gamification import get_gamification_data, get_achievement_emoji, get_next_achievement_progress
from .database_utils import get_focus_time_from_db

# Graceful streamlit import
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False

# Graceful config import
try:
    from ...config import get_config
except ImportError:
    get_config = None


def render_sidebar(user_id: int = 1) -> Dict[str, Any]:
    """Render modern sidebar with navigation and timer controls."""
    if not STREAMLIT_AVAILABLE:
        return {"error": "Streamlit not available"}
    
    # Sidebar navigation to wizard
    with st.sidebar:
        st.markdown("### 🚀 Quick Actions")
        
        if st.button("📝 New Project", use_container_width=True, type="primary"):
            # Import here to avoid circular imports
            try:
                from ...utils.session_manager import set_current_page
                set_current_page("projeto_wizard")
                st.rerun()
            except ImportError:
                st.error("Navigation not available")
        
        st.markdown("---")
        
        # Basic timer controls (placeholder for now)
        st.markdown("### ⏱️ Timer")
        st.markdown("*Timer functionality available in Timer page*")
        
        # Basic gamification display (placeholder for now)  
        st.markdown("### 🎮 Progress")
        st.markdown("*Progress tracking available in Analytics*")
        
    return {
        "sidebar_rendered": True,
        "wizard_button_available": True
    }


def render_timer_controls() -> Dict[str, Any]:
    """
    Render just the timer controls (for embedding in other components).
    
    Returns:
        Dict containing timer state
    """
    if not STREAMLIT_AVAILABLE:
        return {"error": "Streamlit not available"}
    
    # This would be a more focused timer component
    # Implementation would be similar to the sidebar version
    # but optimized for embedding in other pages
    
    return {
        "timer_running": False,
        "elapsed_time": "00:00",
        "current_task": None
    }

