"""
⏱️ Timer Logic Module

Handles timer state management and operations.
Provides start, pause, stop, and elapsed time functionality for focus sessions.
"""

from typing import Dict, Any, Optional
from datetime import datetime

# Graceful import
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False


def initialize_timer_state() -> None:
    """Initialize timer state in session state if not exists."""
    if not STREAMLIT_AVAILABLE:
        return
    
    if "timer_running" not in st.session_state:
        st.session_state.timer_running = False
        st.session_state.timer_start_time = None
        st.session_state.current_task = None
        st.session_state.elapsed_seconds = 0  # accumulated when paused


def start_timer() -> None:
    """Start or resume the timer."""
    if not STREAMLIT_AVAILABLE:
        return
    
    st.session_state.timer_running = True
    st.session_state.timer_start_time = datetime.now()


def pause_timer() -> None:
    """Pause the timer and accumulate elapsed time."""
    if not STREAMLIT_AVAILABLE:
        return
    
    st.session_state.timer_running = False
    if st.session_state.timer_start_time:
        st.session_state.elapsed_seconds += int(
            (datetime.now() - st.session_state.timer_start_time).total_seconds()
        )
        st.session_state.timer_start_time = None


def stop_timer() -> None:
    """Stop and reset the timer."""
    if not STREAMLIT_AVAILABLE:
        return
    
    st.session_state.timer_running = False
    st.session_state.timer_start_time = None
    st.session_state.elapsed_seconds = 0


def get_elapsed_time() -> tuple[int, int]:
    """Get current elapsed time as (minutes, seconds)."""
    if not STREAMLIT_AVAILABLE:
        return 0, 0
    
    # Calculate total elapsed time
    total_secs = st.session_state.get("elapsed_seconds", 0)
    if st.session_state.get("timer_running") and st.session_state.get("timer_start_time"):
        total_secs += int(
            (datetime.now() - st.session_state.timer_start_time).total_seconds()
        )
    
    minutes, seconds = total_secs // 60, total_secs % 60
    return minutes, seconds


def get_timer_state() -> Dict[str, Any]:
    """Get current timer state for sidebar state."""
    if not STREAMLIT_AVAILABLE:
        return {
            "timer_running": False,
            "current_task": None,
            "elapsed_seconds": 0
        }
    
    return {
        "timer_running": st.session_state.get("timer_running", False),
        "current_task": st.session_state.get("current_task"),
        "elapsed_seconds": st.session_state.get("elapsed_seconds", 0)
    }


def set_current_task(task: str) -> None:
    """Set the current task for the timer."""
    if not STREAMLIT_AVAILABLE:
        return
    
    if task != "No task selected":
        st.session_state.current_task = task