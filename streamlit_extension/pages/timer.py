"""
⏱️ Timer Page

Dedicated timer interface with TDAH support:
- Focus session management
- Pomodoro technique integration
- TDAH-specific metrics tracking
- Session history and analytics
- Customizable timer settings
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

# Graceful imports
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False
    st = None

# Local imports
try:
    from streamlit_extension.utils.database import DatabaseManager
    from streamlit_extension.config import load_config
    from streamlit_extension.components.timer import TimerComponent
    from streamlit_extension.utils.security import (
        sanitize_display, validate_form, check_rate_limit,
        security_manager
    )
    from streamlit_extension.utils.exception_handler import (
        handle_streamlit_exceptions, streamlit_error_boundary, safe_streamlit_operation
    )
    from streamlit_extension.config.constants import ErrorMessages, UIConstants, TaskStatus
    # Import authentication middleware
    from streamlit_extension.auth.middleware import init_protected_page
    DATABASE_UTILS_AVAILABLE = True
except ImportError:
    DatabaseManager = load_config = TimerComponent = None
    sanitize_display = validate_form = None
    check_rate_limit = security_manager = None
    init_protected_page = ErrorMessages = UIConstants = TaskStatus = None
    DATABASE_UTILS_AVAILABLE = False


@handle_streamlit_exceptions(show_error=True, attempt_recovery=True)
def render_timer_page():
    """Render the dedicated timer page."""
    if not STREAMLIT_AVAILABLE:
        return {"error": "Streamlit not available"}
    
    # Initialize protected page with authentication
    current_user = init_protected_page(UIConstants.TIMER_PAGE_TITLE)
    if not current_user:
        return {"error": "Authentication required"}
    
    # Check rate limit for page load
    page_rate_allowed, page_rate_error = check_rate_limit("page_load") if check_rate_limit else (True, None)
    if not page_rate_allowed:
        st.error(f"🚦 {page_rate_error}")
        st.info("Please wait before reloading the page.")
        return {"error": "Rate limited"}
    
    st.markdown("---")
    
    if not DATABASE_UTILS_AVAILABLE:
        st.error(
            ErrorMessages.LOADING_ERROR.format(
                entity="database utilities", error="not available"
            )
        )
        return
    
    # Initialize components
    try:
        config = load_config()
        db_manager = DatabaseManager(
            framework_db_path=str(config.get_database_path()),
            timer_db_path=str(config.get_timer_database_path())
        )
        
        # Initialize timer component if not in session state
        if "timer_component" not in st.session_state:
            st.session_state.timer_component = TimerComponent()
        
        timer_component = st.session_state.timer_component
        
    except Exception as e:
        st.error(ErrorMessages.LOADING_ERROR.format(entity="initialization", error=e))
        return
    
    # Sidebar for timer settings
    _render_timer_sidebar(config)
    
    # Main timer interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
        _render_main_timer(timer_component, db_manager, config)
    
    with col2:
        _render_session_stats(db_manager)
    
    st.markdown("---")
    
    # Session history and analytics
    _render_session_history(db_manager)
    
    # TDAH-specific insights
    _render_tdah_insights(db_manager)


def _render_timer_sidebar(config):
    """Render timer configuration sidebar."""
    
    st.sidebar.markdown("## ⏱️ Timer Settings")
    
    # Session type
    session_types = {
        "Focus Session": config.focus_session_duration,
        "Short Break": config.short_break_duration,
        "Long Break": config.long_break_duration,
        "Custom": 0
    }
    
    selected_type = st.sidebar.selectbox(
        "Session Type", 
        list(session_types.keys()),
        index=0
    )
    
    if selected_type == "Custom":
        duration = st.sidebar.number_input(
            "Duration (minutes)", 
            min_value=1, 
            max_value=120, 
            value=25,
            step=5
        )
    else:
        duration = session_types[selected_type]
        st.sidebar.info(f"Duration: {duration} minutes")
    
    st.session_state.timer_duration = duration
    st.session_state.timer_type = selected_type.lower().replace(" ", "_")
    
    st.sidebar.markdown("---")
    
    # TDAH Settings
    st.sidebar.markdown("## 🧠 TDAH Settings")
    
    st.session_state.timer_track_focus = st.sidebar.checkbox(
        "Track Focus Rating", 
        value=config.enable_focus_tracking,
        help="Rate your focus level during sessions"
    )
    
    st.session_state.timer_track_interruptions = st.sidebar.checkbox(
        "Count Interruptions", 
        value=True,
        help="Track interruptions during focus sessions"
    )
    
    st.session_state.timer_track_energy = st.sidebar.checkbox(
        "Track Energy Level", 
        value=True,
        help="Monitor energy levels throughout the day"
    )
    
    st.session_state.timer_track_mood = st.sidebar.checkbox(
        "Track Mood", 
        value=True,
        help="Record mood before/after sessions"
    )
    
    # Sound settings
    st.sidebar.markdown("## 🔊 Alerts")
    
    st.session_state.timer_sound_alerts = st.sidebar.checkbox(
        "Sound Alerts", 
        value=config.enable_sound_alerts,
        help="Play sound when timer completes"
    )
    
    st.session_state.timer_notifications = st.sidebar.checkbox(
        "Browser Notifications", 
        value=config.enable_notifications,
        help="Show browser notifications"
    )


def _render_main_timer(timer_component, db_manager: DatabaseManager, config):
    """Render the main timer interface."""
    
    st.markdown("### 🎯 Current Session")
    
    # Task selection with error handling and memoization
    @st.cache_data(ttl=300)  # Cache for 5 minutes to improve performance
    def get_active_tasks():
        """Get active tasks with caching for performance."""
        tasks = db_manager.get_tasks()
        return [
            t
            for t in tasks
            if t.get("status")
            in [
                TaskStatus.TODO.value,
                TaskStatus.PENDING.value,
                TaskStatus.IN_PROGRESS.value,
            ]
        ]
    
    try:
        active_tasks = get_active_tasks()
        
        if active_tasks:
            task_options = ["No specific task"] + [f"{t['title']} ({t.get('epic_name', 'No Epic')})" for t in active_tasks]
            selected_task_option = st.selectbox("Working on:", task_options)
            
            if selected_task_option != "No specific task":
                # Find selected task
                selected_task = None
                for task in active_tasks:
                    task_display = f"{task['title']} ({task.get('epic_name', 'No Epic')})"
                    if task_display == selected_task_option:
                        selected_task = task
                        break
                
                if selected_task:
                    st.session_state.current_task = selected_task
                    st.info(f"🎯 **Task:** {selected_task['title']}")
                    if selected_task.get('description'):
                        st.caption(f"Description: {selected_task['description']}")
                    # Show epic info
                    if selected_task.get('epic_name'):
                        st.caption(f"📊 Epic: {selected_task['epic_name']}")
            else:
                st.session_state.current_task = None
        else:
            st.info(ErrorMessages.NO_ITEMS_FOUND.format(entity="active tasks"))
            st.session_state.current_task = None
    except Exception as e:
        st.error(
            ErrorMessages.LOADING_ERROR.format(
                entity="tasks for timer", error=e
            )
        )
        st.session_state.current_task = None
    
    # Main timer display
    timer_state = timer_component.render()
    
    # Session controls
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if not timer_state.get("current_session"):
            if st.button("▶️ Start Timer", type="primary", use_container_width=True):
                _start_timer_session(timer_component, db_manager)
        else:
            if st.button(f"{UIConstants.ICON_ON_HOLD} Pause", use_container_width=True):
                timer_component.pause_session()
                st.rerun()
    
    with col2:
        if timer_state.get("current_session"):
            if st.button("⏹️ Stop", use_container_width=True):
                _end_timer_session(timer_component, db_manager)
            
    with col3:
        if timer_state.get("current_session") and timer_state.get("paused"):
            if st.button("▶️ Resume", use_container_width=True):
                timer_component.resume_session()
                st.rerun()
        elif timer_state.get("current_session"):
            if st.button("⏭️ Skip", use_container_width=True):
                _skip_timer_session(timer_component, db_manager)
    
    with col4:
        if st.button("🔄 Reset", use_container_width=True):
            timer_component.reset_session()
            if "current_task" in st.session_state:
                del st.session_state.current_task
            st.rerun()
    
    # Session progress and info
    if timer_state.get("current_session"):
        session = timer_state["current_session"]
        elapsed_minutes = timer_state.get("elapsed_minutes", 0)
        total_minutes = session.planned_duration_minutes
        progress = min(elapsed_minutes / total_minutes, 1.0) if total_minutes > 0 else 0
        
        st.progress(progress)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Elapsed", f"{elapsed_minutes:.0f}min")
        with col2:
            st.metric("Target", f"{total_minutes}min")
        with col3:
            remaining = max(0, total_minutes - elapsed_minutes)
            st.metric("Remaining", f"{remaining:.0f}min")
        
        # Session type indicator
        session_type = st.session_state.get("timer_type", "focus_session").replace("_", " ").title()
        st.info(f"🎯 **{session_type}** in progress...")
        
        if timer_state.get("paused"):
            st.warning(f"{UIConstants.ICON_ON_HOLD} **Timer is paused**")


def _render_session_stats(db_manager: DatabaseManager):
    """Render session statistics in the sidebar."""
    
    st.markdown("### 📊 Today's Stats")
    
    # Get today's sessions
    today_sessions = _get_todays_sessions(db_manager)
    
    if today_sessions:
        total_time = sum(s.get("planned_duration_minutes", 0) for s in today_sessions)
        completed_sessions = len([s for s in today_sessions if s.get("ended_at")])
        avg_focus = _calculate_avg_focus_rating(today_sessions)
        total_interruptions = sum(s.get("interruptions_count", 0) for s in today_sessions)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Focus Time", f"{total_time}min")
            st.metric("Sessions", completed_sessions)
        
        with col2:
            st.metric("Avg Focus", f"{avg_focus:.1f}/10" if avg_focus > 0 else "N/A")
            st.metric("Interruptions", total_interruptions)
        
        # Focus time visualization
        if len(today_sessions) > 1:
            st.markdown("#### 📈 Focus Pattern")
            session_times = []
            session_ratings = []
            
            for i, session in enumerate(today_sessions):
                session_times.append(f"S{i+1}")
                session_ratings.append(session.get("focus_rating", 0))
            
            # Simple bar chart using st.bar_chart
            if any(session_ratings):
                import pandas as pd
                chart_data = pd.DataFrame({
                    "Focus Rating": session_ratings
                }, index=session_times)
                st.bar_chart(chart_data)
        
    else:
        st.info("🌅 Start your first session of the day!")


def _render_session_history(db_manager: DatabaseManager):
    """Render recent session history."""
    
    st.markdown("### 📅 Recent Sessions")
    
    @st.cache_data(ttl=180)  # Cache for 3 minutes
    def get_recent_sessions():
        """Get recent sessions with caching for performance."""
        return db_manager.get_timer_sessions(days=7)
    
    recent_sessions = get_recent_sessions()
    
    if not recent_sessions:
        st.info(ErrorMessages.NO_ITEMS_FOUND.format(entity="recent sessions"))
        return
    
    # Session history table
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Show last 10 sessions
        for session in recent_sessions[:10]:
            with st.container():
                # Session header
                started_at = session.get("started_at", "Unknown")
                task_ref = session.get("task_reference", "General focus")
                duration = session.get("planned_duration_minutes", 0)
                
                col_info, col_metrics = st.columns([2, 1])
                
                with col_info:
                    date_str = started_at[:16] if len(started_at) >= 16 else started_at
                    st.markdown(f"**{date_str}** - {task_ref}")
                    st.caption(f"Duration: {duration} minutes")
                
                with col_metrics:
                    focus_rating = session.get("focus_rating")
                    if focus_rating:
                        st.metric("Focus", f"{focus_rating}/10")
                    
                    interruptions = session.get("interruptions_count", 0)
                    if interruptions > 0:
                        st.metric("Interruptions", interruptions)
                
                st.markdown("---")
    
    with col2:
        # Summary stats
        st.markdown("#### 📊 Week Summary")
        
        total_sessions = len(recent_sessions)
        total_minutes = sum(s.get("planned_duration_minutes", 0) for s in recent_sessions)
        hours = total_minutes // 60
        minutes = total_minutes % 60
        
        st.metric("Total Sessions", total_sessions)
        st.metric("Total Time", f"{hours}h {minutes}m")
        
        avg_focus = _calculate_avg_focus_rating(recent_sessions)
        if avg_focus > 0:
            st.metric("Avg Focus", f"{avg_focus:.1f}/10")
        
        # Best session
        if recent_sessions:
            best_session = max(
                recent_sessions, 
                key=lambda s: s.get("focus_rating", 0)
            )
            if best_session.get("focus_rating", 0) > 0:
                st.metric("Best Focus", f"{best_session['focus_rating']}/10")


def _render_tdah_insights(db_manager: DatabaseManager):
    """Render TDAH-specific insights and recommendations."""
    
    st.markdown("### 🧠 TDAH Insights")
    
    @st.cache_data(ttl=600)  # Cache for 10 minutes (insights don't change frequently)
    def get_sessions_for_analysis():
        """Get sessions for TDAH analysis with caching."""
        return db_manager.get_timer_sessions(days=14)
    
    # Get data for analysis
    recent_sessions = get_sessions_for_analysis()
    
    if len(recent_sessions) < 3:
        st.info("📊 Complete a few more sessions to see personalized TDAH insights.")
        return
    
    # Analyze patterns
    insights = _analyze_tdah_patterns(recent_sessions)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🎯 Focus Patterns")
        
        best_time = insights.get("best_focus_time")
        if best_time:
            st.success(f"🌟 **Best focus time:** {best_time}")
        
        avg_session_length = insights.get("avg_effective_session")
        if avg_session_length:
            st.info(f"⏱️ **Optimal session length:** {avg_session_length} minutes")
        
        interruption_pattern = insights.get("interruption_pattern")
        if interruption_pattern:
            st.warning(f"🚫 **Interruption trend:** {interruption_pattern}")
    
    with col2:
        st.markdown("#### 💡 Recommendations")
        
        recommendations = insights.get("recommendations", [])
        for rec in recommendations:
            st.markdown(f"• {rec}")
        
        if not recommendations:
            st.info("Keep tracking sessions to get personalized recommendations!")
    
    # Energy level analysis
    energy_sessions = [s for s in recent_sessions if s.get("energy_level")]
    if energy_sessions:
        st.markdown("#### ⚡ Energy Level Analysis")
        
        energy_data = {}
        for session in energy_sessions:
            hour = _extract_hour_from_timestamp(session.get("started_at"))
            if hour is not None:
                if hour not in energy_data:
                    energy_data[hour] = []
                energy_data[hour].append(session.get("energy_level", 0))
        
        if energy_data:
            # Find peak energy hours
            avg_energy_by_hour = {
                hour: sum(levels) / len(levels) 
                for hour, levels in energy_data.items()
            }
            
            peak_hour = max(avg_energy_by_hour, key=avg_energy_by_hour.get)
            peak_energy = avg_energy_by_hour[peak_hour]
            
            st.success(f"⚡ **Peak energy time:** {peak_hour}:00 (avg {peak_energy:.1f}/10)")


def _start_timer_session(timer_component, db_manager: DatabaseManager):
    """Start a new timer session."""
    
    duration = st.session_state.get("timer_duration", 25)
    session_type = st.session_state.get("timer_type", "focus_session")
    current_task = st.session_state.get("current_task")
    
    # Pre-session TDAH metrics
    pre_session_data = {}
    
    if st.session_state.get("timer_track_mood"):
        pre_session_data["pre_mood"] = _get_quick_mood_rating()
    
    if st.session_state.get("timer_track_energy"):
        pre_session_data["energy_level"] = _get_quick_energy_rating()
    
    # Start the session
    task_reference = current_task.get("title") if current_task else None
    timer_component.start_session(
        duration_minutes=duration,
        session_type=session_type,
        task_reference=task_reference,
        **pre_session_data
    )
    
    st.success(f"⏱️ Started {duration}-minute {session_type.replace('_', ' ')} session!")
    st.rerun()


def _end_timer_session(timer_component, db_manager: DatabaseManager):
    """End the current timer session with TDAH metrics."""
    
    if not timer_component.current_session:
        return
    
    # Collect post-session metrics
    post_session_data = {}
    
    if st.session_state.get("timer_track_focus"):
        post_session_data["focus_rating"] = _get_focus_rating()
    
    if st.session_state.get("timer_track_interruptions"):
        post_session_data["interruptions_count"] = _get_interruption_count()
    
    if st.session_state.get("timer_track_mood"):
        post_session_data["post_mood"] = _get_quick_mood_rating()
    
    # End the session
    timer_component.end_session(**post_session_data)
    
    st.success(f"{UIConstants.ICON_COMPLETED} Session completed! Great work!")
    st.rerun()


def _skip_timer_session(timer_component, db_manager: DatabaseManager):
    """Skip the current session (early completion)."""
    
    if not timer_component.current_session:
        return
    
    # Still collect some metrics
    post_session_data = {}
    
    if st.session_state.get("timer_track_focus"):
        post_session_data["focus_rating"] = _get_focus_rating()
    
    if st.session_state.get("timer_track_interruptions"):
        post_session_data["interruptions_count"] = _get_interruption_count()
    
    # End session early
    timer_component.end_session(**post_session_data)
    
    st.info("⏭️ Session skipped. Every bit of progress counts!")
    st.rerun()


# Helper functions for TDAH metrics

def _get_focus_rating() -> int:
    """Get focus rating from user (quick modal-like interface)."""
    # In a real implementation, this would show a modal or use session state
    # For now, return a default value
    return st.session_state.get("temp_focus_rating", 7)


def _get_interruption_count() -> int:
    """Get interruption count from user."""
    return st.session_state.get("temp_interruption_count", 0)


def _get_quick_mood_rating() -> int:
    """Get quick mood rating."""
    return st.session_state.get("temp_mood_rating", 5)


def _get_quick_energy_rating() -> int:
    """Get quick energy rating."""
    return st.session_state.get("temp_energy_rating", 5)


@st.cache_data(ttl=120)  # Cache for 2 minutes (today's data changes frequently)
def _get_todays_sessions(db_manager: DatabaseManager) -> List[Dict[str, Any]]:
    """Get today's timer sessions with caching."""
    
    all_sessions = db_manager.get_timer_sessions(days=1)
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    return [
        s for s in all_sessions 
        if s.get("started_at", "").startswith(today_str)
    ]


def _calculate_avg_focus_rating(sessions: List[Dict[str, Any]]) -> float:
    """Calculate average focus rating from sessions."""
    
    ratings = [s.get("focus_rating") for s in sessions if s.get("focus_rating")]
    return sum(ratings) / len(ratings) if ratings else 0.0


def _analyze_tdah_patterns(sessions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze TDAH patterns from session data."""
    
    insights = {
        "recommendations": []
    }
    
    # Analyze focus ratings by time of day
    hourly_focus = {}
    for session in sessions:
        hour = _extract_hour_from_timestamp(session.get("started_at"))
        focus_rating = session.get("focus_rating")
        
        if hour is not None and focus_rating:
            if hour not in hourly_focus:
                hourly_focus[hour] = []
            hourly_focus[hour].append(focus_rating)
    
    if hourly_focus:
        # Find best focus time
        avg_by_hour = {h: sum(ratings)/len(ratings) for h, ratings in hourly_focus.items()}
        best_hour = max(avg_by_hour, key=avg_by_hour.get)
        insights["best_focus_time"] = f"{best_hour}:00"
        
        if avg_by_hour[best_hour] > 7:
            insights["recommendations"].append(f"Schedule important work around {best_hour}:00")
    
    # Analyze session lengths
    effective_sessions = [s for s in sessions if s.get("focus_rating", 0) >= 7]
    if effective_sessions:
        avg_duration = sum(s.get("planned_duration_minutes", 0) for s in effective_sessions) / len(effective_sessions)
        insights["avg_effective_session"] = int(avg_duration)
        
        if avg_duration < 20:
            insights["recommendations"].append("Try shorter 15-minute sessions")
        elif avg_duration > 45:
            insights["recommendations"].append("Consider breaking longer sessions with short breaks")
    
    # Interruption analysis
    recent_interruptions = [s.get("interruptions_count", 0) for s in sessions[-7:]]  # Last 7 sessions
    if recent_interruptions:
        avg_interruptions = sum(recent_interruptions) / len(recent_interruptions)
        if avg_interruptions > 3:
            insights["interruption_pattern"] = "High interruption rate"
            insights["recommendations"].append("Try using 'Do Not Disturb' mode during focus sessions")
        elif avg_interruptions < 1:
            insights["interruption_pattern"] = "Low interruption rate"
    
    return insights


def _extract_hour_from_timestamp(timestamp: Optional[str]) -> Optional[int]:
    """Extract hour from timestamp string."""
    if not timestamp:
        return None
    
    try:
        if "T" in timestamp:
            time_part = timestamp.split("T")[1]
        elif " " in timestamp:
            time_part = timestamp.split(" ")[1]
        else:
            return None
        
        hour = int(time_part.split(":")[0])
        return hour
    except (ValueError, IndexError):
        return None


if __name__ == "__main__":
    render_timer_page()