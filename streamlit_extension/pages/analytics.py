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
import time
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
    from streamlit_extension.utils.auth import require_authentication
    from streamlit_extension.config import load_config
    DATABASE_UTILS_AVAILABLE = True
except ImportError:
    DatabaseManager = load_config = None
    DATABASE_UTILS_AVAILABLE = False

try:
    from tdah_tools.analytics_engine import AnalyticsEngine, TDDAHAnalytics
    ANALYTICS_ENGINE_AVAILABLE = True
except ImportError:
    AnalyticsEngine = TDDAHAnalytics = None
    ANALYTICS_ENGINE_AVAILABLE = False

# Performance optimization imports
try:
    import functools
    import hashlib
    PERFORMANCE_UTILS_AVAILABLE = True
except ImportError:
    functools = hashlib = None
    PERFORMANCE_UTILS_AVAILABLE = False


# Performance optimization functions
class AnalyticsCache:
    """Simple in-memory cache for analytics data with TTL support."""

    def __init__(self):
        self.cache = {}
        self.cache_timestamps = {}
        self.default_ttl = 300  # 5 minutes

    def get_cache_key(self, *args, **kwargs):
        """Generate a cache key from arguments."""
        if not PERFORMANCE_UTILS_AVAILABLE:
            return None

        key_data = str(args) + str(sorted(kwargs.items()))
        return hashlib.sha256(key_data.encode()).hexdigest()

    def get(self, key, ttl=None):
        """Get cached data if still valid."""
        if not key or key not in self.cache:
            return None

        ttl = ttl or self.default_ttl
        cache_time = self.cache_timestamps.get(key, 0)

        if time.time() - cache_time > ttl:
            # Expired, remove from cache
            self.cache.pop(key, None)
            self.cache_timestamps.pop(key, None)
            return None

        return self.cache[key]

    def set(self, key, value):
        """Cache data with timestamp."""
        if not key:
            return

        self.cache[key] = value
        self.cache_timestamps[key] = time.time()

    def clear(self):
        """Clear all cached data."""
        self.cache.clear()
        self.cache_timestamps.clear()

    def size(self):
        """Get current cache size."""
        return len(self.cache)


# Global cache instance
_analytics_cache = AnalyticsCache()


def performance_monitor(func):
    """Decorator to monitor function performance."""
    if not PERFORMANCE_UTILS_AVAILABLE:
        return func

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time

        # Store performance metrics in session state
        if 'performance_metrics' not in st.session_state:
            st.session_state.performance_metrics = {}

        st.session_state.performance_metrics[func.__name__] = {
            'execution_time': execution_time,
            'timestamp': time.time()
        }

        return result
    return wrapper


def cached_analytics_data(ttl=300):
    """Decorator for caching analytics data with configurable TTL."""
    def decorator(func):
        if not PERFORMANCE_UTILS_AVAILABLE:
            return func

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Check if caching is enabled
            if hasattr(st.session_state, 'performance_settings') and not st.session_state.performance_settings.get('use_cache', True):
                return func(*args, **kwargs)

            # Generate cache key
            cache_key = _analytics_cache.get_cache_key(func.__name__, *args, **kwargs)

            # Try to get from cache
            cached_result = _analytics_cache.get(cache_key, ttl)
            if cached_result is not None:
                return cached_result

            # Execute function and cache result
            result = func(*args, **kwargs)
            _analytics_cache.set(cache_key, result)

            return result
        return wrapper
    return decorator


def optimize_database_queries(db_manager: DatabaseManager, days: int, filters: Dict[str, Any] = None) -> Dict[str, Any]:
    """Optimized database queries with intelligent batching and filtering."""

    try:
        # Batch multiple queries for efficiency
        query_results = {}

        # Get all data in optimized batches
        with st.spinner("Optimizing data queries..."):
            # Query 1: Get timer sessions with pre-filtering
            session_query_filters = {}
            if filters:
                if filters.get("focus_range") and filters["focus_range"] != (1, 10):
                    min_focus, max_focus = filters["focus_range"]
                    session_query_filters["focus_range"] = (min_focus, max_focus)

                if filters.get("selected_session_types"):
                    session_query_filters["session_types"] = filters["selected_session_types"]

            query_results["timer_sessions"] = db_manager.get_timer_sessions(days)

            # Query 2: Get tasks with pre-filtering
            task_query_filters = {}
            if filters:
                if filters.get("selected_epics"):
                    task_query_filters["epic_names"] = filters["selected_epics"]

                if filters.get("selected_tdd_phases"):
                    task_query_filters["tdd_phases"] = filters["selected_tdd_phases"]

            query_results["tasks"] = db_manager.get_tasks()
            query_results["epics"] = db_manager.get_epics()
            query_results["user_stats"] = db_manager.get_user_stats()

        return query_results

    except Exception as e:
        st.error(f"Database query optimization failed: {e}")
        # Fallback to individual queries
        return {
            "timer_sessions": db_manager.get_timer_sessions(days),
            "tasks": db_manager.get_tasks(),
            "epics": db_manager.get_epics(),
            "user_stats": db_manager.get_user_stats()
        }


@require_authentication
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

    # Initialize database manager and analytics engine
    try:
        config = load_config()
        db_manager = DatabaseManager(
            framework_db_path=str(config.get_database_path()),
            timer_db_path=str(config.get_timer_database_path())
        )

        # Initialize analytics engine
        if ANALYTICS_ENGINE_AVAILABLE:
            analytics_engine = TDDAHAnalytics(db_path=str(config.get_timer_database_path()))
            st.sidebar.success("🧠 Advanced analytics enabled")
        else:
            analytics_engine = None
            st.sidebar.warning("⚠️ Basic analytics mode (install pandas, plotly for full features)")

    except Exception as e:
        st.error(f"❌ Database connection error: {e}")
        return

    # Enhanced time range selector with interactivity
    st.sidebar.markdown("## 📅 Time Range")

    # Quick time range options
    time_options = {
        "Today": 1,
        "Last 3 days": 3,
        "Last 7 days": 7,
        "Last 14 days": 14,
        "Last 30 days": 30,
        "Last 90 days": 90,
        "Last 6 months": 180,
        "Last year": 365,
        "All time": 9999,
        "Custom range": 0
    }

    selected_range = st.sidebar.selectbox("Select time range", list(time_options.keys()), index=2)

    if selected_range == "Custom range":
        col1, col2 = st.sidebar.columns(2)
        with col1:
            start_date = st.date_input("From", value=datetime.now() - timedelta(days=30))
        with col2:
            end_date = st.date_input("To", value=datetime.now())

        # Calculate days difference
        days = (end_date - start_date).days + 1
        st.sidebar.caption(f"Period: {days} days")
    else:
        days = time_options[selected_range]

    # Advanced filters
    st.sidebar.markdown("## 🔍 Advanced Filters")

    # Epic filter
    show_epic_filter = st.sidebar.checkbox("Filter by Epic", value=False)
    selected_epics = []
    if show_epic_filter:
        try:
            config = load_config()
            db_manager = DatabaseManager(
                framework_db_path=str(config.get_database_path()),
                timer_db_path=str(config.get_timer_database_path())
            )
            all_epics = db_manager.get_epics()
            epic_names = [epic.get("name", "Unknown") for epic in all_epics]
            selected_epics = st.sidebar.multiselect("Select Epics", epic_names)
        except:
            st.sidebar.warning("Could not load epics")

    # Focus level filter
    show_focus_filter = st.sidebar.checkbox("Filter by Focus Level", value=False)
    focus_range = (1, 10)
    if show_focus_filter:
        focus_range = st.sidebar.slider(
            "Focus Rating Range", 
            min_value=1, max_value=10, 
            value=(1, 10), 
            step=1
        )

    # TDD phase filter
    show_tdd_filter = st.sidebar.checkbox("Filter by TDD Phase", value=False)
    selected_tdd_phases = []
    if show_tdd_filter:
        tdd_phases = ["red", "green", "refactor"]
        selected_tdd_phases = st.sidebar.multiselect("Select TDD Phases", tdd_phases)

    # Session type filter
    show_session_filter = st.sidebar.checkbox("Filter by Session Type", value=False)
    selected_session_types = []
    if show_session_filter:
        session_types = ["focus_session", "short_break", "long_break", "custom"]
        selected_session_types = st.sidebar.multiselect("Select Session Types", session_types)

    # Store filters in session state for use across functions
    st.session_state.analytics_filters = {
        "days": days,
        "selected_epics": selected_epics,
        "focus_range": focus_range,
        "selected_tdd_phases": selected_tdd_phases,
        "selected_session_types": selected_session_types,
        "custom_date_range": (start_date, end_date) if selected_range == "Custom range" else None
    }

    # Interactive controls
    st.sidebar.markdown("## ⚡ Interactive Controls")

    # Auto-refresh option
    auto_refresh = st.sidebar.checkbox("Auto-refresh (30s)", value=False)
    if auto_refresh:
        st.sidebar.info("📡 Data refreshes automatically")
        # Add auto-refresh functionality
        if 'refresh_counter' not in st.session_state:
            st.session_state.refresh_counter = 0
        st.session_state.refresh_counter += 1

        # Show refresh indicator
        st.sidebar.caption(f"Last refresh: {datetime.now().strftime('%H:%M:%S')}")

        # Auto-refresh every 30 seconds
        time.sleep(1)  # Small delay to prevent too frequent refreshes
        st.rerun()

    # Manual refresh button
    if st.sidebar.button("🔄 Refresh Data", type="primary"):
        st.rerun()

    # Export controls
    st.sidebar.markdown("## 📊 Export Options")

    export_format = st.sidebar.selectbox(
        "Export Format",
        ["CSV", "JSON", "Excel"],
        help="Choose format for exporting analytics data"
    )

    if st.sidebar.button("📥 Export Data"):
        _export_analytics_data(analytics_data if 'analytics_data' in locals() else {}, export_format)

    # Chart interaction settings
    st.sidebar.markdown("## 📈 Chart Settings")

    chart_theme = st.sidebar.selectbox(
        "Chart Theme",
        ["plotly", "plotly_white", "plotly_dark", "presentation"],
        index=0,
        help="Choose visual theme for charts"
    )

    show_animations = st.sidebar.checkbox("Chart Animations", value=True)
    show_tooltips = st.sidebar.checkbox("Enhanced Tooltips", value=True)

    # Store chart settings
    st.session_state.chart_settings = {
        "theme": chart_theme,
        "animations": show_animations,
        "tooltips": show_tooltips
    }

    # Performance settings
    st.sidebar.markdown("## ⚙️ Performance")

    use_cache = st.sidebar.checkbox("Use Data Caching", value=True, help="Cache data for faster loading")
    chart_quality = st.sidebar.selectbox("Chart Quality", ["High", "Medium", "Fast"], index=1)

    st.session_state.performance_settings = {
        "use_cache": use_cache,
        "chart_quality": chart_quality
    }

    # Performance monitoring display
    if st.sidebar.checkbox("Show Performance Metrics", value=False):
        _render_performance_metrics()

    # Fetch data using analytics engine or fallback
    with st.spinner("Loading analytics data..."):
        if analytics_engine:
            analytics_data = _get_enhanced_analytics_data(analytics_engine, db_manager, days)
        else:
            analytics_data = _get_analytics_data(db_manager, days)

        # Apply filters if any are set
        if hasattr(st.session_state, 'analytics_filters') and st.session_state.analytics_filters:
            analytics_data = _apply_data_filters(analytics_data, st.session_state.analytics_filters)

            # Show filter status
            active_filters = []
            filters = st.session_state.analytics_filters

            if filters.get("selected_epics"):
                active_filters.append(f"Epics: {len(filters['selected_epics'])}")
            if filters.get("focus_range") != (1, 10):
                active_filters.append(f"Focus: {filters['focus_range'][0]}-{filters['focus_range'][1]}")
            if filters.get("selected_tdd_phases"):
                active_filters.append(f"TDD: {len(filters['selected_tdd_phases'])}")
            if filters.get("selected_session_types"):
                active_filters.append(f"Sessions: {len(filters['selected_session_types'])}")

            if active_filters:
                st.info(f"🔍 **Active filters:** {' | '.join(active_filters)}")

                # Add reset filters button
                col1, col2 = st.columns([1, 4])
                with col1:
                    if st.button("🗑️ Clear Filters"):
                        if hasattr(st.session_state, 'analytics_filters'):
                            del st.session_state.analytics_filters
                        st.rerun()

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

    st.markdown("---")

    # Advanced TDAH metrics dashboard
    _render_advanced_tdah_metrics(analytics_data)

    # Detailed tables
    with st.expander("📋 Detailed Data"):
        _render_detailed_tables(analytics_data)


@cached_analytics_data(ttl=300)  # Cache for 5 minutes
@performance_monitor
def _get_enhanced_analytics_data(analytics_engine: Any, db_manager: DatabaseManager, days: int) -> Dict[str, Any]:
    """Get enhanced analytics data using the analytics engine."""

    try:
        # Get productivity metrics from analytics engine
        productivity_metrics = analytics_engine.generate_productivity_metrics(days)

        # Get time patterns analysis
        time_patterns = analytics_engine.analyze_time_patterns(days)

        # Get session data
        session_data = analytics_engine.load_session_data(days)

        # Get basic database data for supplemental info
        basic_data = _get_analytics_data(db_manager, days)

        # Combine enhanced analytics with basic data
        enhanced_data = {
            **basic_data,
            "productivity_metrics": productivity_metrics,
            "time_patterns": time_patterns,
            "session_data": session_data,
            "analytics_engine_enabled": True
        }

        return enhanced_data

    except Exception as e:
        st.warning(f"⚠️ Analytics engine error, falling back to basic mode: {e}")
        return _get_analytics_data(db_manager, days)


@cached_analytics_data(ttl=180)  # Cache for 3 minutes  
@performance_monitor
def _get_analytics_data(db_manager: DatabaseManager, days: int) -> Dict[str, Any]:
    """Get basic analytics data from database (fallback mode) with optimized queries."""

    # Use optimized database queries
    filters = getattr(st.session_state, 'analytics_filters', {})
    query_results = optimize_database_queries(db_manager, days, filters)

    timer_sessions = query_results.get("timer_sessions", [])
    epics = query_results.get("epics", [])
    tasks = query_results.get("tasks", [])
    user_stats = query_results.get("user_stats", {})

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
    """Render overview metrics cards with enhanced analytics engine data."""

    col1, col2, col3, col4 = st.columns(4)

    # Check if analytics engine is enabled for enhanced metrics
    engine_enabled = analytics_data.get("analytics_engine_enabled", False)
    productivity_metrics = analytics_data.get("productivity_metrics", {})

    with col1:
        if engine_enabled and productivity_metrics:
            # Use enhanced productivity metrics
            total_time = productivity_metrics.get("total_focus_time_minutes", 0)
            efficiency_score = productivity_metrics.get("focus_efficiency_score", 0)
            delta_text = f"Efficiency: {efficiency_score:.1f}%" if efficiency_score > 0 else None
        else:
            # Fallback to basic metrics
            total_time = analytics_data.get("total_focus_time", 0)
            delta_text = f"{analytics_data.get('total_sessions', 0)} sessions"

        hours = total_time // 60
        minutes = total_time % 60
        st.metric(
            "🕐 Total Focus Time",
            f"{hours}h {minutes}m",
            delta_text
        )

    with col2:
        if engine_enabled and productivity_metrics:
            # Enhanced task completion metrics
            completed = productivity_metrics.get("tasks_completed", analytics_data.get("completed_tasks", 0))
            velocity = productivity_metrics.get("daily_velocity", 0)
            delta_text = f"Velocity: {velocity:.1f}/day" if velocity > 0 else None
        else:
            # Basic metrics
            completed = analytics_data.get("completed_tasks", 0)
            avg_per_day = completed / analytics_data.get("period_days", 1) if completed > 0 else 0
            delta_text = f"{avg_per_day:.1f}/day avg"

        st.metric(
            "✅ Tasks Completed",
            completed,
            delta_text
        )

    with col3:
        if engine_enabled and productivity_metrics:
            # Enhanced focus metrics with trend
            focus_rating = productivity_metrics.get("average_focus_rating", 0)
            focus_trend = productivity_metrics.get("focus_trend", "stable")
            trend_emoji = {"improving": "📈", "declining": "📉", "stable": "➡️"}.get(focus_trend, "➡️")
            delta_text = f"{trend_emoji} {focus_trend}"
        else:
            # Basic focus rating
            focus_rating = analytics_data.get("average_focus_rating", 0)
            delta_text = "TDAH metric"

        st.metric(
            "🎯 Avg Focus Rating",
            f"{focus_rating:.1f}/10",
            delta_text
        )

    with col4:
        if engine_enabled and productivity_metrics:
            # Enhanced points with streak info
            points = productivity_metrics.get("total_points", analytics_data.get("total_points", 0))
            streak = productivity_metrics.get("current_streak", 0)
            delta_text = f"🔥 {streak} day streak" if streak > 1 else f"{analytics_data.get('active_epics', 0)} active epics"
        else:
            # Basic points
            points = analytics_data.get("total_points", 0)
            delta_text = f"{analytics_data.get('active_epics', 0)} active epics"

        st.metric(
            "🌟 Total Points",
            f"{points:,}",
            delta_text
        )


def _render_productivity_chart(analytics_data: Dict[str, Any]):
    """Render enhanced productivity over time chart using analytics engine data."""
    if not PLOTLY_AVAILABLE:
        st.warning("Charts require plotly installation")
        return

    st.markdown("### 📈 Daily Productivity")

    engine_enabled = analytics_data.get("analytics_engine_enabled", False)
    productivity_metrics = analytics_data.get("productivity_metrics", {})

    if engine_enabled and productivity_metrics:
        # Use enhanced productivity data from analytics engine
        daily_productivity = productivity_metrics.get("daily_productivity", [])

        if not daily_productivity:
            # Fallback to basic daily metrics
            daily_metrics = analytics_data.get("daily_metrics", [])
            daily_productivity = daily_metrics

        if daily_productivity and PANDAS_AVAILABLE:
            # Convert to DataFrame for easier manipulation
            df_data = []
            for day_data in daily_productivity:
                df_data.append({
                    "date": day_data.get("date", ""),
                    "focus_minutes": day_data.get("focus_minutes", day_data.get("total_focus_time", 0)),
                    "tasks_completed": day_data.get("tasks_completed", 0),
                    "productivity_score": day_data.get("productivity_score", 0),
                    "focus_efficiency": day_data.get("focus_efficiency", 0),
                    "avg_focus_rating": day_data.get("avg_focus_rating", 0)
                })

            df = pd.DataFrame(df_data)
            df = df.sort_values("date")

            # Create enhanced chart with productivity score
            fig = make_subplots(
                rows=2, cols=1,
                subplot_titles=["Focus Time & Tasks Completed", "Productivity Score & Focus Efficiency"],
                specs=[[{"secondary_y": True}], [{"secondary_y": True}]],
                vertical_spacing=0.12
            )

            # Top chart: Focus time (bars) and tasks (line)
            fig.add_trace(
                go.Bar(
                    x=df["date"],
                    y=df["focus_minutes"],
                    name="Focus Minutes",
                    marker_color="lightblue",
                    opacity=0.7
                ),
                row=1, col=1, secondary_y=False
            )

            fig.add_trace(
                go.Scatter(
                    x=df["date"],
                    y=df["tasks_completed"],
                    mode="lines+markers",
                    name="Tasks Completed",
                    line=dict(color="orange", width=2),
                    marker=dict(size=6)
                ),
                row=1, col=1, secondary_y=True
            )

            # Bottom chart: Productivity metrics
            fig.add_trace(
                go.Scatter(
                    x=df["date"],
                    y=df["productivity_score"],
                    mode="lines+markers",
                    name="Productivity Score",
                    line=dict(color="green", width=3),
                    marker=dict(size=8)
                ),
                row=2, col=1, secondary_y=False
            )

            fig.add_trace(
                go.Scatter(
                    x=df["date"],
                    y=df["focus_efficiency"],
                    mode="lines+markers",
                    name="Focus Efficiency %",
                    line=dict(color="purple", width=2, dash="dash"),
                    marker=dict(size=6)
                ),
                row=2, col=1, secondary_y=True
            )

            # Update axes
            fig.update_xaxes(title_text="Date", row=2, col=1)
            fig.update_yaxes(title_text="Focus Minutes", row=1, col=1, secondary_y=False)
            fig.update_yaxes(title_text="Tasks Completed", row=1, col=1, secondary_y=True)
            fig.update_yaxes(title_text="Productivity Score", row=2, col=1, secondary_y=False)
            fig.update_yaxes(title_text="Focus Efficiency %", row=2, col=1, secondary_y=True)

            fig.update_layout(
                height=600,
                showlegend=True,
                title=None
            )

            st.plotly_chart(fig, use_container_width=True)

            # Add insights if available
            if productivity_metrics.get("insights"):
                st.markdown("#### 💡 Productivity Insights")
                for insight in productivity_metrics["insights"][:3]:
                    st.info(f"• {insight}")
        else:
            st.info("No productivity data available")
    else:
        # Fallback to basic chart
        daily_metrics = analytics_data.get("daily_metrics", [])
        if not daily_metrics:
            st.info("No daily data available")
            return

        # Sort by date
        daily_metrics.sort(key=lambda x: x["date"])

        if PANDAS_AVAILABLE:
            df = pd.DataFrame(daily_metrics)

            # Create basic subplot with secondary y-axis
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
    """Render enhanced focus time analysis using analytics engine time patterns."""
    if not PLOTLY_AVAILABLE:
        st.warning("Charts require plotly installation")
        return

    st.markdown("### ⏱️ Focus Time Analysis")

    engine_enabled = analytics_data.get("analytics_engine_enabled", False)
    time_patterns = analytics_data.get("time_patterns", {})

    if engine_enabled and time_patterns:
        # Use enhanced time patterns from analytics engine
        hourly_focus = time_patterns.get("hourly_focus_distribution", {})
        peak_hours = time_patterns.get("peak_productivity_hours", [])
        focus_quality_by_hour = time_patterns.get("focus_quality_by_hour", {})

        if hourly_focus:
            # Create enhanced hourly chart with focus quality overlay
            hours = list(range(24))
            minutes = [hourly_focus.get(str(h), 0) for h in hours]
            focus_quality = [focus_quality_by_hour.get(str(h), 0) for h in hours]

            # Create dual chart showing time and quality
            fig = make_subplots(
                rows=2, cols=1,
                subplot_titles=["Focus Time by Hour", "Focus Quality by Hour"],
                vertical_spacing=0.15
            )

            # Top chart: Focus time with peak hours highlighted
            colors = ['rgba(255, 99, 132, 0.8)' if h in peak_hours else 'rgba(54, 162, 235, 0.6)' for h in hours]

            fig.add_trace(
                go.Bar(
                    x=hours,
                    y=minutes,
                    name="Focus Minutes",
                    marker_color=colors,
                    text=[f"{m:.0f}min" if m > 0 else "" for m in minutes],
                    textposition="outside"
                ),
                row=1, col=1
            )

            # Bottom chart: Focus quality
            fig.add_trace(
                go.Scatter(
                    x=hours,
                    y=focus_quality,
                    mode="lines+markers",
                    name="Focus Quality",
                    line=dict(color="green", width=3),
                    marker=dict(size=8, color=focus_quality, colorscale="RdYlGn", cmin=0, cmax=10),
                    fill="tonexty" if focus_quality else None
                ),
                row=2, col=1
            )

            # Update layout
            fig.update_xaxes(title_text="Hour of Day", row=2, col=1, dtick=2)
            fig.update_yaxes(title_text="Minutes", row=1, col=1)
            fig.update_yaxes(title_text="Quality (1-10)", row=2, col=1, range=[0, 10])

            fig.update_layout(
                height=500,
                showlegend=False,
                title=None
            )

            st.plotly_chart(fig, use_container_width=True)

            # Add insights
            col1, col2 = st.columns(2)
            with col1:
                if peak_hours:
                    peak_times = ", ".join([f"{h}:00" for h in peak_hours[:3]])
                    st.success(f"🌟 **Peak Hours:** {peak_times}")

                total_focus_time = sum(minutes)
                avg_session_quality = sum(focus_quality) / len([q for q in focus_quality if q > 0]) if any(focus_quality) else 0
                st.info(f"⏱️ **Total Focus:** {total_focus_time:.0f} minutes")
                st.info(f"🎯 **Avg Quality:** {avg_session_quality:.1f}/10")

            with col2:
                # Time patterns insights
                patterns = time_patterns.get("patterns", [])
                if patterns:
                    st.markdown("**💡 Time Insights:**")
                    for pattern in patterns[:3]:
                        st.markdown(f"• {pattern}")
        else:
            st.info("No enhanced time pattern data available")
    else:
        # Fallback to basic hourly analysis
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
        phase = task.get("tdd_phase") or "unknown"
        phase = phase.lower() if isinstance(phase, str) else "unknown"
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
    """Render enhanced epic progress overview with productivity insights."""
    if not PLOTLY_AVAILABLE:
        st.warning("Charts require plotly installation")
        return

    st.markdown("### 📊 Epic Progress")

    engine_enabled = analytics_data.get("analytics_engine_enabled", False)
    productivity_metrics = analytics_data.get("productivity_metrics", {})

    if engine_enabled and productivity_metrics:
        # Enhanced epic analysis from analytics engine
        epic_analysis = productivity_metrics.get("epic_analysis", {})

        if epic_analysis:
            epic_performance = epic_analysis.get("epic_performance", [])

            if epic_performance and PANDAS_AVAILABLE:
                # Create comprehensive epic dashboard
                df = pd.DataFrame(epic_performance)

                # Multi-metric epic chart
                fig = make_subplots(
                    rows=2, cols=2,
                    subplot_titles=[
                        "Points Earned by Epic",
                        "Epic Velocity (Tasks/Week)", 
                        "Epic Efficiency Score",
                        "Progress vs Target"
                    ],
                    specs=[
                        [{"type": "bar"}, {"type": "bar"}],
                        [{"type": "scatter"}, {"type": "bar"}]
                    ]
                )

                # Top-left: Points by Epic
                fig.add_trace(
                    go.Bar(
                        x=df["epic_name"] if "epic_name" in df.columns else df.get("name", []),
                        y=df["points_earned"] if "points_earned" in df.columns else df.get("points", []),
                        name="Points",
                        marker_color="lightblue",
                        text=df["points_earned"] if "points_earned" in df.columns else df.get("points", []),
                        textposition="outside"
                    ),
                    row=1, col=1
                )

                # Top-right: Epic Velocity (if available)
                if "velocity" in df.columns:
                    fig.add_trace(
                        go.Bar(
                            x=df["epic_name"] if "epic_name" in df.columns else df.get("name", []),
                            y=df["velocity"],
                            name="Velocity",
                            marker_color="orange",
                            text=[f"{v:.1f}" for v in df["velocity"]],
                            textposition="outside"
                        ),
                        row=1, col=2
                    )

                # Bottom-left: Efficiency Score (if available)
                if "efficiency_score" in df.columns:
                    fig.add_trace(
                        go.Scatter(
                            x=df["epic_name"] if "epic_name" in df.columns else df.get("name", []),
                            y=df["efficiency_score"],
                            mode="markers+lines",
                            name="Efficiency",
                            marker=dict(size=12, color=df["efficiency_score"], colorscale="RdYlGn", cmin=0, cmax=100),
                            line=dict(color="green", width=2)
                        ),
                        row=2, col=1
                    )

                # Bottom-right: Progress vs Target (if available)
                if "progress_percentage" in df.columns:
                    fig.add_trace(
                        go.Bar(
                            x=df["epic_name"] if "epic_name" in df.columns else df.get("name", []),
                            y=df["progress_percentage"],
                            name="Actual Progress",
                            marker_color="lightgreen",
                            opacity=0.7
                        ),
                        row=2, col=2
                    )

                    if "target_percentage" in df.columns:
                        fig.add_trace(
                            go.Scatter(
                                x=df["epic_name"] if "epic_name" in df.columns else df.get("name", []),
                                y=df["target_percentage"],
                                mode="markers+lines",
                                name="Target",
                                line=dict(color="red", dash="dash", width=2),
                                marker=dict(size=8, color="red")
                            ),
                            row=2, col=2
                        )

                # Update layout
                fig.update_layout(
                    height=600,
                    showlegend=False
                )

                # Update axes
                fig.update_xaxes(tickangle=-45)
                fig.update_yaxes(title_text="Points", row=1, col=1)
                fig.update_yaxes(title_text="Tasks/Week", row=1, col=2)
                fig.update_yaxes(title_text="Efficiency %", range=[0, 100], row=2, col=1)
                fig.update_yaxes(title_text="Progress %", range=[0, 100], row=2, col=2)

                st.plotly_chart(fig, use_container_width=True)

                # Epic insights
                col1, col2, col3 = st.columns(3)

                with col1:
                    if "velocity" in df.columns and len(df) > 0:
                        top_velocity_epic = df.loc[df["velocity"].idxmax()]
                        epic_name = top_velocity_epic.get("epic_name", top_velocity_epic.get("name", "Unknown"))
                        st.success(f"🚀 **Fastest Epic:** {epic_name}")
                        st.caption(f"Velocity: {top_velocity_epic['velocity']:.1f} tasks/week")

                with col2:
                    if "efficiency_score" in df.columns and len(df) > 0:
                        most_efficient_epic = df.loc[df["efficiency_score"].idxmax()]
                        epic_name = most_efficient_epic.get("epic_name", most_efficient_epic.get("name", "Unknown"))
                        st.success(f"⚙️ **Most Efficient:** {epic_name}")
                        st.caption(f"Efficiency: {most_efficient_epic['efficiency_score']:.1f}%")

                with col3:
                    points_col = "points_earned" if "points_earned" in df.columns else "points"
                    total_points = df[points_col].sum() if points_col in df.columns else 0
                    avg_progress = df["progress_percentage"].mean() if "progress_percentage" in df.columns else 0
                    st.metric("Total Points", f"{total_points:,}", f"Avg Progress: {avg_progress:.1f}%")
            else:
                # Fallback to basic epic chart
                _render_basic_epic_progress(analytics_data)
        else:
            _render_basic_epic_progress(analytics_data)
    else:
        _render_basic_epic_progress(analytics_data)

def _render_basic_epic_progress(analytics_data: Dict[str, Any]):
    """Render basic epic progress (fallback)."""
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
    """Render enhanced TDAH-specific insights using analytics engine data."""
    st.markdown("### 🧠 TDAH Insights")

    engine_enabled = analytics_data.get("analytics_engine_enabled", False)
    session_data = analytics_data.get("session_data", {})
    time_patterns = analytics_data.get("time_patterns", {})
    productivity_metrics = analytics_data.get("productivity_metrics", {})

    if engine_enabled and session_data:
        # Enhanced TDAH analysis from analytics engine
        tdah_metrics = session_data.get("tdah_metrics", {})
        focus_patterns = session_data.get("focus_patterns", {})
        interruption_analysis = session_data.get("interruption_analysis", {})
        energy_patterns = session_data.get("energy_patterns", {})

        # Main metrics row
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            # Enhanced interruption analysis
            avg_interruptions = interruption_analysis.get("average_per_session", 0)
            interruption_trend = interruption_analysis.get("trend", "stable")
            trend_color = "red" if interruption_trend == "increasing" else "green" if interruption_trend == "decreasing" else "blue"

            st.metric(
                "🚫 Avg Interruptions",
                f"{avg_interruptions:.1f}",
                f"{interruption_trend}",
                delta_color=trend_color
            )

        with col2:
            # Energy pattern analysis
            avg_energy = energy_patterns.get("average_level", 0)
            optimal_energy_time = energy_patterns.get("peak_hours", [])
            energy_consistency = energy_patterns.get("consistency_score", 0)

            st.metric(
                "⚡ Energy Level",
                f"{avg_energy:.1f}/10",
                f"Consistency: {energy_consistency:.0f}%"
            )

        with col3:
            # Focus sustainability
            focus_sustainability = focus_patterns.get("sustainability_score", 0)
            optimal_session_length = focus_patterns.get("optimal_duration", 0)

            st.metric(
                "🎯 Focus Sustainability",
                f"{focus_sustainability:.0f}%",
                f"Optimal: {optimal_session_length}min"
            )

        with col4:
            # TDAH adaptation score
            adaptation_score = tdah_metrics.get("adaptation_score", 0)
            improvement_trend = tdah_metrics.get("improvement_trend", "stable")

            st.metric(
                "🧠 TDAH Adaptation",
                f"{adaptation_score:.0f}%",
                improvement_trend
            )

        st.markdown("---")

        # Detailed insights
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 📈 Focus Patterns")

            # Focus quality distribution
            focus_distribution = focus_patterns.get("quality_distribution", {})
            if focus_distribution and PLOTLY_AVAILABLE:
                labels = list(focus_distribution.keys())
                values = list(focus_distribution.values())

                fig = px.pie(
                    values=values,
                    names=labels,
                    title="Focus Quality Distribution",
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)

            # Best performance times
            best_times = focus_patterns.get("best_performance_times", [])
            if best_times:
                st.success(f"🌟 **Best focus times:** {', '.join(best_times)}")

        with col2:
            st.markdown("#### 💡 Personalized Recommendations")

            # Get recommendations from analytics engine
            recommendations = tdah_metrics.get("recommendations", [])
            if recommendations:
                for i, rec in enumerate(recommendations[:5]):
                    priority = rec.get("priority", "medium")
                    emoji = "🔴" if priority == "high" else "🟡" if priority == "medium" else "🟢"
                    st.markdown(f"{emoji} **{rec.get('title', 'Recommendation')}**")
                    st.caption(rec.get('description', ''))
            else:
                st.info("Keep tracking sessions to get personalized recommendations!")

        # Energy vs Focus correlation
        if energy_patterns and focus_patterns:
            st.markdown("#### ⚡ Energy vs Focus Correlation")

            correlation_data = session_data.get("energy_focus_correlation", {})
            correlation_score = correlation_data.get("correlation_coefficient", 0)

            if abs(correlation_score) > 0.3:
                if correlation_score > 0:
                    st.success(f"📈 Strong positive correlation ({correlation_score:.2f}) - Higher energy = better focus")
                else:
                    st.warning(f"📉 Negative correlation ({correlation_score:.2f}) - Consider fatigue management")
            else:
                st.info(f"➡️ Weak correlation ({correlation_score:.2f}) - Energy and focus vary independently")

    else:
        # Fallback to basic TDAH analysis
        timer_sessions = analytics_data.get("timer_sessions", [])
        if not timer_sessions:
            st.info("No TDAH data available")
            return

        col1, col2 = st.columns(2)

        with col1:
            # Basic interruption analysis
            total_interruptions = sum(s.get("interruptions_count", 0) for s in timer_sessions)
            avg_interruptions = total_interruptions / len(timer_sessions) if timer_sessions else 0

            st.metric(
                "🚫 Total Interruptions",
                total_interruptions,
                f"{avg_interruptions:.1f} avg per session"
            )

            # Basic energy level analysis
            energy_levels = [s.get("energy_level") for s in timer_sessions if s.get("energy_level")]
            if energy_levels:
                avg_energy = sum(energy_levels) / len(energy_levels)
                st.metric(
                    "⚡ Avg Energy Level",
                    f"{avg_energy:.1f}/10",
                    f"Based on {len(energy_levels)} sessions"
                )

        with col2:
            # Basic focus rating distribution
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


def _export_analytics_data(analytics_data: Dict[str, Any], export_format: str):
    """Export analytics data in the specified format."""

    try:
        import io
        from datetime import datetime

        # Prepare export data
        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "period_days": analytics_data.get("period_days", 0),
            "overview_metrics": {
                "total_focus_time": analytics_data.get("total_focus_time", 0),
                "total_sessions": analytics_data.get("total_sessions", 0),
                "completed_tasks": analytics_data.get("completed_tasks", 0),
                "average_focus_rating": analytics_data.get("average_focus_rating", 0),
                "total_points": analytics_data.get("total_points", 0)
            },
            "daily_metrics": analytics_data.get("daily_metrics", []),
            "timer_sessions": analytics_data.get("timer_sessions", []),
            "tasks": analytics_data.get("tasks", []),
            "epics": analytics_data.get("epics", [])
        }

        # Add enhanced data if available
        if analytics_data.get("analytics_engine_enabled"):
            export_data["enhanced_metrics"] = {
                "productivity_metrics": analytics_data.get("productivity_metrics", {}),
                "time_patterns": analytics_data.get("time_patterns", {}),
                "session_data": analytics_data.get("session_data", {})
            }

        filename = f"tdd_analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        if export_format == "JSON":
            import json
            json_data = json.dumps(export_data, indent=2, default=str)
            st.download_button(
                label="📥 Download JSON",
                data=json_data,
                file_name=f"{filename}.json",
                mime="application/json"
            )

        elif export_format == "CSV" and PANDAS_AVAILABLE:
            # Create CSV from daily metrics
            if export_data["daily_metrics"]:
                df = pd.DataFrame(export_data["daily_metrics"])
                csv_buffer = io.StringIO()
                df.to_csv(csv_buffer, index=False)

                st.download_button(
                    label="📥 Download CSV",
                    data=csv_buffer.getvalue(),
                    file_name=f"{filename}.csv",
                    mime="text/csv"
                )
            else:
                st.warning("No daily metrics available for CSV export")

        elif export_format == "Excel" and PANDAS_AVAILABLE:
            # Create Excel with multiple sheets
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                # Overview sheet
                overview_df = pd.DataFrame([export_data["overview_metrics"]])
                overview_df.to_excel(writer, sheet_name='Overview', index=False)

                # Daily metrics
                if export_data["daily_metrics"]:
                    daily_df = pd.DataFrame(export_data["daily_metrics"])
                    daily_df.to_excel(writer, sheet_name='Daily_Metrics', index=False)

                # Sessions
                if export_data["timer_sessions"]:
                    sessions_df = pd.DataFrame(export_data["timer_sessions"])
                    sessions_df.to_excel(writer, sheet_name='Sessions', index=False)

                # Tasks
                if export_data["tasks"]:
                    tasks_df = pd.DataFrame(export_data["tasks"])
                    tasks_df.to_excel(writer, sheet_name='Tasks', index=False)

            st.download_button(
                label="📥 Download Excel",
                data=buffer.getvalue(),
                file_name=f"{filename}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        st.success(f"✅ Export ready! Download your {export_format} file above.")

    except Exception as e:
        st.error(f"❌ Export failed: {e}")


def _apply_data_filters(data: Dict[str, Any], filters: Dict[str, Any]) -> Dict[str, Any]:
    """Apply filters to analytics data."""

    if not filters:
        return data

    filtered_data = data.copy()

    # Apply epic filter
    if filters.get("selected_epics"):
        selected_epics = filters["selected_epics"]

        # Filter tasks
        if "tasks" in filtered_data:
            filtered_data["tasks"] = [
                task for task in filtered_data["tasks"]
                if task.get("epic_name") in selected_epics
            ]

        # Filter epics
        if "epics" in filtered_data:
            filtered_data["epics"] = [
                epic for epic in filtered_data["epics"]
                if epic.get("name") in selected_epics
            ]

    # Apply focus level filter
    if filters.get("focus_range") and filters["focus_range"] != (1, 10):
        min_focus, max_focus = filters["focus_range"]

        # Filter timer sessions
        if "timer_sessions" in filtered_data:
            filtered_data["timer_sessions"] = [
                session for session in filtered_data["timer_sessions"]
                if (session.get("focus_rating") is None or 
                    min_focus <= session.get("focus_rating", 0) <= max_focus)
            ]

    # Apply TDD phase filter
    if filters.get("selected_tdd_phases"):
        selected_phases = filters["selected_tdd_phases"]

        # Filter tasks
        if "tasks" in filtered_data:
            filtered_data["tasks"] = [
                task for task in filtered_data["tasks"]
                if task.get("tdd_phase") in selected_phases
            ]

    # Apply session type filter
    if filters.get("selected_session_types"):
        selected_types = filters["selected_session_types"]

        # Filter timer sessions
        if "timer_sessions" in filtered_data:
            filtered_data["timer_sessions"] = [
                session for session in filtered_data["timer_sessions"]
                if session.get("session_type") in selected_types
            ]

    # Recalculate metrics after filtering
    filtered_data = _recalculate_metrics(filtered_data)

    return filtered_data


def _recalculate_metrics(data: Dict[str, Any]) -> Dict[str, Any]:
    """Recalculate metrics after applying filters."""

    timer_sessions = data.get("timer_sessions", [])
    tasks = data.get("tasks", [])

    # Recalculate basic metrics
    data["total_sessions"] = len(timer_sessions)
    data["total_focus_time"] = sum(s.get("planned_duration_minutes", 0) for s in timer_sessions)
    data["completed_tasks"] = len([t for t in tasks if t.get("status") == "completed"])

    # Recalculate focus rating
    focus_ratings = [s.get("focus_rating") for s in timer_sessions if s.get("focus_rating")]
    data["average_focus_rating"] = sum(focus_ratings) / len(focus_ratings) if focus_ratings else 0

    # Recalculate daily metrics
    data["daily_metrics"] = _calculate_daily_metrics(timer_sessions, tasks)

    return data


def _render_advanced_tdah_metrics(analytics_data: Dict[str, Any]):
    """Render advanced TDAH-specific metrics dashboard."""

    st.markdown("### 🧠 Advanced TDAH Performance Dashboard")

    engine_enabled = analytics_data.get("analytics_engine_enabled", False)
    session_data = analytics_data.get("session_data", {})
    time_patterns = analytics_data.get("time_patterns", {})
    productivity_metrics = analytics_data.get("productivity_metrics", {})

    if engine_enabled and session_data:
        # Advanced TDAH analysis from analytics engine
        tdah_advanced = session_data.get("tdah_advanced_metrics", {})

        # Key TDAH performance indicators
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            # Attention span indicator
            attention_span = tdah_advanced.get("average_attention_span", 0)
            optimal_span = tdah_advanced.get("optimal_attention_span", 25)
            span_efficiency = min(100, (attention_span / optimal_span) * 100) if optimal_span > 0 else 0

            st.metric(
                "🎯 Attention Span",
                f"{attention_span:.0f}min",
                f"{span_efficiency:.0f}% efficiency"
            )

        with col2:
            # Hyperfocus detection
            hyperfocus_sessions = tdah_advanced.get("hyperfocus_sessions", 0)
            total_sessions = analytics_data.get("total_sessions", 1)
            hyperfocus_rate = (hyperfocus_sessions / total_sessions) * 100 if total_sessions > 0 else 0

            st.metric(
                "⚡ Hyperfocus Rate",
                f"{hyperfocus_rate:.1f}%",
                f"{hyperfocus_sessions} sessions"
            )

        with col3:
            # Distraction resilience
            resilience_score = tdah_advanced.get("distraction_resilience", 0)
            resilience_trend = tdah_advanced.get("resilience_trend", "stable")

            st.metric(
                "🛡️ Distraction Resilience", 
                f"{resilience_score:.0f}%",
                resilience_trend
            )

        with col4:
            # Task switching frequency
            task_switches = tdah_advanced.get("avg_task_switches_per_hour", 0)
            switch_efficiency = max(0, 100 - (task_switches * 10))  # Penalize frequent switching

            st.metric(
                "🔄 Task Switching",
                f"{task_switches:.1f}/hour",
                f"{switch_efficiency:.0f}% efficiency"
            )

        # Advanced visualizations
        tab1, tab2, tab3 = st.tabs(["🎯 Focus Patterns", "⚡ Energy Analysis", "🧠 Cognitive Load"])

        with tab1:
            _render_focus_patterns_analysis(tdah_advanced, time_patterns)

        with tab2:
            _render_energy_analysis(tdah_advanced, session_data)

        with tab3:
            _render_cognitive_load_analysis(tdah_advanced, productivity_metrics)

    else:
        # Fallback TDAH metrics using basic session data
        _render_basic_tdah_metrics(analytics_data)


def _render_focus_patterns_analysis(tdah_advanced: Dict[str, Any], time_patterns: Dict[str, Any]):
    """Render detailed focus patterns analysis."""

    st.markdown("#### 🎯 Focus Patterns & Optimization")

    focus_patterns = tdah_advanced.get("focus_patterns", {})

    if focus_patterns and PLOTLY_AVAILABLE:
        # Focus quality heatmap by hour and day
        heatmap_data = focus_patterns.get("weekly_focus_heatmap", {})

        if heatmap_data:
            col1, col2 = st.columns([2, 1])

            with col1:
                # Create focus quality heatmap
                days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                hours = list(range(6, 24))  # 6 AM to 11 PM

                # Convert data to matrix format
                z_data = []
                for day in days:
                    day_data = []
                    for hour in hours:
                        focus_quality = heatmap_data.get(f"{day}_{hour}", 0)
                        day_data.append(focus_quality)
                    z_data.append(day_data)

                fig = go.Figure(data=go.Heatmap(
                    z=z_data,
                    x=[f"{h}:00" for h in hours],
                    y=days,
                    colorscale="RdYlGn",
                    zmin=0, zmax=10,
                    colorbar=dict(title="Focus Quality")
                ))

                fig.update_layout(
                    title="Weekly Focus Quality Heatmap",
                    xaxis_title="Hour of Day",
                    yaxis_title="Day of Week",
                    height=300
                )

                st.plotly_chart(fig, use_container_width=True)

            with col2:
                # Focus optimization recommendations
                st.markdown("**🎯 Optimization Tips:**")

                peak_times = focus_patterns.get("peak_focus_times", [])
                low_times = focus_patterns.get("low_focus_times", [])

                if peak_times:
                    st.success(f"✨ **Best times:** {', '.join(peak_times[:3])}")
                    st.info("Schedule important tasks during these hours")

                if low_times:
                    st.warning(f"⚠️ **Challenging times:** {', '.join(low_times[:2])}")
                    st.info("Use these for routine/administrative tasks")

                # Focus duration insights
                optimal_duration = focus_patterns.get("optimal_session_duration", 25)
                st.success(f"🎯 **Optimal session:** {optimal_duration} minutes")

        # Attention span trends
        attention_trends = focus_patterns.get("attention_span_trends", [])
        if attention_trends:
            st.markdown("**📈 Attention Span Trends**")

            # Create line chart for attention span over time
            if PANDAS_AVAILABLE:
                df = pd.DataFrame(attention_trends)

                fig = px.line(
                    df,
                    x="date",
                    y="attention_span",
                    title="Attention Span Over Time",
                    labels={"attention_span": "Minutes", "date": "Date"}
                )

                fig.add_hline(y=df["attention_span"].mean(), line_dash="dash", line_color="red",
                             annotation_text=f"Average: {df['attention_span'].mean():.1f}min")

                fig.update_layout(height=250)
                st.plotly_chart(fig, use_container_width=True)


def _render_energy_analysis(tdah_advanced: Dict[str, Any], session_data: Dict[str, Any]):
    """Render energy level analysis specific to TDAH."""

    st.markdown("#### ⚡ Energy Patterns & Management")

    energy_analysis = tdah_advanced.get("energy_analysis", {})

    if energy_analysis and PLOTLY_AVAILABLE:
        col1, col2 = st.columns(2)

        with col1:
            # Energy vs Focus correlation
            correlation_data = energy_analysis.get("energy_focus_correlation", [])

            if correlation_data and PANDAS_AVAILABLE:
                df = pd.DataFrame(correlation_data)

                fig = px.scatter(
                    df,
                    x="energy_level",
                    y="focus_rating",
                    size="session_duration",
                    color="time_of_day",
                    title="Energy vs Focus Correlation",
                    labels={
                        "energy_level": "Energy Level (1-10)",
                        "focus_rating": "Focus Rating (1-10)",
                        "session_duration": "Session Duration (min)"
                    }
                )

                # Add trend line
                if len(df) > 1:
                    correlation_coef = df["energy_level"].corr(df["focus_rating"])
                    fig.add_annotation(
                        text=f"Correlation: {correlation_coef:.2f}",
                        xref="paper", yref="paper",
                        x=0.02, y=0.98, showarrow=False,
                        bgcolor="rgba(255,255,255,0.8)"
                    )

                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Energy depletion patterns
            depletion_patterns = energy_analysis.get("energy_depletion", {})

            if depletion_patterns:
                # Show energy drop rates
                morning_drop = depletion_patterns.get("morning_drop_rate", 0)
                afternoon_drop = depletion_patterns.get("afternoon_drop_rate", 0)
                evening_drop = depletion_patterns.get("evening_drop_rate", 0)

                periods = ["Morning", "Afternoon", "Evening"]
                drop_rates = [morning_drop, afternoon_drop, evening_drop]

                fig = px.bar(
                    x=periods,
                    y=drop_rates,
                    title="Energy Depletion Rates",
                    labels={"x": "Time Period", "y": "Drop Rate (%/hour)"},
                    color=drop_rates,
                    color_continuous_scale="Reds"
                )

                fig.update_layout(height=300, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

        # Energy management recommendations
        st.markdown("**💡 Energy Management Strategies:**")

        energy_tips = energy_analysis.get("management_strategies", [])
        if energy_tips:
            for tip in energy_tips[:4]:
                st.info(f"• {tip}")
        else:
            st.info("• Take breaks every 25-30 minutes")
            st.info("• Schedule demanding tasks during high-energy periods")
            st.info("• Use physical activity to boost energy")
            st.info("• Monitor caffeine intake timing")


def _render_cognitive_load_analysis(tdah_advanced: Dict[str, Any], productivity_metrics: Dict[str, Any]):
    """Render cognitive load analysis for TDAH management."""

    st.markdown("#### 🧠 Cognitive Load & Task Complexity")

    cognitive_analysis = tdah_advanced.get("cognitive_analysis", {})

    if cognitive_analysis:
        col1, col2 = st.columns(2)

        with col1:
            # Cognitive load by task type
            load_by_type = cognitive_analysis.get("load_by_task_type", {})

            if load_by_type and PLOTLY_AVAILABLE:
                task_types = list(load_by_type.keys())
                load_scores = list(load_by_type.values())

                fig = px.bar(
                    x=task_types,
                    y=load_scores,
                    title="Cognitive Load by Task Type",
                    labels={"x": "Task Type", "y": "Cognitive Load (1-10)"},
                    color=load_scores,
                    color_continuous_scale="Viridis"
                )

                fig.update_layout(height=300, xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Multitasking impact
            multitasking_data = cognitive_analysis.get("multitasking_impact", {})

            if multitasking_data:
                single_task_performance = multitasking_data.get("single_task_score", 0)
                multi_task_performance = multitasking_data.get("multi_task_score", 0)
                impact_percentage = ((single_task_performance - multi_task_performance) / single_task_performance * 100) if single_task_performance > 0 else 0

                st.metric(
                    "🎯 Single-Task Focus",
                    f"{single_task_performance:.1f}/10",
                    "Optimal performance"
                )

                st.metric(
                    "🔄 Multi-Task Performance", 
                    f"{multi_task_performance:.1f}/10",
                    f"-{impact_percentage:.1f}% impact"
                )

                # Recommendation
                if impact_percentage > 20:
                    st.warning("💡 **Tip:** Focus on single tasks for better performance")
                else:
                    st.success("✅ **Good:** Multitasking impact is manageable")

        # Cognitive load management
        st.markdown("**🧠 Cognitive Load Management:**")

        complexity_recommendations = cognitive_analysis.get("complexity_recommendations", [])
        if complexity_recommendations:
            for rec in complexity_recommendations[:3]:
                st.info(f"• {rec}")
        else:
            st.info("• Break complex tasks into smaller chunks")
            st.info("• Use time-boxing for demanding cognitive work")
            st.info("• Alternate between high and low cognitive load tasks")


def _render_basic_tdah_metrics(analytics_data: Dict[str, Any]):
    """Render basic TDAH metrics when analytics engine is not available."""

    st.markdown("#### 🧠 Basic TDAH Metrics")
    st.info("💡 Enable the analytics engine for advanced TDAH insights and personalized recommendations.")

    timer_sessions = analytics_data.get("timer_sessions", [])
    if not timer_sessions:
        st.warning("No session data available for TDAH analysis.")
        return

    # Basic TDAH indicators
    col1, col2, col3 = st.columns(3)

    with col1:
        # Average session length
        session_durations = [s.get("planned_duration_minutes", 0) for s in timer_sessions]
        avg_duration = sum(session_durations) / len(session_durations) if session_durations else 0

        st.metric("⏱️ Avg Session Length", f"{avg_duration:.0f}min")

    with col2:
        # Interruption rate
        total_interruptions = sum(s.get("interruptions_count", 0) for s in timer_sessions)
        avg_interruptions = total_interruptions / len(timer_sessions) if timer_sessions else 0

        st.metric("🚫 Avg Interruptions", f"{avg_interruptions:.1f}/session")

    with col3:
        # Focus consistency
        focus_ratings = [s.get("focus_rating") for s in timer_sessions if s.get("focus_rating")]
        if focus_ratings:
            focus_std = pd.Series(focus_ratings).std() if PANDAS_AVAILABLE else 0
            consistency = max(0, 100 - (focus_std * 10))
            st.metric("🎯 Focus Consistency", f"{consistency:.0f}%")
        else:
            st.metric("🎯 Focus Consistency", "No data")


def _render_performance_metrics():
    """Render performance monitoring metrics in sidebar."""

    st.sidebar.markdown("### ⚡ Performance Monitor")

    # Cache statistics
    cache_size = _analytics_cache.size()
    st.sidebar.metric("Cache Size", f"{cache_size} items")

    # Performance metrics
    if hasattr(st.session_state, 'performance_metrics') and st.session_state.performance_metrics:
        metrics = st.session_state.performance_metrics

        st.sidebar.markdown("**Function Performance:**")
        for func_name, data in metrics.items():
            exec_time = data.get('execution_time', 0)

            # Color code based on performance
            if exec_time < 0.1:
                status = "🟢"
            elif exec_time < 0.5:
                status = "🟡"
            else:
                status = "🔴"

            st.sidebar.caption(f"{status} {func_name}: {exec_time:.3f}s")

    # Cache management
    col1, col2 = st.sidebar.columns(2)

    with col1:
        if st.button("🗑️ Clear Cache", key="clear_cache"):
            _analytics_cache.clear()
            st.sidebar.success("Cache cleared")

    with col2:
        if st.button("🔄 Refresh", key="perf_refresh"):
            st.rerun()

    # Performance optimization tips
    if cache_size == 0:
        st.sidebar.info("💡 **Tip:** Enable caching for faster performance")

    # Show optimization level
    chart_quality = getattr(st.session_state, 'performance_settings', {}).get('chart_quality', 'Medium')
    use_cache = getattr(st.session_state, 'performance_settings', {}).get('use_cache', True)

    optimization_score = 0
    if use_cache:
        optimization_score += 50
    if chart_quality == "Fast":
        optimization_score += 30
    elif chart_quality == "Medium":
        optimization_score += 20
    if cache_size > 0:
        optimization_score += 20

    st.sidebar.progress(optimization_score / 100)
    st.sidebar.caption(f"Optimization: {optimization_score}%")


if __name__ == "__main__":
    render_analytics_page()
