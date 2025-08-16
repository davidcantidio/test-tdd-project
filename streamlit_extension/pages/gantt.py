"""
📊 Gantt Chart Page

Visual project timeline and scheduling:
- Interactive Gantt chart visualization
- Epic and task timeline tracking
- Milestone and deadline management
- Progress tracking over time
- Resource allocation views
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

try:
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    import plotly.figure_factory as ff
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    px = go = make_subplots = ff = None

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None

# Local imports
try:
    from streamlit_extension.utils.database import DatabaseManager
    from streamlit_extension.config import load_config
    from streamlit_extension.utils.security import (
        create_safe_client, sanitize_display, validate_form, check_rate_limit,
        security_manager
    )
    DATABASE_UTILS_AVAILABLE = True
except ImportError:
    DatabaseManager = load_config = None
    create_safe_client = sanitize_display = validate_form = None
    check_rate_limit = security_manager = None
    DATABASE_UTILS_AVAILABLE = False

try:
    from gantt_tracker import GanttTracker
    GANTT_TRACKER_AVAILABLE = True
except ImportError:
    GanttTracker = None
    GANTT_TRACKER_AVAILABLE = False


def render_gantt_page():
    """Render the Gantt chart page."""
    if not STREAMLIT_AVAILABLE:
        return {"error": "Streamlit not available"}
    
    # Check rate limit for page load
    page_rate_allowed, page_rate_error = check_rate_limit("page_load") if check_rate_limit else (True, None)
    if not page_rate_allowed:
        st.error(f"🚦 {page_rate_error}")
        st.info("Please wait before reloading the page.")
        return {"error": "Rate limited"}
    
    st.title("📊 Gantt Chart - Project Timeline")
    st.markdown("---")
    
    # Check dependencies
    missing_deps = []
    if not PLOTLY_AVAILABLE:
        missing_deps.append("plotly")
    if not DATABASE_UTILS_AVAILABLE:
        missing_deps.append("database utilities")
    
    if missing_deps:
        st.error(f"❌ Missing dependencies: {', '.join(missing_deps)}")
        st.info("Install with: `pip install plotly`")
        return
    
    # Initialize database manager
    try:
        config = load_config()
        db_manager = DatabaseManager(
            framework_db_path=str(config.get_database_path()),
            timer_db_path=str(config.get_timer_database_path())
        )
    except Exception as e:
        st.error(f"❌ Database connection error: {e}")
        return
    
    # Sidebar controls
    _render_sidebar_controls()
    
    # Load data
    with st.spinner("Loading project data..."):
        gantt_data = _get_gantt_data(db_manager)
    
    if not gantt_data or not gantt_data.get("tasks"):
        st.warning("📝 No project data available for timeline view.")
        _render_data_setup_help()
        return
    
    # Render main Gantt chart
    _render_gantt_chart(gantt_data)
    
    st.markdown("---")
    
    # Render additional views
    col1, col2 = st.columns(2)
    
    with col1:
        _render_epic_timeline(gantt_data)
    
    with col2:
        _render_milestone_tracker(gantt_data)
    
    # Detailed tables
    with st.expander("📋 Detailed Timeline Data"):
        _render_timeline_tables(gantt_data)


def _render_sidebar_controls():
    """Render sidebar controls for Gantt chart customization."""
    
    st.sidebar.markdown("## 📊 Chart Settings")
    
    # View mode
    view_mode = st.sidebar.selectbox(
        "View Mode",
        ["Epic View", "Task View", "Combined View"],
        index=2  # Default to Combined
    )
    st.session_state.gantt_view_mode = view_mode
    
    # Time range
    time_range = st.sidebar.selectbox(
        "Time Range",
        ["Last 30 days", "Last 90 days", "All time", "Custom range"],
        index=1  # Default to 90 days
    )
    st.session_state.gantt_time_range = time_range
    
    if time_range == "Custom range":
        col1, col2 = st.sidebar.columns(2)
        with col1:
            start_date = st.date_input("Start Date", value=datetime.now() - timedelta(days=90))
        with col2:
            end_date = st.date_input("End Date", value=datetime.now() + timedelta(days=30))
        
        st.session_state.gantt_custom_start = start_date
        st.session_state.gantt_custom_end = end_date
    
    # Display options
    st.sidebar.markdown("## 🎨 Display Options")
    
    st.session_state.gantt_show_progress = st.sidebar.checkbox(
        "Show Progress Bars", 
        value=st.session_state.get("gantt_show_progress", True)
    )
    
    st.session_state.gantt_show_milestones = st.sidebar.checkbox(
        "Show Milestones", 
        value=st.session_state.get("gantt_show_milestones", True)
    )
    
    st.session_state.gantt_color_by = st.sidebar.selectbox(
        "Color By",
        ["Epic", "Status", "TDD Phase", "Priority"],
        index=0
    )
    
    # Grouping options
    st.sidebar.markdown("## 📁 Grouping")
    
    st.session_state.gantt_group_by = st.sidebar.selectbox(
        "Group Tasks By",
        ["Epic", "Status", "TDD Phase", "None"],
        index=0
    )


def _get_gantt_data(db_manager: DatabaseManager) -> Dict[str, Any]:
    """Get data for Gantt chart visualization."""
    
    # Try to use existing gantt_tracker first
    if GANTT_TRACKER_AVAILABLE:
        try:
            tracker = GanttTracker()
            return tracker.generate_gantt_data()
        except Exception as e:
            st.warning(f"⚠️ Gantt tracker error: {e}. Using database fallback.")
    
    # Fallback to database queries
    # Check rate limit for database read
    db_read_allowed, db_read_error = check_rate_limit("db_read") if check_rate_limit else (True, None)
    if not db_read_allowed:
        st.error(f"🚦 Database {db_read_error}")
        return {"error": "Database rate limited"}
    
    epics = db_manager.get_epics()
    tasks = db_manager.get_tasks()
    
    # Process data for Gantt chart
    gantt_tasks = []
    
    for task in tasks:
        # Calculate dates
        start_date = _parse_date(task.get("created_at"))
        end_date = _parse_date(task.get("completed_at"))
        
        # If task is not completed, estimate end date
        if not end_date:
            estimate_minutes = task.get("estimate_minutes", 60)
            if start_date:
                end_date = start_date + timedelta(minutes=estimate_minutes)
            else:
                start_date = datetime.now()
                end_date = start_date + timedelta(minutes=estimate_minutes)
        
        # Calculate progress
        progress = _calculate_task_progress(task)
        
        gantt_tasks.append({
            "id": task.get("id"),
            "title": task.get("title", "Untitled Task"),
            "epic_name": task.get("epic_name", "No Epic"),
            "epic_key": task.get("epic_key", ""),
            "status": task.get("status", "todo"),
            "tdd_phase": task.get("tdd_phase", ""),
            "priority": task.get("priority", 2),
            "start_date": start_date,
            "end_date": end_date,
            "progress": progress,
            "estimate_minutes": task.get("estimate_minutes", 60),
            "description": task.get("description", "")
        })
    
    # Process epics
    gantt_epics = []
    for epic in epics:
        # Get tasks for this epic
        epic_tasks = [t for t in gantt_tasks if t["epic_name"] == epic.get("name")]
        
        if epic_tasks:
            # Calculate epic timeline from tasks
            start_dates = [t["start_date"] for t in epic_tasks if t["start_date"]]
            end_dates = [t["end_date"] for t in epic_tasks if t["end_date"]]
            
            epic_start = min(start_dates) if start_dates else datetime.now()
            epic_end = max(end_dates) if end_dates else datetime.now()
            
            # Calculate epic progress
            epic_progress = _calculate_epic_progress(epic, epic_tasks)
            
            gantt_epics.append({
                "id": epic.get("id"),
                "name": epic.get("name", "Untitled Epic"),
                "epic_key": epic.get("epic_key", ""),
                "status": epic.get("status", "planning"),
                "start_date": epic_start,
                "end_date": epic_end,
                "progress": epic_progress,
                "points_earned": epic.get("points_earned", 0),
                "task_count": len(epic_tasks)
            })
    
    return {
        "tasks": gantt_tasks,
        "epics": gantt_epics,
        "generated_at": datetime.now()
    }


def _render_gantt_chart(gantt_data: Dict[str, Any]):
    """Render the main Gantt chart."""
    
    st.markdown("### 📊 Project Timeline")
    
    view_mode = st.session_state.get("gantt_view_mode", "Combined View")
    
    if view_mode == "Epic View":
        _render_epic_gantt(gantt_data["epics"])
    elif view_mode == "Task View":
        _render_task_gantt(gantt_data["tasks"])
    else:  # Combined View
        _render_combined_gantt(gantt_data)


def _render_epic_gantt(epics: List[Dict[str, Any]]):
    """Render Gantt chart for epics only."""
    
    if not epics or not PLOTLY_AVAILABLE:
        st.info("No epic data available for timeline view")
        return
    
    # Prepare data for Plotly
    df_data = []
    for epic in epics:
        df_data.append({
            "Task": epic["name"],
            "Start": epic["start_date"],
            "Finish": epic["end_date"],
            "Resource": epic["status"],
            "Progress": epic["progress"],
            "Description": f"Tasks: {epic['task_count']}, Points: {epic['points_earned']}"
        })
    
    if PANDAS_AVAILABLE and df_data:
        df = pd.DataFrame(df_data)
        
        # Create Gantt chart using plotly figure_factory
        try:
            fig = ff.create_gantt(
                df,
                colors=_get_status_colors(),
                index_col="Resource",
                show_colorbar=True,
                group_tasks=True,
                showgrid_x=True,
                showgrid_y=True,
                title="Epic Timeline"
            )
            
            fig.update_layout(
                height=max(400, len(epics) * 40),
                xaxis_title="Timeline",
                yaxis_title="Epics"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error rendering epic Gantt chart: {e}")
            _render_fallback_timeline(epics, "Epic")


def _render_task_gantt(tasks: List[Dict[str, Any]]):
    """Render Gantt chart for tasks only."""
    
    if not tasks or not PLOTLY_AVAILABLE:
        st.info("No task data available for timeline view")
        return
    
    # Limit to recent tasks to avoid overcrowding
    recent_tasks = sorted(tasks, key=lambda x: x["start_date"], reverse=True)[:20]
    
    # Prepare data
    df_data = []
    color_by = st.session_state.get("gantt_color_by", "Epic")
    
    for task in recent_tasks:
        color_value = task.get(color_by.lower().replace(" ", "_"), "Unknown")
        
        df_data.append({
            "Task": task["title"][:30] + ("..." if len(task["title"]) > 30 else ""),
            "Start": task["start_date"],
            "Finish": task["end_date"],
            "Resource": str(color_value),
            "Progress": task["progress"],
            "Description": f"Epic: {task['epic_name']}, Status: {task['status']}"
        })
    
    if PANDAS_AVAILABLE and df_data:
        df = pd.DataFrame(df_data)
        
        try:
            colors = _get_dynamic_colors(color_by, [task[color_by.lower().replace(" ", "_")] for task in recent_tasks])
            
            fig = ff.create_gantt(
                df,
                colors=colors,
                index_col="Resource",
                show_colorbar=True,
                group_tasks=True,
                showgrid_x=True,
                showgrid_y=True,
                title=f"Task Timeline (Recent 20, Colored by {color_by})"
            )
            
            fig.update_layout(
                height=max(600, len(recent_tasks) * 25),
                xaxis_title="Timeline",
                yaxis_title="Tasks"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error rendering task Gantt chart: {e}")
            _render_fallback_timeline(recent_tasks, "Task")


def _render_combined_gantt(gantt_data: Dict[str, Any]):
    """Render combined view with epics and key tasks."""
    
    if not PLOTLY_AVAILABLE:
        st.info("Combined view requires Plotly")
        return
    
    epics = gantt_data["epics"]
    tasks = gantt_data["tasks"]
    
    # Combine epics and priority tasks
    combined_data = []
    
    # Add epics
    for epic in epics:
        combined_data.append({
            "Task": f"📊 {epic['name']}",
            "Start": epic["start_date"],
            "Finish": epic["end_date"],
            "Resource": "Epic",
            "Progress": epic["progress"],
            "Type": "Epic",
            "Description": f"Epic: {epic['task_count']} tasks, {epic['points_earned']} points"
        })
    
    # Add high-priority or in-progress tasks
    priority_tasks = [t for t in tasks if t["priority"] == 1 or t["status"] == "in_progress"]
    priority_tasks = sorted(priority_tasks, key=lambda x: (x["priority"], x["start_date"]))[:10]
    
    for task in priority_tasks:
        combined_data.append({
            "Task": f"   └─ {task['title'][:25]}{'...' if len(task['title']) > 25 else ''}",
            "Start": task["start_date"],
            "Finish": task["end_date"],
            "Resource": task["status"],
            "Progress": task["progress"],
            "Type": "Task",
            "Description": f"Task: {task['epic_name']}, {task['status']}"
        })
    
    if PANDAS_AVAILABLE and combined_data:
        df = pd.DataFrame(combined_data)
        
        try:
            colors = {
                "Epic": "#1f77b4",
                "todo": "#ff7f0e",
                "in_progress": "#ffbb78",
                "completed": "#2ca02c"
            }
            
            fig = ff.create_gantt(
                df,
                colors=colors,
                index_col="Resource",
                show_colorbar=True,
                group_tasks=True,
                showgrid_x=True,
                showgrid_y=True,
                title="Combined Project Timeline (Epics + Priority Tasks)"
            )
            
            fig.update_layout(
                height=max(500, len(combined_data) * 30),
                xaxis_title="Timeline",
                yaxis_title="Project Items"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error rendering combined Gantt chart: {e}")
            _render_fallback_combined_timeline(gantt_data)


def _render_epic_timeline(gantt_data: Dict[str, Any]):
    """Render simplified epic timeline view."""
    
    st.markdown("### 📋 Epic Timeline Overview")
    
    epics = gantt_data["epics"]
    if not epics:
        st.info("No epics available")
        return
    
    for epic in epics[:5]:  # Show top 5 epics
        with st.container():
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.markdown(f"**{epic['name']}**")
                progress = epic["progress"]
                st.progress(progress / 100)
                
                # Timeline info
                duration = epic["end_date"] - epic["start_date"]
                st.caption(f"Duration: {duration.days} days")
            
            with col2:
                st.metric("Progress", f"{progress:.0f}%")
                st.caption(f"Status: {epic['status']}")
            
            with col3:
                st.metric("Tasks", epic["task_count"])
                st.metric("Points", epic["points_earned"])


def _render_milestone_tracker(gantt_data: Dict[str, Any]):
    """Render milestone tracking."""
    
    st.markdown("### 🎯 Milestones & Deadlines")
    
    # Calculate milestones from epics
    epics = gantt_data["epics"]
    milestones = []
    
    for epic in epics:
        if epic["status"] == "completed":
            milestones.append({
                "name": f"✅ {epic['name']} Completed",
                "date": epic["end_date"],
                "type": "completed",
                "description": f"{epic['task_count']} tasks, {epic['points_earned']} points"
            })
        else:
            milestones.append({
                "name": f"🎯 {epic['name']} Target",
                "date": epic["end_date"],
                "type": "upcoming",
                "description": f"Target completion date"
            })
    
    # Sort by date
    milestones.sort(key=lambda x: x["date"])
    
    if milestones:
        for milestone in milestones[:8]:  # Show top 8 milestones
            date_str = milestone["date"].strftime("%Y-%m-%d")
            days_diff = (milestone["date"] - datetime.now()).days
            
            if days_diff < 0:
                date_info = f"{abs(days_diff)} days ago"
                status_color = "🟢"
            elif days_diff == 0:
                date_info = "Today"
                status_color = "🟡"
            else:
                date_info = f"In {days_diff} days"
                status_color = "🔴" if days_diff <= 7 else "🔵"
            
            with st.container():
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"{status_color} **{milestone['name']}**")
                    st.caption(milestone["description"])
                
                with col2:
                    st.markdown(f"**{date_str}**")
                    st.caption(date_info)
    else:
        st.info("No milestones available")


def _render_timeline_tables(gantt_data: Dict[str, Any]):
    """Render detailed timeline tables."""
    
    tab1, tab2 = st.tabs(["📊 Epic Timeline", "📋 Task Timeline"])
    
    with tab1:
        epics = gantt_data["epics"]
        if epics and PANDAS_AVAILABLE:
            epic_df = pd.DataFrame([
                {
                    "Epic": epic["name"],
                    "Status": epic["status"],
                    "Start": epic["start_date"].strftime("%Y-%m-%d"),
                    "End": epic["end_date"].strftime("%Y-%m-%d"),
                    "Progress": f"{epic['progress']:.1f}%",
                    "Tasks": epic["task_count"],
                    "Points": epic["points_earned"]
                }
                for epic in epics
            ])
            st.dataframe(epic_df, use_container_width=True)
        else:
            st.info("No epic timeline data available")
    
    with tab2:
        tasks = gantt_data["tasks"][:20]  # Limit to recent 20 tasks
        if tasks and PANDAS_AVAILABLE:
            task_df = pd.DataFrame([
                {
                    "Task": task["title"],
                    "Epic": task["epic_name"],
                    "Status": task["status"],
                    "TDD Phase": task["tdd_phase"] or "N/A",
                    "Start": task["start_date"].strftime("%Y-%m-%d"),
                    "End": task["end_date"].strftime("%Y-%m-%d"),
                    "Progress": f"{task['progress']:.1f}%",
                    "Estimate": f"{task['estimate_minutes']}min"
                }
                for task in tasks
            ])
            st.dataframe(task_df, use_container_width=True)
        else:
            st.info("No task timeline data available")


def _render_data_setup_help():
    """Render help for setting up timeline data."""
    
    st.info("""
    📋 **Timeline Setup Help**
    
    To see project timelines, you need:
    1. **Epics** with tasks assigned
    2. **Tasks** with creation dates
    3. **Time estimates** for better planning
    
    **Quick Start:**
    - Create epics in your epics/ directory
    - Add tasks with estimates
    - Use the timer to track actual progress
    """)
    
    if st.button("🔄 Refresh Data"):
        # Check rate limit for form submission
        rate_allowed, rate_error = check_rate_limit("form_submit") if check_rate_limit else (True, None)
        if not rate_allowed:
            st.error(f"🚦 {rate_error}")
            return
        
        st.rerun()


def _render_fallback_timeline(items: List[Dict[str, Any]], item_type: str):
    """Render fallback timeline view when Gantt chart fails."""
    
    st.markdown(f"### 📋 {item_type} Timeline (Simplified)")
    
    for item in items[:10]:  # Show top 10 items
        name = item.get("name", item.get("title", "Unknown"))
        start_date = item["start_date"].strftime("%Y-%m-%d")
        end_date = item["end_date"].strftime("%Y-%m-%d")
        progress = item.get("progress", 0)
        
        with st.container():
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.markdown(f"**{name}**")
                st.progress(progress / 100)
            
            with col2:
                st.markdown(f"**Start:** {start_date}")
                st.markdown(f"**End:** {end_date}")
            
            with col3:
                st.metric("Progress", f"{progress:.0f}%")


def _render_fallback_combined_timeline(gantt_data: Dict[str, Any]):
    """Render fallback combined timeline."""
    
    st.markdown("### 📊 Combined Timeline (Simplified)")
    
    # Show epics first
    epics = gantt_data["epics"][:3]  # Top 3 epics
    tasks = gantt_data["tasks"][:5]  # Top 5 tasks
    
    st.markdown("#### 📊 Epics")
    for epic in epics:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**{epic['name']}**")
            st.progress(epic["progress"] / 100)
        with col2:
            st.metric("Tasks", epic["task_count"])
    
    st.markdown("#### 📋 Priority Tasks")
    for task in tasks:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**{task['title']}**")
            st.caption(f"Epic: {task['epic_name']}")
        with col2:
            st.metric("Status", task["status"])


# Helper functions

def _parse_date(date_string: Optional[str]) -> Optional[datetime]:
    """Parse date string into datetime object."""
    if not date_string:
        return None
    
    try:
        # Try different date formats
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%m/%d/%Y"
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_string, fmt)
            except ValueError:
                continue
        
        return None
    except Exception:
        return None


def _calculate_task_progress(task: Dict[str, Any]) -> float:
    """Calculate task progress percentage."""
    status = task.get("status", "todo")
    
    if status == "completed":
        return 100.0
    elif status == "in_progress":
        return 50.0
    else:
        return 0.0


def _calculate_epic_progress(epic: Dict[str, Any], epic_tasks: List[Dict[str, Any]]) -> float:
    """Calculate epic progress from its tasks."""
    if not epic_tasks:
        return 0.0
    
    total_progress = sum(task["progress"] for task in epic_tasks)
    return total_progress / len(epic_tasks)


def _get_status_colors() -> Dict[str, str]:
    """Get color mapping for status values."""
    return {
        "planning": "#FFA500",
        "active": "#1E90FF",
        "completed": "#32CD32",
        "on_hold": "#FFD700",
        "cancelled": "#DC143C",
        "todo": "#FF7F50",
        "in_progress": "#FFD700"
    }


def _get_dynamic_colors(color_by: str, values: List[Any]) -> Dict[str, str]:
    """Generate dynamic color mapping based on unique values."""
    unique_values = list(set(str(v) for v in values))
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2", "#7f7f7f"]
    
    color_map = {}
    for i, value in enumerate(unique_values):
        color_map[value] = colors[i % len(colors)]
    
    return color_map


if __name__ == "__main__":
    render_gantt_page()