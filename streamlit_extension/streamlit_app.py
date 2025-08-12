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
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Graceful imports
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    # Graceful fallback for testing and development
    print("⚠️ Streamlit not available - running in headless mode")
    print("To run the dashboard: pip install streamlit")
    STREAMLIT_AVAILABLE = False
    
    # Mock streamlit module for testing
    class MockStreamlit:
        def __getattr__(self, name):
            def mock_func(*args, **kwargs):
                return None
            return mock_func
    
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
    from streamlit_extension.config import load_config, load_config
except ImportError as e:
    st.error(f"❌ Import Error: {e}")
    st.error("Make sure to run from the project root directory")
    st.stop()


def initialize_session_state():
    """Initialize Streamlit session state variables."""
    
    # Core app state
    if "config" not in st.session_state:
        try:
            st.session_state.config = load_config()
        except Exception as e:
            st.error(f"❌ Configuration Error: {e}")
            st.stop()
    
    if "db_manager" not in st.session_state:
        config = st.session_state.config
        st.session_state.db_manager = DatabaseManager(
            framework_db_path=str(config.get_database_path()),
            timer_db_path=str(config.get_timer_database_path())
        )
    
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
        st.session_state.db_health_check = st.session_state.db_manager.check_database_health()
    
    # Dashboard preferences
    if "dashboard_view_mode" not in st.session_state:
        st.session_state.dashboard_view_mode = "default"
    
    # Notifications
    if "notifications_shown" not in st.session_state:
        st.session_state.notifications_shown = set()


def render_enhanced_header():
    """Render the enhanced main application header with welcome message and quick stats."""
    
    # Welcome header with dynamic greeting
    WelcomeHeader.render(username="Developer")
    
    # Daily statistics bar
    db_manager = st.session_state.db_manager
    daily_stats = db_manager.get_daily_summary()
    DailyStats.render(daily_stats)
    
    # Separator
    st.markdown("---")


def render_productivity_overview():
    """Render productivity overview section with heatmap and metrics."""
    
    st.markdown("## 📊 Productivity Overview")
    
    db_manager = st.session_state.db_manager
    productivity_stats = db_manager.get_productivity_stats(days=7)
    
    # Create three columns for productivity metrics
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        # Activity heatmap
        st.markdown("### 📈 Weekly Activity")
        ProductivityHeatmap.render(
            activity_data=productivity_stats.get("activity_by_date", {}),
            title="Tasks Completed",
            height=120
        )
    
    with col2:
        # Task completion rate
        st.markdown("### ✅ Completion Rate")
        avg_tasks = productivity_stats.get("average_daily_tasks", 0)
        target_tasks = 5  # Daily target
        completion_rate = min(1.0, avg_tasks / target_tasks) if target_tasks > 0 else 0
        
        ProgressRing.render(
            progress=completion_rate,
            label="Daily Average",
            size="medium",
            color="#00CC88"
        )
    
    with col3:
        # Focus time metrics
        st.markdown("### ⏱️ Focus Time")
        focus_time = productivity_stats.get("focus_time_total", 0)
        
        # Mini sparkline of focus time trend
        # For demo, create sample data
        focus_trend = [30, 45, 60, 55, 70, 65, focus_time // 7]
        SparklineChart.render(
            data=focus_trend,
            color="#FF6B6B",
            show_points=True,
            height=80
        )
        
        st.metric(
            label="Total This Week",
            value=f"{focus_time // 60}h {focus_time % 60}m",
            delta="On track" if focus_time >= 600 else "Below target"
        )


def render_timer_and_current_task():
    """Render timer component and current task info."""
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### ⏱️ Focus Timer")
        timer_component = st.session_state.timer_component
        timer_state = timer_component.render()
    
    with col2:
        st.markdown("### 📌 Current Focus")
        
        # Get current task if any
        db_manager = st.session_state.db_manager
        tasks = db_manager.get_tasks()
        in_progress = [t for t in tasks if t.get("status") == "in_progress"]
        
        if in_progress:
            current_task = in_progress[0]
            st.info(f"**{current_task['title']}**")
            st.caption(f"Epic: {current_task.get('epic_name', 'None')}")
            
            # TDD phase indicator
            tdd_phase = current_task.get("tdd_phase", "")
            if tdd_phase:
                phase_colors = {"red": "🔴", "green": "🟢", "refactor": "🔵"}
                st.markdown(f"TDD Phase: {phase_colors.get(tdd_phase, '⚪')} **{tdd_phase.title()}**")
        else:
            st.info("No task in progress. Start a new task to begin tracking!")
            
            # Quick task selector
            all_tasks = [t for t in tasks if t.get("status") == "todo"][:5]
            if all_tasks:
                task_options = ["Select a task..."] + [t["title"] for t in all_tasks]
                selected = st.selectbox("Quick start:", task_options)
                
                if selected != "Select a task...":
                    if st.button("▶️ Start Task"):
                        st.success(f"Started: {selected}")
                        st.rerun()


def render_enhanced_epic_cards():
    """Render enhanced epic progress cards with visualizations."""
    
    st.markdown("### 🎯 Epic Progress")
    
    db_manager = st.session_state.db_manager
    epics = db_manager.get_epics()
    
    if not epics:
        st.info("📝 No epics found. Create your first epic to get started!")
        return
    
    # Show top 3 active epics
    active_epics = [e for e in epics if e.get("status") != "completed"][:3]
    
    for epic in active_epics:
        with st.expander(f"**{epic['name']}** - {epic['epic_key']}", expanded=True):
            # Progress metrics
            progress = db_manager.get_epic_progress(epic['id'])
            progress_pct = progress.get("progress_percentage", 0) / 100
            
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            
            with col1:
                st.markdown(f"**Description:** {epic.get('description', 'No description')}")
                
                # Progress bar with custom styling
                st.progress(progress_pct)
                st.caption(f"Progress: {progress_pct*100:.1f}%")
            
            with col2:
                # Tasks breakdown
                total_tasks = progress.get("total_tasks", 0)
                completed_tasks = progress.get("completed_tasks", 0)
                
                st.metric(
                    label="Tasks",
                    value=f"{completed_tasks}/{total_tasks}",
                    delta=f"{total_tasks - completed_tasks} remaining"
                )
            
            with col3:
                # Points earned
                points = epic.get("points_earned", 0)
                st.metric(
                    label="Points",
                    value=points,
                    delta="+10" if points > 0 else None
                )
            
            with col4:
                # Difficulty indicator
                difficulty = epic.get("difficulty_level", 1)
                difficulty_stars = "⭐" * min(5, difficulty)
                st.markdown(f"**Difficulty**")
                st.markdown(difficulty_stars)
            
            # Mini burndown chart (simplified)
            if progress.get("daily_progress"):
                st.markdown("**Burndown Trend**")
                burndown_data = [100, 85, 70, 60, 45, 30, (1-progress_pct)*100]
                SparklineChart.render(
                    data=burndown_data,
                    color="#4CAF50",
                    show_points=False,
                    height=60
                )


def render_notifications_panel():
    """Render notifications panel with alerts and reminders."""
    
    st.markdown("### 🔔 Notifications & Alerts")
    
    db_manager = st.session_state.db_manager
    notifications = db_manager.get_pending_notifications()
    
    if notifications:
        for notif in notifications[:3]:  # Show max 3 notifications
            notif_id = f"{notif['type']}_{notif['title']}_{notif['timestamp']}"
            
            if notif_id not in st.session_state.notifications_shown:
                notification = NotificationData(
                    title=notif['title'],
                    message=notif['message'],
                    type=notif['type'],
                    timestamp=notif['timestamp']
                )
                NotificationToast.show(notification)
                st.session_state.notifications_shown.add(notif_id)
    else:
        st.success("✨ All clear! No pending notifications.")


def render_gamification_widget():
    """Render gamification widget with achievements and points."""
    
    st.markdown("### 🎮 Achievements & Progress")
    
    db_manager = st.session_state.db_manager
    achievements = db_manager.get_user_achievements(limit=6)
    daily_summary = db_manager.get_daily_summary()
    
    # Points and level display
    col1, col2 = st.columns([1, 2])
    
    with col1:
        total_points = daily_summary.get("points_earned_today", 0)
        st.metric(
            label="🏆 Points Today",
            value=total_points,
            delta=f"+{total_points}" if total_points > 0 else None
        )
        
        # Level progress (simplified)
        level = (total_points // 100) + 1
        progress_to_next = (total_points % 100) / 100
        
        st.markdown(f"**Level {level}**")
        st.progress(progress_to_next)
        st.caption(f"{int(progress_to_next * 100)}% to Level {level + 1}")
    
    with col2:
        # Recent achievements
        st.markdown("**Recent Achievements**")
        
        if achievements:
            # Show first 3 achievements
            for achievement in achievements[:3]:
                AchievementCard.render(
                    title=achievement['name'],
                    description=achievement['description'],
                    icon=achievement['icon'],
                    unlocked=achievement['unlocked'],
                    progress=achievement.get('progress')
                )
        else:
            st.info("🎯 Complete tasks to unlock achievements!")


def render_quick_actions():
    """Render quick action buttons grid."""
    
    st.markdown("### ⚡ Quick Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        QuickActionButton.render(
            label="New Task",
            icon="➕",
            callback=lambda: st.session_state.update({"show_create_task": True}),
            color="primary",
            tooltip="Create a new task"
        )
    
    with col2:
        QuickActionButton.render(
            label="Analytics",
            icon="📊",
            callback=lambda: st.session_state.update({"current_page": "Analytics"}),
            color="success",
            tooltip="View detailed analytics"
        )
    
    with col3:
        QuickActionButton.render(
            label="Kanban",
            icon="📋",
            callback=lambda: st.session_state.update({"current_page": "Kanban"}),
            color="warning",
            tooltip="Open Kanban board"
        )
    
    with col4:
        config = st.session_state.config
        if config.is_github_configured():
            QuickActionButton.render(
                label="Sync",
                icon="🔄",
                callback=lambda: st.info("GitHub sync coming soon!"),
                color="secondary",
                tooltip="Sync with GitHub"
            )
        else:
            QuickActionButton.render(
                label="Settings",
                icon="⚙️",
                callback=lambda: st.session_state.update({"current_page": "Settings"}),
                color="secondary",
                tooltip="Configure settings"
            )


def render_recent_activity():
    """Render recent activity feed."""
    
    st.markdown("### 📋 Recent Activity")
    
    db_manager = st.session_state.db_manager
    tasks = db_manager.get_tasks()
    
    if tasks:
        # Show last 5 tasks with activity
        recent_tasks = tasks[:5]
        
        for task in recent_tasks:
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                status_emoji = {
                    "todo": "📝",
                    "in_progress": "🔄",
                    "completed": "✅"
                }.get(task.get("status", "todo"), "⚪")
                
                st.markdown(f"{status_emoji} **{task['title']}**")
                st.caption(f"Epic: {task.get('epic_name', 'None')}")
            
            with col2:
                tdd_phase = task.get("tdd_phase", "")
                if tdd_phase:
                    phase_colors = {"red": "🔴", "green": "🟢", "refactor": "🔵"}
                    st.caption(f"TDD: {phase_colors.get(tdd_phase, '⚪')} {tdd_phase}")
            
            with col3:
                if task.get("updated_at"):
                    st.caption(f"Updated: {task['updated_at'][:10]}")
    else:
        st.info("No recent activity. Start working on tasks to see them here!")


def render_debug_panel():
    """Render debug information panel."""
    if not st.session_state.show_debug_info:
        return
    
    with st.expander("🔧 Debug Information"):
        st.markdown("#### Configuration")
        config = st.session_state.config
        debug_config = {
            "streamlit_port": config.streamlit_port,
            "database_url": config.database_url,
            "timer_database_url": config.timer_database_url,
            "timezone": config.timezone,
            "enable_gamification": config.enable_gamification,
            "github_configured": config.is_github_configured()
        }
        st.json(debug_config)
        
        st.markdown("#### Database Health")
        st.json(st.session_state.db_health_check)
        
        st.markdown("#### Session State Keys")
        st.write(list(st.session_state.keys()))
        
        st.markdown("#### Cache Statistics")
        cache_stats = st.session_state.db_manager.get_cache_stats()
        st.json(cache_stats)


def main():
    """Main application entry point with enhanced dashboard."""
    
    # Check if running in headless mode
    if not STREAMLIT_AVAILABLE:
        print("📊 Dashboard functions available for testing")
        print("Run 'streamlit run streamlit_app.py' for full UI")
        return
    
    # Initialize session state
    initialize_session_state()
    
    # Check database connectivity
    health = st.session_state.db_health_check
    if not health["framework_db_connected"]:
        st.error("❌ **Database Connection Error**")
        st.error("Cannot connect to framework.db. Please check:")
        st.code("python database_maintenance.py health")
        
        with st.expander("🔧 Database Health Details"):
            st.json(health)
        
        st.stop()
    
    # Render sidebar
    sidebar_state = render_sidebar()
    
    # Main content area with enhanced dashboard
    with st.container():
        # Enhanced header with welcome and quick stats
        render_enhanced_header()
        
        # Productivity overview section
        render_productivity_overview()
        
        st.markdown("---")
        
        # Timer and current task in two columns
        render_timer_and_current_task()
        
        st.markdown("---")
        
        # Enhanced epic progress cards
        render_enhanced_epic_cards()
        
        st.markdown("---")
        
        # Two column layout for notifications and gamification
        col1, col2 = st.columns([1, 1])
        
        with col1:
            render_notifications_panel()
        
        with col2:
            render_gamification_widget()
        
        st.markdown("---")
        
        # Quick actions bar
        render_quick_actions()
        
        st.markdown("---")
        
        # Recent activity feed
        render_recent_activity()
        
        # Debug panel (if enabled)
        render_debug_panel()
    
    # Footer with enhanced information
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.caption("🚀 TDD Framework v1.2.1")
    
    with col2:
        st.caption("📍 Enhanced Dashboard")
    
    with col3:
        st.caption(f"🕐 {datetime.now().strftime('%H:%M:%S')}")
    
    with col4:
        if st.button("🔄 Refresh", key="footer_refresh"):
            st.rerun()


if __name__ == "__main__":
    main()