"""
📊 Analytics & Metrics Cards

Analytics dashboard components for KPIs, progress indicators, and metrics visualization.
UI-only pattern: receives prepared data and renders cards without any database queries.
"""

from typing import Dict, Any, TypedDict, Optional

# Graceful streamlit import
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False
    st = None

# Safe imports for dashboard widgets
try:
    from .dashboard_widgets import DailyStats, ProgressRing, SparklineChart
    DASHBOARD_WIDGETS_AVAILABLE = True
except ImportError:
    DASHBOARD_WIDGETS_AVAILABLE = False
    DailyStats = None
    ProgressRing = None
    SparklineChart = None

# Type definitions for better type safety
class AnalyticsStats(TypedDict, total=False):
    """Type definition for analytics statistics data."""
    completed_tasks: int
    weekly_completion: float
    focus_series: list[float]
    total_tasks: int
    focus_time_hours: float
    productivity_score: float
    current_streak: int

# Constants for consistent error messages
class ErrorMessages:
    """Centralized error message constants."""
    DAILY_STATS_UNAVAILABLE = "📈 **Daily Stats** (temporarily unavailable)"
    WEEKLY_PROGRESS_UNAVAILABLE = "📊 **Weekly Progress** (temporarily unavailable)"
    FOCUS_TREND_UNAVAILABLE = "📉 **Focus Trend** (temporarily unavailable)"
    ANALYTICS_UNAVAILABLE = "📊 Analytics temporarily unavailable"
    KPI_SUMMARY_UNAVAILABLE = "📈 KPI Summary temporarily unavailable"
    NO_FOCUS_DATA = "No focus data available"


def _safe_float_conversion(value: Any, default: float = 0.0) -> float:
    """
    Safely convert value to float with fallback.
    Extracted from streamlit_app._as_float() for reusability.
    """
    try:
        return float(value if value is not None else default)
    except (ValueError, TypeError, OverflowError):
        return default

def _validate_stats_input(stats: Any) -> Dict[str, Any]:
    """
    Validate and sanitize stats input parameter.
    
    Args:
        stats: Input statistics data
        
    Returns:
        Validated dictionary or empty dict if invalid
    """
    if stats is None:
        return {}
    if not isinstance(stats, dict):
        return {}
    return stats

def _safe_session_state_access(key: str, default: Any = None) -> Any:
    """
    Safely access Streamlit session state with fallback.
    USES SESSION_MANAGER ABSTRACTION - NO DIRECT ACCESS
    """
    try:
        from ..utils.session_manager import get_session_value
        return get_session_value(key, default)
    except ImportError:
        return default


def render_daily_stats_card(stats: Dict[str, Any]) -> None:
    """Render daily statistics card with fallback."""
    if not STREAMLIT_AVAILABLE:
        return
    
    validated_stats = _validate_stats_input(stats)
    
    try:
        if DASHBOARD_WIDGETS_AVAILABLE and DailyStats:
            DailyStats.render(stats=validated_stats)
        else:
            # Fallback rendering
            st.markdown("### 📈 Daily Stats")
            completed = validated_stats.get("completed_tasks", 0)
            st.metric("Completed Tasks", str(completed))
    except Exception:
        st.markdown(ErrorMessages.DAILY_STATS_UNAVAILABLE)


def render_progress_ring_card(stats: Dict[str, Any]) -> None:
    """Render weekly progress ring with fallback."""
    if not STREAMLIT_AVAILABLE:
        return
    
    validated_stats = _validate_stats_input(stats)
    
    try:
        weekly_completion = _safe_float_conversion(validated_stats.get("weekly_completion"), 0.0)
        
        if DASHBOARD_WIDGETS_AVAILABLE and ProgressRing:
            ProgressRing(
                value=weekly_completion,
                label="Conclusão da Semana",
            )
        else:
            # Fallback rendering
            st.markdown("### 📊 Weekly Progress")
            percentage = int(weekly_completion * 100)
            st.progress(weekly_completion)
            st.markdown(f"**{percentage}%** complete this week")
    except Exception:
        st.markdown(ErrorMessages.WEEKLY_PROGRESS_UNAVAILABLE)


def render_sparkline_chart_card(stats: Dict[str, Any]) -> None:
    """Render focus sparkline chart with fallback."""
    if not STREAMLIT_AVAILABLE:
        return
    
    validated_stats = _validate_stats_input(stats)
    
    try:
        focus_series = validated_stats.get("focus_series") or []
        
        if DASHBOARD_WIDGETS_AVAILABLE and SparklineChart:
            SparklineChart(series=focus_series, title="Foco (7d)")
        else:
            # Fallback rendering
            st.markdown("### 📉 Focus Trend (7d)")
            if focus_series:
                # Simplified average calculation (focus_series already checked for truthiness)
                avg_focus = sum(focus_series) / len(focus_series)
                st.metric("Avg Focus", f"{avg_focus:.1f}h")
            else:
                st.info(ErrorMessages.NO_FOCUS_DATA)
    except Exception:
        st.markdown(ErrorMessages.FOCUS_TREND_UNAVAILABLE)


def render_analytics_cards(stats: Optional[Dict[str, Any]] = None) -> None:
    """
    Main analytics cards renderer - UI only with prepared data.
    
    Args:
        stats: Dictionary containing analytics data (KPIs, metrics, series)
               Expected keys: completed_tasks, weekly_completion, focus_series
               Can be None for graceful degradation.
    """
    if not STREAMLIT_AVAILABLE:
        return
    
    try:
        # Validate and ensure we have safe data
        validated_stats = _validate_stats_input(stats)
        
        # Create 3-column layout for analytics cards
        c1, c2, c3 = st.columns([1, 1, 1])
        
        with c1:
            render_daily_stats_card(validated_stats)
            
        with c2:
            render_progress_ring_card(validated_stats)
            
        with c3:
            render_sparkline_chart_card(validated_stats)
            
    except Exception as e:
        # Graceful fallback for entire analytics section
        st.info(ErrorMessages.ANALYTICS_UNAVAILABLE)
        
        # Optional debug info with safer session state access
        if _safe_session_state_access("show_debug_info", False):
            st.error(f"Analytics error: {str(e)}")


def render_kpi_summary(kpis: Optional[Dict[str, Any]] = None) -> None:
    """
    Render high-level KPI summary cards.
    Alternative layout for executive dashboards.
    
    Args:
        kpis: Dictionary containing KPI data
              Expected keys: total_tasks, completed_tasks, focus_time_hours,
                           productivity_score, current_streak
              Can be None for graceful degradation.
    """
    if not STREAMLIT_AVAILABLE:
        return
    
    try:
        validated_metrics = _validate_stats_input(kpis)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_tasks = validated_metrics.get("total_tasks", 0)
            completed_tasks = validated_metrics.get("completed_tasks", 0)
            st.metric("Tasks Completed", completed_tasks, f"of {total_tasks}")
        
        with col2:
            focus_time = _safe_float_conversion(validated_metrics.get("focus_time_hours"), 0.0)
            st.metric("Focus Time", f"{focus_time:.1f}h")
        
        with col3:
            productivity = _safe_float_conversion(validated_metrics.get("productivity_score"), 0.0)
            st.metric("Productivity", f"{productivity:.1f}%")
        
        with col4:
            streak = validated_metrics.get("current_streak", 0)
            st.metric("Current Streak", f"{streak} days")
            
    except Exception:
        st.info(ErrorMessages.KPI_SUMMARY_UNAVAILABLE)


# Backward compatibility aliases
render_analytics_row = render_analytics_cards
render_metrics_cards = render_analytics_cards