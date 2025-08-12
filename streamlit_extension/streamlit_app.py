#!/usr/bin/env python3
"""
🚀 TDD Framework - Streamlit Interface

Main Streamlit application providing:
- Interactive timer with TDAH support
- Task management and Kanban board  
- Analytics dashboards
- Epic progress tracking
- Gamification system
- GitHub Projects V2 integration
"""

import sys
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Graceful imports
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    print("❌ Streamlit not available. Install with: pip install streamlit")
    sys.exit(1)

# Configure page
st.set_page_config(
    page_title="TDD Framework",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': 'https://github.com/davidcantidio/test-tdd-project/issues',
        'About': """
        # TDD Framework - Streamlit Interface
        
        Interactive development environment for TDD workflow with:
        - ⏱️ Focus timer with TDAH support
        - 📋 Task management
        - 📊 Analytics dashboards  
        - 🎮 Gamification system
        - 🐙 GitHub integration
        
        **Version:** 1.0.0
        **Phase:** 1.2 Development
        """
    }
)

# Import components
try:
    from streamlit_extension.components.sidebar import render_sidebar
    from streamlit_extension.components.timer import TimerComponent
    from streamlit_extension.utils.database import DatabaseManager
    from streamlit_extension.config import get_config, load_config
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


def render_main_header():
    """Render the main application header."""
    col1, col2, col3 = st.columns([2, 3, 1])
    
    with col1:
        st.title("🚀 TDD Framework")
    
    with col2:
        # Quick stats
        db_manager = st.session_state.db_manager
        stats = db_manager.get_user_stats()
        
        st.metric(
            label="Tasks Completed",
            value=stats.get("completed_tasks", 0),
            delta=1 if stats.get("completed_tasks", 0) > 0 else None
        )
    
    with col3:
        # Health indicator
        health = st.session_state.db_health_check
        if health["framework_db_connected"]:
            st.success("🟢 Connected")
        else:
            st.error("🔴 DB Error")


def render_main_content():
    """Render the main content area."""
    
    # Main dashboard content
    st.markdown("## 🏠 Dashboard")
    
    # Check database connectivity
    health = st.session_state.db_health_check
    if not health["framework_db_connected"]:
        st.error("❌ **Database Connection Error**")
        st.error("Cannot connect to framework.db. Please check:")
        st.code("python database_maintenance.py health")
        
        with st.expander("🔧 Database Health Details"):
            st.json(health)
        
        st.stop()
    
    # Timer section
    st.markdown("### ⏱️ Focus Timer")
    
    timer_component = st.session_state.timer_component
    timer_state = timer_component.render()
    
    # Show timer summary
    if timer_state.get("current_session"):
        session_type = timer_state["session_type"].replace("_", " ").title()
        st.info(f"🎯 Active {session_type} Session - {timer_state['elapsed_minutes']} minutes elapsed")
    
    # Epic progress section
    st.markdown("### 📊 Epic Progress")
    
    db_manager = st.session_state.db_manager
    epics = db_manager.get_epics()
    
    if epics:
        # Show top 3 active epics
        active_epics = [e for e in epics if e.get("status") != "completed"][:3]
        
        for epic in active_epics:
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.markdown(f"**{epic['name']}**")
                    st.caption(f"Key: {epic['epic_key']}")
                
                with col2:
                    # Get progress for this epic
                    progress = db_manager.get_epic_progress(epic['id'])
                    progress_pct = progress.get("progress_percentage", 0)
                    st.progress(progress_pct / 100)
                    st.caption(f"{progress_pct:.1f}%")
                
                with col3:
                    points = epic.get("points_earned", 0)
                    st.metric("Points", points)
    else:
        st.info("📝 No epics found. Create your first epic to get started!")
        
        if st.button("🔄 Refresh Data"):
            st.rerun()
    
    # Recent tasks section
    st.markdown("### 📋 Recent Tasks")
    
    tasks = db_manager.get_tasks()
    if tasks:
        # Show last 5 tasks
        recent_tasks = tasks[:5]
        
        for task in recent_tasks:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                
                with col1:
                    st.markdown(f"**{task['title']}**")
                    st.caption(f"Epic: {task['epic_name']}")
                
                with col2:
                    status_colors = {
                        "todo": "🔴",
                        "in_progress": "🟡", 
                        "completed": "🟢"
                    }
                    status = task.get("status", "todo")
                    st.markdown(f"{status_colors.get(status, '⚪')} {status.title()}")
                
                with col3:
                    tdd_phase = task.get("tdd_phase", "")
                    if tdd_phase:
                        phase_colors = {
                            "red": "🔴",
                            "green": "🟢", 
                            "refactor": "🔵"
                        }
                        st.markdown(f"{phase_colors.get(tdd_phase, '⚪')} {tdd_phase.title()}")
                
                with col4:
                    estimate = task.get("estimate_minutes", 0)
                    if estimate:
                        st.caption(f"{estimate}min")
    else:
        st.info("📝 No tasks found. Tasks will appear here once you create them.")
    
    # Quick actions
    st.markdown("### ⚡ Quick Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📊 View Analytics", use_container_width=True):
            st.info("📈 Analytics page coming in Task 1.2.4")
    
    with col2:
        if st.button("📋 Task Board", use_container_width=True):
            st.info("🔄 Kanban board coming in Task 1.2.5")
    
    with col3:
        if st.button("📈 Gantt Chart", use_container_width=True):
            st.info("📊 Gantt view coming in Task 1.2.6")
    
    with col4:
        if st.button("🐙 Sync GitHub", use_container_width=True):
            config = st.session_state.config
            if config.is_github_configured():
                st.info("🔄 GitHub sync coming in Task 1.2.8")
            else:
                st.warning("⚠️ GitHub not configured")


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


def main():
    """Main application entry point."""
    
    # Initialize session state
    initialize_session_state()
    
    # Render sidebar
    sidebar_state = render_sidebar()
    
    # Main content area
    with st.container():
        # Header
        render_main_header()
        
        # Main content
        render_main_content()
        
        # Debug panel
        render_debug_panel()
    
    # Footer
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.caption("🚀 TDD Framework v1.0.0")
    
    with col2:
        st.caption("📍 Phase 1.2 - Streamlit Interface")
    
    with col3:
        if st.button("🔄 Refresh", key="footer_refresh"):
            st.rerun()


if __name__ == "__main__":
    main()