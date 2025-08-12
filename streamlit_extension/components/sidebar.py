"""
🎛️ Streamlit Sidebar Component

Persistent sidebar with timer controls and navigation.
"""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta

# Graceful imports
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False

try:
    from ..config import get_config
except ImportError:
    get_config = None


def render_sidebar() -> Dict[str, Any]:
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
        
        # Timer Section (placeholder for now)
        st.markdown("## ⏱️ Timer")
        
        # Initialize timer state
        if "timer_running" not in st.session_state:
            st.session_state.timer_running = False
            st.session_state.timer_start_time = None
            st.session_state.current_task = None
            st.session_state.elapsed_seconds = 0
        
        # Task selection (placeholder)
        current_task = st.selectbox(
            "Current Task",
            ["No task selected", "Task 1", "Task 2", "Task 3"],
            index=0
        )
        
        if current_task != "No task selected":
            st.session_state.current_task = current_task
        
        # Timer controls
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("▶️ Start" if not st.session_state.timer_running else "⏸️ Pause"):
                if not st.session_state.timer_running:
                    st.session_state.timer_running = True
                    st.session_state.timer_start_time = datetime.now()
                else:
                    st.session_state.timer_running = False
                st.rerun()
        
        with col2:
            if st.button("⏹️ Stop"):
                st.session_state.timer_running = False
                st.session_state.timer_start_time = None
                st.session_state.elapsed_seconds = 0
                st.rerun()
        
        # Timer display
        if st.session_state.timer_running and st.session_state.timer_start_time:
            elapsed = datetime.now() - st.session_state.timer_start_time
            elapsed_seconds = int(elapsed.total_seconds())
            minutes = elapsed_seconds // 60
            seconds = elapsed_seconds % 60
            st.markdown(f"### ⏰ {minutes:02d}:{seconds:02d}")
        else:
            st.markdown("### ⏰ 00:00")
        
        sidebar_state["timer_running"] = st.session_state.timer_running
        sidebar_state["current_task"] = st.session_state.current_task
        sidebar_state["elapsed_seconds"] = st.session_state.elapsed_seconds
        
        st.markdown("---")
        
        # Epic Progress Section (placeholder)
        st.markdown("## 📊 Current Epic")
        
        # Progress bar (placeholder)
        progress_value = 0.65  # 65% completion
        st.progress(progress_value)
        st.markdown(f"**Progress:** {int(progress_value * 100)}%")
        
        # Stats
        st.markdown("### 📈 Today's Stats")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Tasks Done", "3", "1")
        with col2:
            st.metric("Focus Time", "2.5h", "0.5h")
        
        st.markdown("---")
        
        # Gamification Section (placeholder)
        if get_config and get_config().enable_gamification:
            st.markdown("## 🏆 Achievements")
            
            # Points display
            st.markdown("### 🌟 Points: **1,250**")
            
            # Streak
            st.markdown("### 🔥 Streak: **5 days**")
            
            # Recent badges (placeholder)
            st.markdown("### 🏅 Recent Badges")
            st.markdown("🎯 **Focus Master** - 25min session")
            st.markdown("⚡ **Speed Demon** - Task in < 10min")
            
            st.markdown("---")
        
        # Settings quick access
        st.markdown("## ⚙️ Quick Settings")
        
        # Theme toggle (placeholder)
        if st.button("🌙 Toggle Theme"):
            # This would toggle theme in actual implementation
            st.info("Theme toggle coming soon!")
        
        # GitHub sync status
        st.markdown("### 🐙 GitHub Sync")
        if get_config and get_config().is_github_configured():
            st.success("✅ Connected")
            if st.button("🔄 Sync Now"):
                st.info("Sync functionality coming in Task 1.2.8")
        else:
            st.warning("⚠️ Not configured")
        
        sidebar_state["github_configured"] = get_config().is_github_configured() if get_config else False
        
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