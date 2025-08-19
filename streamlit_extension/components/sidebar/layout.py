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
    """
    Render the persistent sidebar with timer and navigation.
    
    Returns:
        Dict containing sidebar state and user actions
    """
    if not STREAMLIT_AVAILABLE:
        return {"error": "Streamlit not available"}
    
    sidebar_state = {}
    
    with st.sidebar:
        # Header
        st.markdown("# 🚀 TDD Framework")
        st.markdown("---")
        
        # Timer Section
        st.markdown("## ⏱️ Timer")
        
        # Initialize timer state
        initialize_timer_state()
        
        # Task selection (placeholder)
        current_task = st.selectbox(
            "Current Task",
            ["No task selected", "Task 1", "Task 2", "Task 3"],
            index=0
        )
        
        set_current_task(current_task)
        
        # Timer controls
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("▶️ Start" if not st.session_state.get("timer_running") else "⏸️ Pause"):
                if not st.session_state.get("timer_running"):
                    start_timer()
                else:
                    pause_timer()
                st.rerun()
        
        with col2:
            if st.button("⏹️ Stop"):
                stop_timer()
                st.rerun()
        
        # Display timer
        minutes, seconds = get_elapsed_time()
        st.markdown(f"### ⏰ {minutes:02d}:{seconds:02d}")
        
        # Store timer data for filters
        timer_data = get_timer_state()
        
        st.markdown("---")
        
        # Navigation Menu
        st.markdown("## 🧭 Navigation")
        
        # Initialize current page in session state
        if "current_page" not in st.session_state:
            st.session_state.current_page = "Dashboard"
        
        # Navigation buttons
        nav_pages = {
            "🏠 Dashboard": "Dashboard",
            "👥 Clients": "Clients", 
            "📁 Projects": "Projects",
            "📋 Epics": "Epics",
            "✅ Tasks": "Tasks"
        }
        
        current_page = st.session_state.current_page
        for display_name, page_key in nav_pages.items():
            if st.button(
                display_name, 
                key=f"nav_{page_key}",
                use_container_width=True,
                type="primary" if page_key == current_page else "secondary"
            ):
                st.session_state.current_page = page_key
                st.rerun()
        
        # Format return data as specified: {page: str, filters: dict}
        sidebar_state["page"] = st.session_state.current_page
        sidebar_state["filters"] = timer_data
        
        # Maintain backward compatibility
        sidebar_state["current_page"] = st.session_state.current_page
        
        st.markdown("---")
        
        # Epic Progress Section (placeholder)
        st.markdown("## 📊 Current Epic")
        
        # Progress bar (placeholder)
        progress_value = 0.65  # 65% completion
        st.progress(progress_value)
        st.markdown(f"**Progress:** {int(progress_value * 100)}%")
        
        # Stats (real data from database)
        st.markdown("### 📈 Today's Stats")
        gamification_data = get_gamification_data(user_id)
        
        col1, col2 = st.columns(2)
        with col1:
            completed_tasks = gamification_data.get("completed_tasks", 0)
            st.metric("Tasks Done", str(completed_tasks), "+1" if completed_tasks > 0 else None)
        with col2:
            # Calculate real focus time from work_sessions table
            focus_display, delta_display = get_focus_time_from_db(user_id)
            st.metric("Focus Time", focus_display, delta_display)
        
        st.markdown("---")
        
        # Gamification Section (real data)
        cfg = get_config() if get_config else None
        if cfg and getattr(cfg, "enable_gamification", False):
            st.markdown("## 🏆 Achievements")
            
            # Get real gamification data
            gamification_data = get_gamification_data(user_id)
            
            # Points display
            total_points = gamification_data.get("total_points", 0)
            recent_points = gamification_data.get("recent_points", 0)
            st.metric("🌟 Total Points", f"{total_points:,}", f"+{recent_points}" if recent_points > 0 else None)
            
            # Streak
            current_streak = gamification_data.get("current_streak", 0)
            streak_type = gamification_data.get("streak_type", "daily focus")
            st.metric("🔥 Current Streak", f"{current_streak} days", f"{streak_type}")
            
            # Recent achievements
            achievements = gamification_data.get("recent_achievements", [])
            if achievements:
                st.markdown("### 🏅 Recent Badges")
                for achievement in achievements[:3]:  # Show last 3
                    badge_emoji = get_achievement_emoji(achievement.get("code", ""))
                    st.markdown(f"{badge_emoji} **{achievement.get('name', 'Achievement')}** - {achievement.get('description', '')}")
            else:
                st.markdown("### 🏅 Keep working to unlock badges!")
            
            # Progress to next achievement
            next_achievement = get_next_achievement_progress(gamification_data)
            if next_achievement:
                st.markdown("### 🎯 Next Goal")
                progress_pct = next_achievement.get("progress", 0) / 100
                st.progress(progress_pct)
                st.markdown(f"**{next_achievement.get('name', 'Next Achievement')}**")
                st.markdown(f"{next_achievement.get('progress', 0)}/{next_achievement.get('target', 100)} - {next_achievement.get('description', '')}")
            
            st.markdown("---")
        
        # Settings quick access
        st.markdown("## ⚙️ Quick Settings")
        
        # Theme toggle (placeholder)
        if st.button("🌙 Toggle Theme"):
            # This would toggle theme in actual implementation
            st.info("Theme toggle coming soon!")
        
        # GitHub sync status
        st.markdown("### 🐙 GitHub Sync")
        if cfg and hasattr(cfg, "is_github_configured") and cfg.is_github_configured():
            st.success("✅ Connected")
            if st.button("🔄 Sync Now"):
                st.info("Sync functionality coming in Task 1.2.8")
        else:
            st.warning("⚠️ Not configured")

        # Add github status to filters
        sidebar_state["filters"]["github_configured"] = bool(cfg and hasattr(cfg, "is_github_configured") and cfg.is_github_configured())
        
        # Maintain backward compatibility
        sidebar_state["github_configured"] = bool(cfg and hasattr(cfg, "is_github_configured") and cfg.is_github_configured())
        
        st.markdown("---")
        
        # Footer
        st.markdown("### 🤖 Framework Info")
        st.markdown("**Version:** 1.0.0")
        st.markdown("**Phase:** 1.2 Development")
    
    return sidebar_state


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