"""
📊 Analytics Dashboard Page

Displays comprehensive analytics and metrics for TDD development:
- Productivity metrics and trends
- Focus time analysis
- TDAH-specific insights
- Epic and task completion statistics
- Performance over time
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
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    px = go = make_subplots = None

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None

# Local imports
try:
    from streamlit_extension.utils.database import DatabaseManager
    from streamlit_extension.config import get_config
    DATABASE_UTILS_AVAILABLE = True
except ImportError:
    DatabaseManager = get_config = None
    DATABASE_UTILS_AVAILABLE = False

try:
    from tdah_tools.analytics_engine import AnalyticsEngine
    ANALYTICS_ENGINE_AVAILABLE = True
except ImportError:
    AnalyticsEngine = None
    ANALYTICS_ENGINE_AVAILABLE = False


def render_analytics_page():
    """Render the analytics dashboard page."""
    if not STREAMLIT_AVAILABLE:
        return {"error": "Streamlit not available"}
    
    st.title("📊 Analytics Dashboard")
    st.markdown("---")
    
    # Check if required dependencies are available
    missing_deps = []
    if not PLOTLY_AVAILABLE:
        missing_deps.append("plotly")
    if not PANDAS_AVAILABLE:
        missing_deps.append("pandas")
    if not DATABASE_UTILS_AVAILABLE:
        missing_deps.append("database utilities")
    
    if missing_deps:
        st.error(f"❌ Missing dependencies: {', '.join(missing_deps)}")
        st.info("Install with: `pip install plotly pandas`")
        return
    
    # Initialize database manager
    try:
        config = get_config()
        db_manager = DatabaseManager(
            framework_db_path=str(config.get_database_path()),
            timer_db_path=str(config.get_timer_database_path())
        )
    except Exception as e:
        st.error(f"❌ Database connection error: {e}")
        return
    
    # Time range selector
    st.sidebar.markdown("## 📅 Time Range")
    time_options = {
        "Last 7 days": 7,
        "Last 30 days": 30,
        "Last 90 days": 90,
        "All time": 365
    }
    selected_range = st.sidebar.selectbox("Select time range", list(time_options.keys()))
    days = time_options[selected_range]
    
    # Fetch data
    with st.spinner("Loading analytics data..."):
        analytics_data = _get_analytics_data(db_manager, days)
    
    if not analytics_data:
        st.warning("📝 No data available for the selected time range.")
        return
    
    # Overview metrics
    _render_overview_metrics(analytics_data)
    
    st.markdown("---")
    
    # Charts in columns
    col1, col2 = st.columns(2)
    
    with col1:
        _render_productivity_chart(analytics_data)
        _render_tdd_phase_distribution(analytics_data)
    
    with col2:
        _render_focus_time_chart(analytics_data)
        _render_epic_progress_chart(analytics_data)
    
    st.markdown("---")
    
    # TDAH-specific analytics
    _render_tdah_insights(analytics_data)
    
    # Detailed tables
    with st.expander("📋 Detailed Data"):
        _render_detailed_tables(analytics_data)


def _get_analytics_data(db_manager: DatabaseManager, days: int) -> Dict[str, Any]:
    """Get analytics data from database and analytics engine."""
    
    # Try to use analytics engine first
    if ANALYTICS_ENGINE_AVAILABLE:
        try:
            engine = AnalyticsEngine()
            return engine.generate_productivity_report(days)
        except Exception as e:
            st.warning(f"⚠️ Analytics engine error: {e}. Using fallback data.")
    
    # Fallback to database queries
    timer_sessions = db_manager.get_timer_sessions(days)
    epics = db_manager.get_epics()
    tasks = db_manager.get_tasks()
    user_stats = db_manager.get_user_stats()
    
    # Calculate basic metrics
    total_focus_time = sum(s.get("planned_duration_minutes", 0) for s in timer_sessions)
    completed_tasks = [t for t in tasks if t.get("status") == "completed"]
    
    # Focus ratings analysis
    focus_ratings = [s.get("focus_rating") for s in timer_sessions if s.get("focus_rating")]
    avg_focus = sum(focus_ratings) / len(focus_ratings) if focus_ratings else 0
    
    # Daily productivity
    daily_data = _calculate_daily_metrics(timer_sessions, tasks)
    
    return {
        "period_days": days,
        "total_sessions": len(timer_sessions),
        "total_focus_time": total_focus_time,
        "completed_tasks": len(completed_tasks),
        "average_focus_rating": avg_focus,
        "total_points": user_stats.get("total_points", 0),
        "active_epics": len([e for e in epics if e.get("status") == "active"]),
        "timer_sessions": timer_sessions,
        "epics": epics,
        "tasks": tasks,
        "daily_metrics": daily_data
    }


def _calculate_daily_metrics(timer_sessions: List[Dict], tasks: List[Dict]) -> List[Dict]:
    """Calculate daily productivity metrics."""
    from collections import defaultdict
    
    daily_data = defaultdict(lambda: {
        "date": "",
        "focus_minutes": 0,
        "sessions": 0,
        "tasks_completed": 0,
        "avg_focus_rating": 0,
        "interruptions": 0
    })
    
    # Process timer sessions
    for session in timer_sessions:
        if not session.get("started_at"):
            continue
        
        try:
            date_str = session["started_at"][:10]  # YYYY-MM-DD
            daily_data[date_str]["date"] = date_str
            daily_data[date_str]["focus_minutes"] += session.get("planned_duration_minutes", 0)
            daily_data[date_str]["sessions"] += 1
            daily_data[date_str]["interruptions"] += session.get("interruptions_count", 0)
            
            # Focus rating
            if session.get("focus_rating"):
                current_avg = daily_data[date_str]["avg_focus_rating"]
                sessions_count = daily_data[date_str]["sessions"]
                new_avg = ((current_avg * (sessions_count - 1)) + session["focus_rating"]) / sessions_count
                daily_data[date_str]["avg_focus_rating"] = new_avg
        except (KeyError, IndexError, ValueError):
            continue
    
    # Process completed tasks
    for task in tasks:
        if task.get("status") == "completed" and task.get("completed_at"):
            try:
                date_str = task["completed_at"][:10]
                if date_str in daily_data:
                    daily_data[date_str]["tasks_completed"] += 1
            except (KeyError, IndexError):
                continue
    
    return list(daily_data.values())


def _render_overview_metrics(analytics_data: Dict[str, Any]):
    """Render overview metrics cards."""
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_time = analytics_data.get("total_focus_time", 0)
        hours = total_time // 60
        minutes = total_time % 60
        st.metric(
            "🕐 Total Focus Time",
            f"{hours}h {minutes}m",
            f"{analytics_data.get('total_sessions', 0)} sessions"
        )
    
    with col2:
        completed = analytics_data.get("completed_tasks", 0)
        avg_per_day = completed / analytics_data.get("period_days", 1) if completed > 0 else 0
        st.metric(
            "✅ Tasks Completed",
            completed,
            f"{avg_per_day:.1f}/day avg"
        )
    
    with col3:
        focus_rating = analytics_data.get("average_focus_rating", 0)
        st.metric(
            "🎯 Avg Focus Rating",
            f"{focus_rating:.1f}/10",
            "TDAH metric"
        )
    
    with col4:
        points = analytics_data.get("total_points", 0)
        st.metric(
            "🌟 Total Points",
            f"{points:,}",
            f"{analytics_data.get('active_epics', 0)} active epics"
        )


def _render_productivity_chart(analytics_data: Dict[str, Any]):
    """Render productivity over time chart."""
    if not PLOTLY_AVAILABLE:
        st.warning("Charts require plotly installation")
        return
    
    st.markdown("### 📈 Daily Productivity")
    
    daily_metrics = analytics_data.get("daily_metrics", [])
    if not daily_metrics:
        st.info("No daily data available")
        return
    
    # Sort by date
    daily_metrics.sort(key=lambda x: x["date"])
    
    if PANDAS_AVAILABLE:
        df = pd.DataFrame(daily_metrics)
        
        # Create subplot with secondary y-axis
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        # Add focus time bar chart
        fig.add_trace(
            go.Bar(
                x=df["date"],
                y=df["focus_minutes"],
                name="Focus Minutes",
                marker_color="lightblue",
                opacity=0.7
            ),
            secondary_y=False
        )
        
        # Add tasks completed line
        fig.add_trace(
            go.Scatter(
                x=df["date"],
                y=df["tasks_completed"],
                mode="lines+markers",
                name="Tasks Completed",
                line=dict(color="orange", width=2),
                marker=dict(size=6)
            ),
            secondary_y=True
        )
        
        # Update axes
        fig.update_xaxes(title_text="Date")
        fig.update_yaxes(title_text="Focus Minutes", secondary_y=False)
        fig.update_yaxes(title_text="Tasks Completed", secondary_y=True)
        
        fig.update_layout(
            height=400,
            showlegend=True,
            title=None
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        # Fallback display
        st.json(daily_metrics[:5])  # Show first 5 days


def _render_focus_time_chart(analytics_data: Dict[str, Any]):
    """Render focus time analysis chart."""
    if not PLOTLY_AVAILABLE:
        st.warning("Charts require plotly installation")
        return
    
    st.markdown("### ⏱️ Focus Time Analysis")
    
    timer_sessions = analytics_data.get("timer_sessions", [])
    if not timer_sessions:
        st.info("No timer sessions available")
        return
    
    # Group by hour of day
    from collections import defaultdict
    hourly_data = defaultdict(int)
    
    for session in timer_sessions:
        if session.get("started_at"):
            try:
                # Extract hour from timestamp
                if "T" in session["started_at"]:
                    hour = int(session["started_at"].split("T")[1][:2])
                else:
                    hour = int(session["started_at"].split(" ")[1][:2])
                
                hourly_data[hour] += session.get("planned_duration_minutes", 0)
            except (ValueError, IndexError):
                continue
    
    if hourly_data:
        hours = list(range(24))
        minutes = [hourly_data.get(h, 0) for h in hours]
        
        fig = px.bar(
            x=hours,
            y=minutes,
            title="Focus Time by Hour of Day",
            labels={"x": "Hour", "y": "Minutes"},
            color=minutes,
            color_continuous_scale="Blues"
        )
        
        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)


def _render_tdd_phase_distribution(analytics_data: Dict[str, Any]):
    """Render TDD phase distribution."""
    if not PLOTLY_AVAILABLE:
        st.warning("Charts require plotly installation")
        return
    
    st.markdown("### 🔴🟢🔵 TDD Phase Distribution")
    
    tasks = analytics_data.get("tasks", [])
    if not tasks:
        st.info("No task data available")
        return
    
    # Count tasks by TDD phase
    phase_counts = {"red": 0, "green": 0, "refactor": 0, "unknown": 0}
    
    for task in tasks:
        phase = task.get("tdd_phase", "unknown").lower()
        if phase in phase_counts:
            phase_counts[phase] += 1
        else:
            phase_counts["unknown"] += 1
    
    # Remove zero counts
    phase_counts = {k: v for k, v in phase_counts.items() if v > 0}
    
    if phase_counts:
        colors = {
            "red": "#FF6B6B",
            "green": "#51CF66",
            "refactor": "#339AF0",
            "unknown": "#ADB5BD"
        }
        
        fig = px.pie(
            values=list(phase_counts.values()),
            names=list(phase_counts.keys()),
            title="Tasks by TDD Phase",
            color_discrete_map=colors
        )
        
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)


def _render_epic_progress_chart(analytics_data: Dict[str, Any]):
    """Render epic progress overview."""
    if not PLOTLY_AVAILABLE:
        st.warning("Charts require plotly installation")
        return
    
    st.markdown("### 📊 Epic Progress")
    
    epics = analytics_data.get("epics", [])
    if not epics:
        st.info("No epic data available")
        return
    
    # Get progress for each epic (simplified)
    epic_progress = []
    for epic in epics[:10]:  # Limit to 10 epics
        epic_name = epic.get("name", "Unknown")[:20] + "..."
        points = epic.get("points_earned", 0)
        status = epic.get("status", "unknown")
        
        epic_progress.append({
            "epic": epic_name,
            "points": points,
            "status": status
        })
    
    if epic_progress and PANDAS_AVAILABLE:
        df = pd.DataFrame(epic_progress)
        
        fig = px.bar(
            df,
            x="epic",
            y="points",
            color="status",
            title="Points by Epic",
            labels={"epic": "Epic", "points": "Points Earned"}
        )
        
        fig.update_layout(height=400, xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)


def _render_tdah_insights(analytics_data: Dict[str, Any]):
    """Render TDAH-specific insights."""
    st.markdown("### 🧠 TDAH Insights")
    
    timer_sessions = analytics_data.get("timer_sessions", [])
    if not timer_sessions:
        st.info("No TDAH data available")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Interruption analysis
        total_interruptions = sum(s.get("interruptions_count", 0) for s in timer_sessions)
        avg_interruptions = total_interruptions / len(timer_sessions) if timer_sessions else 0
        
        st.metric(
            "🚫 Total Interruptions",
            total_interruptions,
            f"{avg_interruptions:.1f} avg per session"
        )
        
        # Energy level analysis
        energy_levels = [s.get("energy_level") for s in timer_sessions if s.get("energy_level")]
        if energy_levels:
            avg_energy = sum(energy_levels) / len(energy_levels)
            st.metric(
                "⚡ Avg Energy Level",
                f"{avg_energy:.1f}/10",
                f"Based on {len(energy_levels)} sessions"
            )
    
    with col2:
        # Focus rating distribution
        focus_ratings = [s.get("focus_rating") for s in timer_sessions if s.get("focus_rating")]
        if focus_ratings and PLOTLY_AVAILABLE:
            fig = px.histogram(
                x=focus_ratings,
                nbins=10,
                title="Focus Rating Distribution",
                labels={"x": "Focus Rating (1-10)", "y": "Sessions"},
                color_discrete_sequence=["lightcoral"]
            )
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)


def _render_detailed_tables(analytics_data: Dict[str, Any]):
    """Render detailed data tables."""
    
    tab1, tab2, tab3 = st.tabs(["📅 Daily Metrics", "⏱️ Recent Sessions", "📋 Task Details"])
    
    with tab1:
        daily_metrics = analytics_data.get("daily_metrics", [])
        if daily_metrics and PANDAS_AVAILABLE:
            df = pd.DataFrame(daily_metrics)
            df = df.sort_values("date", ascending=False)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No daily metrics available")
    
    with tab2:
        timer_sessions = analytics_data.get("timer_sessions", [])
        if timer_sessions:
            # Show recent 10 sessions
            recent_sessions = timer_sessions[:10]
            session_data = []
            
            for session in recent_sessions:
                session_data.append({
                    "Date": session.get("started_at", "")[:16],
                    "Duration": f"{session.get('planned_duration_minutes', 0)}min",
                    "Focus": f"{session.get('focus_rating', 'N/A')}/10",
                    "Interruptions": session.get('interruptions_count', 0),
                    "Task": session.get('task_reference', 'N/A')
                })
            
            if PANDAS_AVAILABLE:
                df = pd.DataFrame(session_data)
                st.dataframe(df, use_container_width=True)
            else:
                for session in session_data[:5]:
                    st.json(session)
        else:
            st.info("No timer sessions available")
    
    with tab3:
        tasks = analytics_data.get("tasks", [])
        if tasks:
            task_data = []
            for task in tasks[:20]:  # Recent 20 tasks
                task_data.append({
                    "Title": task.get("title", "Unknown"),
                    "Status": task.get("status", "unknown"),
                    "TDD Phase": task.get("tdd_phase", "unknown"),
                    "Epic": task.get("epic_name", "Unknown"),
                    "Estimate": f"{task.get('estimate_minutes', 0)}min"
                })
            
            if PANDAS_AVAILABLE:
                df = pd.DataFrame(task_data)
                st.dataframe(df, use_container_width=True)
            else:
                for task in task_data[:5]:
                    st.json(task)
        else:
            st.info("No task data available")


if __name__ == "__main__":
    render_analytics_page()