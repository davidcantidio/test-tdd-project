"""
📊 Analytics Engine Integration for Streamlit

Enhanced integration between Streamlit extension and existing analytics engine:
- Streamlit-optimized data formatting
- Caching integration
- Real-time analytics updates
- Performance optimization
- Fallback analytics when engine unavailable
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

# Evite mexer em sys.path; prefira imports relativos e flags de disponibilidade

# IMPORT HELL ELIMINATION: Using centralized dependency management
from .dependencies import (
    get_dependency_manager,
    safe_import_streamlit,
    safe_import_pandas,
    safe_import_plotly,
    streamlit_available,
    pandas_available,
    plotly_available,
    analytics_engine_available,
)

# Safe imports using dependency manager
st = safe_import_streamlit()
pd = safe_import_pandas()
plotly_modules = safe_import_plotly()
px = plotly_modules.express if plotly_modules else None
go = plotly_modules.graph_objects if plotly_modules else None

# Backward compatibility flags
STREAMLIT_AVAILABLE = streamlit_available()
PANDAS_AVAILABLE = pandas_available()
PLOTLY_AVAILABLE = plotly_available()
ANALYTICS_ENGINE_AVAILABLE = analytics_engine_available()

# Local imports - now using clean dependency management
from .database import DatabaseManager
from .cache import streamlit_cached, cache_database_query

# Get AnalyticsEngine if available
dependency_manager = get_dependency_manager()
AnalyticsEngine = dependency_manager.get_module("analytics_engine")


# Custom exceptions for proper error handling
class AnalyticsEngineError(Exception):
    """Base exception for analytics engine operations."""
    pass


class DataNotAvailableError(AnalyticsEngineError):
    """Raised when required data is not available."""
    pass


class ChartGenerationError(AnalyticsEngineError):
    """Raised when chart generation fails."""
    pass


class DatabaseAnalyticsError(AnalyticsEngineError):
    """Raised when database analytics operations fail."""
    pass


@dataclass
class AnalyticsReport:
    """Structured analytics report for Streamlit display."""
    
    period_days: int
    total_sessions: int
    total_focus_time: int  # minutes
    completed_tasks: int
    average_focus_rating: float
    total_points: int
    active_epics: int
    productivity_score: float
    trends: Dict[str, Any]
    recommendations: List[str]
    daily_metrics: List[Dict[str, Any]]
    generated_at: datetime


class StreamlitAnalyticsEngine:
    # Delegation to StreamlitAnalyticsEngineUiinteraction
    def __init__(self):
        self._streamlitanalyticsengineuiinteraction = StreamlitAnalyticsEngineUiinteraction()
    # Delegation to StreamlitAnalyticsEngineLogging
    def __init__(self):
        self._streamlitanalyticsenginelogging = StreamlitAnalyticsEngineLogging()
    # Delegation to StreamlitAnalyticsEngineErrorhandling
    def __init__(self):
        self._streamlitanalyticsengineerrorhandling = StreamlitAnalyticsEngineErrorhandling()
    # Delegation to StreamlitAnalyticsEngineFormatting
    def __init__(self):
        self._streamlitanalyticsengineformatting = StreamlitAnalyticsEngineFormatting()
    # Delegation to StreamlitAnalyticsEngineValidation
    def __init__(self):
        self._streamlitanalyticsenginevalidation = StreamlitAnalyticsEngineValidation()
    # Delegation to StreamlitAnalyticsEngineNetworking
    def __init__(self):
        self._streamlitanalyticsenginenetworking = StreamlitAnalyticsEngineNetworking()
    # Delegation to StreamlitAnalyticsEngineCalculation
    def __init__(self):
        self._streamlitanalyticsenginecalculation = StreamlitAnalyticsEngineCalculation()
    # Delegation to StreamlitAnalyticsEngineCaching
    def __init__(self):
        self._streamlitanalyticsenginecaching = StreamlitAnalyticsEngineCaching()
    # Delegation to StreamlitAnalyticsEngineConfiguration
    def __init__(self):
        self._streamlitanalyticsengineconfiguration = StreamlitAnalyticsEngineConfiguration()
    # Delegation to StreamlitAnalyticsEngineDataaccess
    def __init__(self):
        self._streamlitanalyticsenginedataaccess = StreamlitAnalyticsEngineDataaccess()
    """Streamlit-optimized analytics engine with fallback capabilities."""
    
    def __init__(self, db_manager: DatabaseManager = None):
        self.db_manager = db_manager
        self.engine = AnalyticsEngine() if ANALYTICS_ENGINE_AVAILABLE else None
    
    @streamlit_cached(ttl=600, show_spinner=True) if STREAMLIT_AVAILABLE else (lambda f: f)
    def generate_productivity_report(self, days: int = 30) -> AnalyticsReport:
        """Generate comprehensive productivity report with caching."""
        
        if self.engine and ANALYTICS_ENGINE_AVAILABLE:
            try:
                # Use existing analytics engine
                raw_report = self.engine.generate_productivity_report(days)
                return self._convert_to_streamlit_report(raw_report, days)
            except Exception as e:
                st.warning(f"Analytics engine error: {e}. Using fallback analytics.") if STREAMLIT_AVAILABLE else None
        
        # Fallback to database-based analytics
        return self._generate_fallback_report(days)
    
    @streamlit_cached(ttl=300) if STREAMLIT_AVAILABLE else (lambda f: f)
    def get_focus_trends(self, days: int = 14) -> Dict[str, Any]:
        """Get focus rating trends with caching."""
        
        if not self.db_manager:
            return {"error": "Database manager not available"}
        
        timer_sessions = self.db_manager.get_timer_sessions(days)
        
        # Analyze focus trends
        daily_focus = self._calculate_daily_focus_trends(timer_sessions)
        hourly_focus = self._calculate_hourly_focus_trends(timer_sessions)
        trend_direction = "up" if (daily_focus[-1]["avg"] - daily_focus[0]["avg"]) > 0 else "down" if daily_focus else "flat"

        return {
            "daily_focus": daily_focus,
            "hourly_focus": hourly_focus,
            "trend_direction": trend_direction,
            "best_focus_hour": max(hourly_focus, key=hourly_focus.get) if hourly_focus else None,
            "avg_daily_focus": sum(daily_focus.values()) / len(daily_focus) if daily_focus else 0,
        }
    
    @streamlit_cached(ttl=900) if STREAMLIT_AVAILABLE else lambda f: f
    def get_productivity_metrics(self, days: int = 30) -> Dict[str, Any]:
        """Get detailed productivity metrics with extended caching."""
        
        if not self.db_manager:
            return {"error": "Database manager not available"}
        
        # OPTIMIZED: Get data using combined query instead of 3 separate queries
        try:
            analytics_data = self._get_combined_analytics_data(days)
            timer_sessions = analytics_data["timer_sessions"]
            tasks = analytics_data["tasks"] 
            epics = analytics_data["epics"]
        except DatabaseAnalyticsError as e:
            if self.db_manager:
                self.db_manager.logger.warning(f"Combined analytics query failed, falling back to separate queries: {e}")
            # Fallback to original pattern if combined query fails
            timer_sessions = self.db_manager.get_timer_sessions(days)
            tasks = self.db_manager.get_tasks()
            epics = self.db_manager.get_epics()
        
        # Calculate comprehensive metrics
        metrics = {
            "focus_metrics": self._calculate_focus_metrics(timer_sessions),
            "task_metrics": self._calculate_task_metrics(tasks, days),
            "epic_metrics": self._calculate_epic_metrics(epics),
            "efficiency_metrics": self._calculate_efficiency_metrics(timer_sessions, tasks),
            "tdah_metrics": self._calculate_tdah_metrics(timer_sessions),
            "timeline_metrics": self._calculate_timeline_metrics(timer_sessions, tasks, days)
        }
        
        return metrics
    
    def get_real_time_stats(self) -> Dict[str, Any]:
        """Get real-time statistics (no caching)."""
        
        if not self.db_manager:
            return {"error": "Database manager not available"}
        
        # Today's stats
        today_sessions = self._get_today_sessions()
        
        # Current week stats
        week_sessions = self.db_manager.get_timer_sessions(7)
        
        return {
            "today": {
                "sessions": len(today_sessions),
                "focus_time": sum(s.get("planned_duration_minutes", 0) for s in today_sessions),
                "avg_focus": self._calc_avg_focus(today_sessions),
                "interruptions": sum(s.get("interruptions_count", 0) for s in today_sessions)
            },
            "this_week": {
                "sessions": len(week_sessions),
                "focus_time": sum(s.get("planned_duration_minutes", 0) for s in week_sessions),
                "avg_focus": self._calc_avg_focus(week_sessions),
                "total_interruptions": sum(s.get("interruptions_count", 0) for s in week_sessions)
            },
            "status": "active" if self._has_recent_activity() else "idle",
            "last_session": self._get_last_session_info()
        }
    
    def get_performance_insights(self, days: int = 30) -> List[Dict[str, Any]]:
        """Generate actionable performance insights."""
        
        if not self.db_manager:
            return []
        
        insights = []
        timer_sessions = self.db_manager.get_timer_sessions(days)
        
        # Focus rating insights
        focus_insight = self._analyze_focus_patterns(timer_sessions)
        if focus_insight:
            insights.append(focus_insight)
        
        # Interruption insights
        interruption_insight = self._analyze_interruption_patterns(timer_sessions)
        if interruption_insight:
            insights.append(interruption_insight)
        
        # Time-of-day insights
        time_insight = self._analyze_time_patterns(timer_sessions)
        if time_insight:
            insights.append(time_insight)
        
        # Session length insights
        length_insight = self._analyze_session_lengths(timer_sessions)
        if length_insight:
            insights.append(length_insight)
        
        return insights
    
    def get_streamlit_charts(self, days: int = 30) -> Dict[str, Any]:
        """Generate Plotly charts optimized for Streamlit display."""
        
        if not PLOTLY_AVAILABLE:
            return {"error": "Plotly not available for charts"}
        
        charts = {}
        
        # OPTIMIZED: Get data using combined analytics data to avoid multiple queries
        try:
            analytics_data = self._get_combined_analytics_data(days)
            # Use the combined data for chart generation
            productivity_metrics = self.get_productivity_metrics(days)  # This now uses cached combined data
            focus_trends = self.get_focus_trends(days)
        except DatabaseAnalyticsError as e:
            if self.db_manager:
                self.db_manager.logger.warning(f"Chart data optimization failed, using fallback: {e}")
            # Fallback to original pattern
            productivity_metrics = self.get_productivity_metrics(days)
            focus_trends = self.get_focus_trends(days)
        
        # Focus trend chart
        if focus_trends.get("daily_focus"):
            charts["focus_trend"] = self._create_focus_trend_chart(focus_trends["daily_focus"])
        
        # Productivity overview
        if productivity_metrics.get("focus_metrics"):
            charts["productivity_overview"] = self._create_productivity_chart(productivity_metrics)
        
        # TDAH insights chart
        if productivity_metrics.get("tdah_metrics"):
            charts["tdah_insights"] = self._create_tdah_chart(productivity_metrics["tdah_metrics"])
        
        return charts
    
    # Helper methods
    
    def _convert_to_streamlit_report(self, raw_report: Dict[str, Any], days: int) -> AnalyticsReport:
        """Convert raw analytics report to Streamlit-optimized format."""
        
        return AnalyticsReport(
            period_days=days,
            total_sessions=raw_report.get("total_sessions", 0),
            total_focus_time=raw_report.get("total_focus_time", 0),
            completed_tasks=raw_report.get("completed_tasks", 0),
            average_focus_rating=raw_report.get("average_focus_rating", 0),
            total_points=raw_report.get("total_points", 0),
            active_epics=raw_report.get("active_epics", 0),
            productivity_score=raw_report.get("productivity_score", 0),
            trends=raw_report.get("trends", {}),
            recommendations=raw_report.get("recommendations", []),
            daily_metrics=raw_report.get("daily_metrics", []),
            generated_at=datetime.now()
        )
    
    def _generate_fallback_report(self, days: int) -> AnalyticsReport:
        """Generate analytics report using database queries when engine unavailable."""
        
        if not self.db_manager:
            # Return empty report
            return AnalyticsReport(
                period_days=days,
                total_sessions=0,
                total_focus_time=0,
                completed_tasks=0,
                average_focus_rating=0,
                total_points=0,
                active_epics=0,
                productivity_score=0,
                trends={},
                recommendations=["Database not available"],
                daily_metrics=[],
                generated_at=datetime.now()
            )
        
        # Get data from database - OPTIMIZED: Single combined query instead of 4 separate queries
        analytics_data = self._get_combined_analytics_data(days)
        
        # Extract data from optimized combined query
        timer_sessions = analytics_data["timer_sessions"]
        tasks = analytics_data["tasks"]
        epics = analytics_data["epics"]
        user_stats = analytics_data["user_stats"]
        
        # Calculate metrics
        total_sessions = len(timer_sessions)
        total_focus_time = sum(s.get("planned_duration_minutes", 0) for s in timer_sessions)
        completed_tasks = len([t for t in tasks if t.get("status") == "completed"])
        
        focus_ratings = [s.get("focus_rating") for s in timer_sessions if s.get("focus_rating")]
        average_focus_rating = sum(focus_ratings) / len(focus_ratings) if focus_ratings else 0
        
        total_points = user_stats.get("total_points", 0)
        active_epics = len([e for e in epics if e.get("status") == "active"])
        
        # Calculate productivity score (0-100)
        productivity_score = self._calculate_productivity_score(
            average_focus_rating, total_sessions, completed_tasks, days
        )
        
        # Generate trends
        trends = self._calculate_trends(timer_sessions, tasks)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            timer_sessions, average_focus_rating, total_sessions, days
        )
        
        # Daily metrics
        daily_metrics = self._calculate_daily_metrics(timer_sessions, tasks)
        
        return AnalyticsReport(
            period_days=days,
            total_sessions=total_sessions,
            total_focus_time=total_focus_time,
            completed_tasks=completed_tasks,
            average_focus_rating=average_focus_rating,
            total_points=total_points,
            active_epics=active_epics,
            productivity_score=productivity_score,
            trends=trends,
            recommendations=recommendations,
            daily_metrics=daily_metrics,
            generated_at=datetime.now()
        )
    
    def _calculate_daily_focus_trends(self, timer_sessions: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate daily focus rating trends."""
        
        from collections import defaultdict
        daily_focus = defaultdict(list)
        
        for session in timer_sessions:
            if session.get("focus_rating") and session.get("started_at"):
                try:
                    date = session["started_at"][:10]  # YYYY-MM-DD
                    daily_focus[date].append(session["focus_rating"])
                except (IndexError, KeyError):
                    continue
        
        # Average focus by day
        return {
            date: sum(ratings) / len(ratings)
            for date, ratings in daily_focus.items()
        }
    
    def _calculate_hourly_focus_trends(self, timer_sessions: List[Dict[str, Any]]) -> Dict[int, float]:
        """Calculate hourly focus rating trends."""
        
        from collections import defaultdict
        hourly_focus = defaultdict(list)
        
        for session in timer_sessions:
            if session.get("focus_rating") and session.get("started_at"):
                try:
                    if "T" in session["started_at"]:
                        hour = int(session["started_at"].split("T")[1][:2])
                    else:
                        hour = int(session["started_at"].split(" ")[1][:2])
                    
                    hourly_focus[hour].append(session["focus_rating"])
                except (ValueError, IndexError, KeyError):
                    continue
        
        # Average focus by hour
        return {
            hour: sum(ratings) / len(ratings)
            for hour, ratings in hourly_focus.items()
        }
    
    def _calculate_productivity_score(self, avg_focus: float, sessions: int, tasks: int, days: int) -> float:
        """Calculate overall productivity score (0-100)."""
        
        # Weight factors
        focus_weight = 0.4
        consistency_weight = 0.3
        completion_weight = 0.3
        
        # Focus component (0-10 -> 0-100)
        focus_score = (avg_focus / 10) * 100
        
        # Consistency component (sessions per day)
        sessions_per_day = sessions / days if days > 0 else 0
        consistency_score = min(sessions_per_day * 20, 100)  # 5 sessions/day = 100%
        
        # Completion component (tasks per day)
        tasks_per_day = tasks / days if days > 0 else 0
        completion_score = min(tasks_per_day * 25, 100)  # 4 tasks/day = 100%
        
        # Weighted average
        productivity_score = (
            focus_score * focus_weight +
            consistency_score * consistency_weight +
            completion_score * completion_weight
        )
        
        return round(productivity_score, 1)
    
    def _calculate_trends(self, timer_sessions: List[Dict], tasks: List[Dict]) -> Dict[str, Any]:
        """Calculate various trends from data."""
        
        trends = {}
        
        # Focus trend (last 7 days vs previous 7 days)
        if len(timer_sessions) >= 14:
            recent_focus = self._calc_avg_focus(timer_sessions[:7])
            previous_focus = self._calc_avg_focus(timer_sessions[7:14])
            trends["focus_trend"] = recent_focus - previous_focus
        
        # Session frequency trend
        trends["session_frequency"] = self._calculate_session_frequency_trend(timer_sessions)
        
        return trends
    
    def _generate_recommendations(self, timer_sessions: List[Dict], avg_focus: float, 
                                 total_sessions: int, days: int) -> List[str]:
        """Generate actionable recommendations."""
        
        recommendations = []
        
        # Focus-based recommendations
        if avg_focus < 6:
            recommendations.append("Focus rating is low. Try shorter sessions or eliminate distractions.")
        elif avg_focus > 8:
            recommendations.append("Great focus! Consider extending session length for deeper work.")
        
        # Session frequency recommendations
        sessions_per_day = total_sessions / days if days > 0 else 0
        if sessions_per_day < 2:
            recommendations.append("Try to have at least 2 focus sessions per day for better productivity.")
        elif sessions_per_day > 8:
            recommendations.append("You're doing many sessions. Ensure you're taking adequate breaks.")
        
        # TDAH-specific recommendations
        interruptions = [s.get("interruptions_count", 0) for s in timer_sessions]
        avg_interruptions = sum(interruptions) / len(interruptions) if interruptions else 0
        
        if avg_interruptions > 3:
            recommendations.append("High interruption rate. Try using 'Do Not Disturb' mode during focus sessions.")
        
        return recommendations
    
    def _calculate_daily_metrics(self, timer_sessions: List[Dict], tasks: List[Dict]) -> List[Dict[str, Any]]:
        """Calculate daily metrics for the report."""
        
        from collections import defaultdict
        daily_data = defaultdict(lambda: {
            "date": "",
            "sessions": 0,
            "focus_time": 0,
            "avg_focus": 0,
            "tasks_completed": 0,
            "interruptions": 0
        })
        
        # Process timer sessions
        for session in timer_sessions:
            if session.get("started_at"):
                try:
                    date = session["started_at"][:10]
                    daily_data[date]["date"] = date
                    daily_data[date]["sessions"] += 1
                    daily_data[date]["focus_time"] += session.get("planned_duration_minutes", 0)
                    daily_data[date]["interruptions"] += session.get("interruptions_count", 0)
                    
                    # Calculate running average for focus
                    if session.get("focus_rating"):
                        current_sessions = daily_data[date]["sessions"]
                        current_avg = daily_data[date]["avg_focus"]
                        new_avg = ((current_avg * (current_sessions - 1)) + session["focus_rating"]) / current_sessions
                        daily_data[date]["avg_focus"] = new_avg
                        
                except (IndexError, KeyError):
                    continue
        
        # Process completed tasks
        for task in tasks:
            if task.get("status") == "completed" and task.get("completed_at"):
                try:
                    date = task["completed_at"][:10]
                    if date in daily_data:
                        daily_data[date]["tasks_completed"] += 1
                except (IndexError, KeyError):
                    continue
        
        return list(daily_data.values())
    
    # Additional helper methods for specific calculations
    
    def _get_today_sessions(self) -> List[Dict[str, Any]]:
        """Get today's timer sessions."""
        if not self.db_manager:
            return []
        
        all_sessions = self.db_manager.get_timer_sessions(1)
        today_str = datetime.now().strftime("%Y-%m-%d")
        
        return [
            s for s in all_sessions 
            if s.get("started_at", "").startswith(today_str)
        ]
    
    def _calc_avg_focus(self, sessions: List[Dict[str, Any]]) -> float:
        """Calculate average focus rating."""
        ratings = [s.get("focus_rating") for s in sessions if s.get("focus_rating")]
        return sum(ratings) / len(ratings) if ratings else 0
    
    def _has_recent_activity(self) -> bool:
        """Check if there's been recent activity (last 2 hours)."""
        if not self.db_manager:
            return False
        
        recent_sessions = self.db_manager.get_timer_sessions(1)  # Last day
        if not recent_sessions:
            return False
        
        # Check if last session was within 2 hours
        try:
            last_session = recent_sessions[0]
            last_time = datetime.fromisoformat(last_session.get("started_at", ""))
            return (datetime.now() - last_time).total_seconds() < 7200  # 2 hours
        except (ValueError, TypeError):
            return False
    
    def _get_last_session_info(self) -> Dict[str, Any]:
        """Get information about the last session."""
        if not self.db_manager:
            return {}
        
        recent_sessions = self.db_manager.get_timer_sessions(1)
        if not recent_sessions:
            return {}
        
        last_session = recent_sessions[0]
        return {
            "started_at": last_session.get("started_at", ""),
            "duration": last_session.get("planned_duration_minutes", 0),
            "focus_rating": last_session.get("focus_rating", 0),
            "task_reference": last_session.get("task_reference", "General")
        }
    
    # Analysis methods for insights
    
    def _analyze_focus_patterns(self, sessions: List[Dict]) -> Optional[Dict[str, Any]]:
        """Analyze focus patterns for insights."""
        focus_ratings = [s.get("focus_rating") for s in sessions if s.get("focus_rating")]
        
        if len(focus_ratings) < 5:
            return None
        
        avg_focus = sum(focus_ratings) / len(focus_ratings)
        
        insight = {
            "type": "focus_pattern",
            "title": "Focus Performance",
            "priority": "medium"
        }
        
        if avg_focus >= 8:
            insight["message"] = f"Excellent focus performance ({avg_focus:.1f}/10). Keep up the great work!"
            insight["icon"] = "🌟"
            insight["priority"] = "low"
        elif avg_focus >= 6:
            insight["message"] = f"Good focus levels ({avg_focus:.1f}/10). Consider techniques to reach 8+ consistently."
            insight["icon"] = "👍"
        else:
            insight["message"] = f"Focus needs improvement ({avg_focus:.1f}/10). Try shorter sessions or reduce distractions."
            insight["icon"] = "⚠️"
            insight["priority"] = "high"
        
        return insight
    
    def _analyze_interruption_patterns(self, sessions: List[Dict]) -> Optional[Dict[str, Any]]:
        """Analyze interruption patterns."""
        interruptions = [s.get("interruptions_count", 0) for s in sessions]
        
        if not interruptions:
            return None
        
        avg_interruptions = sum(interruptions) / len(interruptions)
        
        insight = {
            "type": "interruption_pattern",
            "title": "Interruption Analysis"
        }
        
        if avg_interruptions <= 1:
            insight["message"] = f"Low interruption rate ({avg_interruptions:.1f}/session). Great focus environment!"
            insight["icon"] = "🔇"
            insight["priority"] = "low"
        elif avg_interruptions <= 3:
            insight["message"] = f"Moderate interruptions ({avg_interruptions:.1f}/session). Room for improvement."
            insight["icon"] = "📱"
            insight["priority"] = "medium"
        else:
            insight["message"] = f"High interruption rate ({avg_interruptions:.1f}/session). Consider 'Do Not Disturb' settings."
            insight["icon"] = "🚫"
            insight["priority"] = "high"
        
        return insight
    
    def _get_combined_analytics_data(self, days: int) -> Dict[str, Any]:
        """Get all analytics data in a single optimized query to fix N+1 problem.
        
        Args:
            days: Number of days to look back
            
        Returns:
            Combined data dictionary with timer_sessions, tasks, epics, user_stats
            
        Raises:
            DatabaseOperationError: If database operation fails
        """
        try:
            from datetime import datetime, timedelta
            date_filter = datetime.now() - timedelta(days=days)
            
            # Single optimized query combining all needed data
            combined_query = """
                SELECT 
                    -- Timer sessions data
                    ws.id as session_id,
                    ws.start_time,
                    ws.end_time,
                    ws.planned_duration_minutes,
                    ws.focus_rating,
                    ws.energy_level,
                    ws.mood_rating,
                    ws.status as session_status,
                    ws.session_type,
                    
                    -- Task data
                    t.id as task_id,
                    t.title as task_title,
                    t.status as task_status,
                    
                    -- Epic data
                    e.id as epic_id,
                    e.title as epic_title,
                    e.status as epic_status
                    
                FROM work_sessions ws
                LEFT JOIN framework_tasks t ON ws.task_id = t.id
                LEFT JOIN framework_epics e ON t.epic_id = e.id
                WHERE ws.start_time >= ?
                ORDER BY ws.start_time DESC
            """
            
            # Execute optimized query
            raw_data = self.db_manager.execute_query(combined_query, (date_filter,))
            
            # Separate data into logical groups
            timer_sessions = []
            tasks_dict = {}
            epics_dict = {}
            
            for row in raw_data:
                # Timer session data
                session = {
                    "id": row.get("session_id"),
                    "start_time": row.get("start_time"),
                    "end_time": row.get("end_time"),
                    "planned_duration_minutes": row.get("planned_duration_minutes"),
                    "focus_rating": row.get("focus_rating"),
                    "energy_level": row.get("energy_level"),
                    "mood_rating": row.get("mood_rating"),
                    "status": row.get("session_status"),
                    "session_type": row.get("session_type")
                }
                timer_sessions.append(session)
                
                # Task data (deduplicate)
                if row.get("task_id") and row.get("task_id") not in tasks_dict:
                    tasks_dict[row.get("task_id")] = {
                        "id": row.get("task_id"),
                        "title": row.get("task_title"),
                        "status": row.get("task_status")
                    }
                
                # Epic data (deduplicate)
                if row.get("epic_id") and row.get("epic_id") not in epics_dict:
                    epics_dict[row.get("epic_id")] = {
                        "id": row.get("epic_id"),
                        "title": row.get("epic_title"),
                        "status": row.get("epic_status")
                    }
            
            # Get user stats separately (small query)
            user_stats_query = "SELECT total_points FROM user_stats ORDER BY id DESC LIMIT 1"
            user_stats_result = self.db_manager.execute_query(user_stats_query)
            user_stats = {"total_points": user_stats_result[0].get("total_points", 0) if user_stats_result else 0}
            
            return {
                "timer_sessions": timer_sessions,
                "tasks": list(tasks_dict.values()),
                "epics": list(epics_dict.values()),
                "user_stats": user_stats
            }
            
        except (AttributeError, TypeError) as e:
            if self.db_manager:
                self.db_manager.logger.error(f"Database manager error in combined analytics query: {e}")
            raise DatabaseAnalyticsError(f"Database operation failed: {e}") from e
        except Exception as e:
            if self.db_manager:
                self.db_manager.logger.error(f"Unexpected error in combined analytics query: {e}")
            raise DatabaseAnalyticsError(f"Unexpected database error: {e}") from e


# Factory function for easy instantiation
def create_analytics_engine(db_manager: DatabaseManager = None) -> StreamlitAnalyticsEngine:
    """Create a StreamlitAnalyticsEngine instance."""
    return StreamlitAnalyticsEngine(db_manager)


# Convenience functions for direct use
@streamlit_cached(ttl=600) if STREAMLIT_AVAILABLE else lambda f: f
def get_productivity_summary(db_manager: DatabaseManager, days: int = 7) -> Dict[str, Any]:
    """Get a quick productivity summary."""
    engine = create_analytics_engine(db_manager)
    report = engine.generate_productivity_report(days)
    
    return {
        "focus_time_hours": report.total_focus_time / 60,
        "sessions": report.total_sessions,
        "avg_focus": report.average_focus_rating,
        "productivity_score": report.productivity_score,
        "top_recommendation": report.recommendations[0] if report.recommendations else "Keep up the good work!"
    }


if __name__ == "__main__":
    # Test the analytics integration
    logging.info("StreamlitAnalyticsEngine loaded successfully")
    logging.info(f"Analytics Engine Available: {ANALYTICS_ENGINE_AVAILABLE}")
    logging.info(f"Streamlit Available: {STREAMLIT_AVAILABLE}")
    logging.info(f"Plotly Available: {PLOTLY_AVAILABLE}")
