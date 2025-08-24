"""
📊 Analytics Service Layer

Business logic for analytics, reporting, and metrics.
Provides insights into productivity, progress, and performance across the TDD framework.
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, date, timedelta
import json
from collections import defaultdict
import statistics
from dataclasses import asdict, is_dataclass
from collections.abc import Iterable, Mapping

from .base import (
    BaseService, ServiceResult, ServiceError, ServiceErrorType,
    BaseRepository
)
from ..utils.database import DatabaseManager
from ..config.constants import TaskStatus, EpicStatus, ProjectStatus, TDDPhase
# Auth imports
from streamlit_extension.auth.middleware import require_auth, require_admin
from streamlit_extension.auth.user_model import UserRole


def _ensure_dict_list(data: Any) -> List[Dict[str, Any]]:
    """Ensure an iterable contains only dictionaries."""
    if not data:
        return []

    try:
        iterable = data if isinstance(data, Iterable) and not isinstance(data, (str, bytes, dict)) else list(data)
    except Exception:
        iterable = []

    normalized: List[Dict[str, Any]] = []
    for item in iterable:
        if isinstance(item, dict):
            normalized.append(item)
        elif hasattr(item, "_asdict"):
            normalized.append(item._asdict())
        elif is_dataclass(item):
            normalized.append(asdict(item))
        elif isinstance(item, Mapping):
            normalized.append(dict(item))
        elif hasattr(item, "__dict__"):
            normalized.append(vars(item))
        elif isinstance(item, tuple):
            normalized.append({f"field_{i}": v for i, v in enumerate(item)})
    return normalized

class AnalyticsRepository(BaseRepository):
    # Delegation to AnalyticsRepositoryDataaccess
    def __init__(self):
        self._analyticsrepositorydataaccess = AnalyticsRepositoryDataaccess()
    # Delegation to AnalyticsRepositoryLogging
    def __init__(self):
        self._analyticsrepositorylogging = AnalyticsRepositoryLogging()
    # Delegation to AnalyticsRepositoryErrorhandling
    def __init__(self):
        self._analyticsrepositoryerrorhandling = AnalyticsRepositoryErrorhandling()
    # Delegation to AnalyticsRepositoryCalculation
    def __init__(self):
        self._analyticsrepositorycalculation = AnalyticsRepositoryCalculation()
    # Delegation to AnalyticsRepositoryFormatting
    def __init__(self):
        self._analyticsrepositoryformatting = AnalyticsRepositoryFormatting()
    """Repository for analytics data access operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        super().__init__(db_manager)
    
    
    def get_project_progress_metrics(self, project_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get project progress metrics."""
        try:
            if project_id:
                where_clause = "WHERE p.id = ?"
                params = [project_id]
            else:
                where_clause = ""
                params = []
            
            query = f"""
                SELECT 
                    p.id as project_id,
                    p.name as project_name,
                    p.status as project_status,
                    COUNT(DISTINCT e.id) as total_epics,
                    COUNT(DISTINCT t.id) as total_tasks,
                    SUM(CASE WHEN e.status = 'completed' THEN 1 ELSE 0 END) as completed_epics,
                    SUM(CASE WHEN t.status = 'completed' THEN 1 ELSE 0 END) as completed_tasks,
                    AVG(CASE WHEN t.status = 'completed' THEN 100.0 ELSE 0.0 END) as completion_percentage,
                    SUM(COALESCE(ws.total_time, 0)) as total_time_minutes,
                    SUM(t.estimated_hours) as total_estimated_hours
                FROM framework_projects p
                LEFT JOIN framework_epics e ON p.id = e.project_id
                LEFT JOIN framework_tasks t ON e.id = t.epic_id
                LEFT JOIN (
                    SELECT task_id, SUM(duration_minutes) as total_time
                    FROM work_sessions
                    GROUP BY task_id
                ) ws ON t.id = ws.task_id
                {where_clause}
                GROUP BY p.id, p.name, p.status
                ORDER BY p.created_at DESC
            """
            
            result = self.db_manager.execute_query(query, params)
            return _ensure_dict_list(result)
            
        except Exception as e:
            self.db_manager.logger.error(f"Error getting project progress metrics: {e}")
            return []
    
    def get_tdd_cycle_metrics(self, days: int = 30) -> Dict[str, Any]:
        """Get TDD cycle completion metrics."""
        try:
            date_filter = datetime.now() - timedelta(days=days)
            
            # Tasks by TDD phase
            phase_query = """
                SELECT 
                    t.tdd_phase,
                    COUNT(*) as task_count,
                    AVG(COALESCE(ws.total_time, 0)) as avg_time_minutes
                FROM framework_tasks t
                LEFT JOIN (
                    SELECT task_id, SUM(duration_minutes) as total_time
                    FROM work_sessions
                    GROUP BY task_id
                ) ws ON t.id = ws.task_id
                WHERE t.created_at >= ?
                GROUP BY t.tdd_phase
            """
            
            phase_results = _ensure_dict_list(
                self.db_manager.execute_query(phase_query, [date_filter])
            )
            
            # TDD cycle completions (tasks that went through full RED -> GREEN -> REFACTOR)
            cycle_query = """
                SELECT 
                    COUNT(*) as completed_cycles,
                    AVG(COALESCE(ws.total_time, 0)) as avg_cycle_time
                FROM framework_tasks t
                LEFT JOIN (
                    SELECT task_id, SUM(duration_minutes) as total_time
                    FROM work_sessions
                    GROUP BY task_id
                ) ws ON t.id = ws.task_id
                WHERE t.status = 'completed' 
                AND t.tdd_phase = 'refactor'
                AND t.created_at >= ?
            """
            
            cycle_results = _ensure_dict_list(
                self.db_manager.execute_query(cycle_query, [date_filter])
            )
            
            return {
                'phase_distribution': {row['tdd_phase']: row['task_count'] for row in phase_results},
                'phase_avg_times': {row['tdd_phase']: row['avg_time_minutes'] for row in phase_results},
                'completed_cycles': cycle_results[0]['completed_cycles'] if cycle_results else 0,
                'avg_cycle_time': cycle_results[0]['avg_cycle_time'] if cycle_results else 0
            }
            
        except Exception as e:
            self.db_manager.logger.error(f"Error getting TDD cycle metrics: {e}")
            return {}
    
    def get_productivity_metrics(self, days: int = 30) -> Dict[str, Any]:
        """Get productivity and time tracking metrics."""
        try:
            date_filter = datetime.now() - timedelta(days=days)
            
            # Daily productivity
            daily_query = """
                SELECT 
                    DATE(ws.start_time) as work_date,
                    COUNT(DISTINCT ws.task_id) as tasks_worked,
                    COUNT(ws.id) as total_sessions,
                    SUM(ws.duration_minutes) as total_minutes,
                    AVG(ws.duration_minutes) as avg_session_minutes
                FROM work_sessions ws
                WHERE ws.start_time >= ?
                GROUP BY DATE(ws.start_time)
                ORDER BY work_date DESC
            """
            
            daily_results = _ensure_dict_list(
                self.db_manager.execute_query(daily_query, [date_filter])
            )
            
            # Focus patterns (sessions by hour of day)
            focus_query = """
                SELECT 
                    CAST(strftime('%H', ws.start_time) AS INTEGER) as hour_of_day,
                    COUNT(*) as session_count,
                    SUM(ws.duration_minutes) as total_minutes,
                    AVG(ws.duration_minutes) as avg_session_minutes
                FROM work_sessions ws
                WHERE ws.start_time >= ?
                GROUP BY hour_of_day
                ORDER BY hour_of_day
            """
            
            focus_results = _ensure_dict_list(
                self.db_manager.execute_query(focus_query, [date_filter])
            )
            
            # Estimate accuracy
            accuracy_query = """
                SELECT 
                    t.estimated_hours,
                    COALESCE(ws.total_time, 0) / 60.0 as actual_hours,
                    ABS(t.estimated_hours - COALESCE(ws.total_time, 0) / 60.0) as variance_hours
                FROM framework_tasks t
                LEFT JOIN (
                    SELECT task_id, SUM(duration_minutes) as total_time
                    FROM work_sessions
                    GROUP BY task_id
                ) ws ON t.id = ws.task_id
                WHERE t.estimated_hours IS NOT NULL 
                AND t.estimated_hours > 0
                AND t.created_at >= ?
            """
            
            accuracy_results = _ensure_dict_list(
                self.db_manager.execute_query(accuracy_query, [date_filter])
            )
            
            return {
                'daily_productivity': daily_results,
                'focus_patterns': focus_results,
                'estimate_accuracy': accuracy_results
            }
            
        except Exception as e:
            self.db_manager.logger.error(f"Error getting productivity metrics: {e}")
            return {}
    
    def get_gamification_metrics(self, days: int = 30) -> Dict[str, Any]:
        """Get gamification and achievement metrics."""
        try:
            date_filter = datetime.now() - timedelta(days=days)
            
            # Epic completion and points
            epic_query = """
                SELECT 
                    e.difficulty,
                    e.priority,
                    e.points,
                    e.status,
                    COUNT(t.id) as total_tasks,
                    SUM(CASE WHEN t.status = 'completed' THEN 1 ELSE 0 END) as completed_tasks,
                    SUM(COALESCE(ws.total_time, 0)) as total_time_minutes
                FROM framework_epics e
                LEFT JOIN framework_tasks t ON e.id = t.epic_id
                LEFT JOIN (
                    SELECT task_id, SUM(duration_minutes) as total_time
                    FROM work_sessions
                    GROUP BY task_id
                ) ws ON t.id = ws.task_id
                WHERE e.created_at >= ?
                GROUP BY e.id, e.difficulty, e.priority, e.points, e.status
            """
            
            epic_results = _ensure_dict_list(
                self.db_manager.execute_query(epic_query, [date_filter])
            )
            
            # Calculate points earned and achievements
            total_points = sum(row.get('points') or 0 for row in epic_results if row.get('status') == 'completed')
            
            # Difficulty distribution
            difficulty_dist = defaultdict(int)
            for row in epic_results:
                difficulty_dist[row.get('difficulty')] += 1
            
            # Priority completion rates
            priority_completion = defaultdict(lambda: {'total': 0, 'completed': 0})
            for row in epic_results:
                priority = row.get('priority')
                priority_completion[priority]['total'] += 1
                if row.get('status') == 'completed':
                    priority_completion[priority]['completed'] += 1
            
            return {
                'total_points_earned': total_points,
                'difficulty_distribution': dict(difficulty_dist),
                'priority_completion_rates': dict(priority_completion),
                'epic_metrics': epic_results
            }
            
        except Exception as e:
            self.db_manager.logger.error(f"Error getting gamification metrics: {e}")
            return {}


class AnalyticsService(BaseService):
    """Service for analytics and reporting operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.repository = AnalyticsRepository(db_manager)
        super().__init__(self.repository)
    
    def get_dashboard_summary(self, days: int = 30) -> ServiceResult[Dict[str, Any]]:
        """
        Get comprehensive dashboard summary metrics.
        
        Args:
            days: Number of days to include in metrics
            
        Returns:
            ServiceResult with dashboard summary data
        """
        self.log_operation("get_dashboard_summary", days=days)
        
        try:
            # Validate input
            if days < 1 or days > 365:
                return ServiceResult.validation_error("Days must be between 1 and 365", "days")
            
            # Get all metrics
            project_metrics = _ensure_dict_list(
                self.repository.get_project_progress_metrics()
            )
            tdd_metrics = self.repository.get_tdd_cycle_metrics(days=days)
            productivity_metrics = self.repository.get_productivity_metrics(days=days)
            gamification_metrics = self.repository.get_gamification_metrics(days=days)
            
            # Calculate derived metrics
            completion_rates = self._calculate_completion_rates({})
            productivity_trends = self._analyze_productivity_trends(productivity_metrics)
            tdd_effectiveness = self._analyze_tdd_effectiveness(tdd_metrics)
            
            summary = {
                'period_days': days,
                # usar UTC para relatórios consistentes
                'generated_at': datetime.utcnow().isoformat() + "Z",
                'overview': {
                    'total_projects': len(project_metrics),
                    'total_epics': sum(p.get('total_epics', 0) for p in project_metrics),
                    'total_tasks': sum(p.get('total_tasks', 0) for p in project_metrics),
                    'total_project_value': sum(p.get('total_estimated_hours', 0) for p in project_metrics)
                },
                'completion_rates': completion_rates,
                'productivity': productivity_trends,
                'tdd_effectiveness': tdd_effectiveness,
                'gamification': {
                    'points_earned': gamification_metrics.get('total_points_earned', 0),
                    'difficulty_distribution': gamification_metrics.get('difficulty_distribution', {}),
                    'priority_completion': gamification_metrics.get('priority_completion_rates', {})
                },
                'projects': project_metrics[:10]  # Top 10 projects
            }
            
            return ServiceResult.ok(summary)
            
        except Exception as e:
            logger.warning("Operation failed: %s", str(e))
    
    
    def get_project_analytics(self, project_id: int) -> ServiceResult[Dict[str, Any]]:
        """
        Get analytics for a specific project.
        
        Args:
            project_id: Project ID
            
        Returns:
            ServiceResult with project analytics
        """
        self.log_operation("get_project_analytics", project_id=project_id)
        
        try:
            # Get project-specific metrics
            project_metrics = _ensure_dict_list(
                self.repository.get_project_progress_metrics(project_id=project_id)
            )
            
            if not project_metrics:
                return ServiceResult.not_found("Project", project_id)
            
            project = project_metrics[0]
            
            # Calculate project-specific analytics
            analytics = {
                'project_id': project_id,
                'project_info': project,
                'progress_analysis': self._analyze_project_progress(project),
                'time_analysis': self._analyze_project_time(project),
                'risk_assessment': self._assess_project_risks(project),
                'recommendations': self._generate_project_recommendations(project)
            }
            
            return ServiceResult.ok(analytics)
            
        except Exception as e:
            logger.warning("Operation failed: %s", str(e))
    
    def get_productivity_report(self, days: int = 30) -> ServiceResult[Dict[str, Any]]:
        """
        Get comprehensive productivity report.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            ServiceResult with productivity report
        """
        self.log_operation("get_productivity_report", days=days)
        
        try:
            # Get productivity metrics
            productivity_metrics = self.repository.get_productivity_metrics(days=days)
            tdd_metrics = self.repository.get_tdd_cycle_metrics(days=days)
            
            # Analyze patterns and trends
            daily_trends = self._analyze_daily_productivity(productivity_metrics.get('daily_productivity', []))
            focus_patterns = self._analyze_focus_patterns(productivity_metrics.get('focus_patterns', []))
            accuracy_analysis = self._analyze_estimate_accuracy(productivity_metrics.get('estimate_accuracy', []))
            tdd_analysis = self._analyze_tdd_productivity(tdd_metrics)
            
            report = {
                'period_days': days,
                'generated_at': datetime.utcnow().isoformat() + "Z",
                'daily_trends': daily_trends,
                'focus_patterns': focus_patterns,
                'estimate_accuracy': accuracy_analysis,
                'tdd_effectiveness': tdd_analysis,
                'insights': self._generate_productivity_insights(daily_trends, focus_patterns, accuracy_analysis),
                'recommendations': self._generate_productivity_recommendations(daily_trends, focus_patterns)
            }
            
            return ServiceResult.ok(report)
            
        except Exception as e:
            logger.warning("Operation failed: %s", str(e))
    
    def get_tdd_metrics_report(self, days: int = 30) -> ServiceResult[Dict[str, Any]]:
        """
        Get TDD-specific metrics and analysis.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            ServiceResult with TDD metrics report
        """
        self.log_operation("get_tdd_metrics_report", days=days)
        
        try:
            # Get TDD metrics
            tdd_metrics = self.repository.get_tdd_cycle_metrics(days=days)
            
            # Analyze TDD effectiveness
            phase_analysis = self._analyze_tdd_phases(tdd_metrics.get('phase_distribution', {}))
            cycle_analysis = self._analyze_tdd_cycles(tdd_metrics)
            recommendations = self._generate_tdd_recommendations(tdd_metrics)
            
            report = {
                'period_days': days,
                'generated_at': datetime.utcnow().isoformat() + "Z",
                'phase_distribution': tdd_metrics.get('phase_distribution', {}),
                'phase_avg_times': tdd_metrics.get('phase_avg_times', {}),
                'completed_cycles': tdd_metrics.get('completed_cycles', 0),
                'avg_cycle_time': tdd_metrics.get('avg_cycle_time', 0),
                'phase_analysis': phase_analysis,
                'cycle_analysis': cycle_analysis,
                'recommendations': recommendations,
                'tdd_score': self._calculate_tdd_score(tdd_metrics)
            }
            
            return ServiceResult.ok(report)
            
        except Exception as e:
            logger.warning("Operation failed: %s", str(e))
    
    def get_time_tracking_report(self, days: int = 30) -> ServiceResult[Dict[str, Any]]:
        """
        Get time tracking analysis report.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            ServiceResult with time tracking report
        """
        self.log_operation("get_time_tracking_report", days=days)
        
        try:
            # Get productivity metrics
            productivity_metrics = self.repository.get_productivity_metrics(days=days)
            
            # Analyze time patterns
            daily_analysis = self._analyze_daily_time_patterns(productivity_metrics.get('daily_productivity', []))
            hourly_analysis = self._analyze_hourly_patterns(productivity_metrics.get('focus_patterns', []))
            accuracy_analysis = self._analyze_estimate_accuracy(productivity_metrics.get('estimate_accuracy', []))
            
            report = {
                'period_days': days,
                # usar UTC para relatórios consistentes
                'generated_at': datetime.utcnow().isoformat() + "Z",
                'daily_patterns': daily_analysis,
                'hourly_patterns': hourly_analysis,
                'estimate_accuracy': accuracy_analysis,
                'optimal_times': self._identify_optimal_work_times(hourly_analysis),
                'efficiency_insights': self._generate_efficiency_insights(daily_analysis, accuracy_analysis),
                'recommendations': self._generate_time_management_recommendations(daily_analysis, hourly_analysis)
            }
            
            return ServiceResult.ok(report)
            
        except Exception as e:
            logger.warning("Operation failed: %s", str(e))
    
    # Private helper methods for analytics calculations
    
    def _calculate_completion_rates(self, metrics: Dict[str, Any]) -> Dict[str, float]:
        """Calculate completion rates for different entity types."""
        return {
            'projects': self._safe_percentage(metrics.get('completed_projects', 0), metrics.get('total_projects', 0)),
            'epics': self._safe_percentage(metrics.get('completed_epics', 0), metrics.get('total_epics', 0)),
            'tasks': self._safe_percentage(metrics.get('completed_tasks', 0), metrics.get('total_tasks', 0))
        }
    
    def _analyze_productivity_trends(self, productivity_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze productivity trends from metrics."""
        daily_data = productivity_metrics.get('daily_productivity', [])
        
        if not daily_data:
            return {'trend': 'insufficient_data', 'avg_daily_hours': 0, 'peak_productivity_day': None}
        
        # Calculate averages
        avg_daily_minutes = statistics.mean([row['total_minutes'] for row in daily_data])
        avg_daily_hours = avg_daily_minutes / 60
        
        # Find peak productivity day
        peak_day = max(daily_data, key=lambda x: x['total_minutes'])
        
        return {
            'trend': self._determine_trend(daily_data),
            'avg_daily_hours': round(avg_daily_hours, 2),
            'peak_productivity_day': peak_day['work_date'],
            'peak_productivity_hours': round(peak_day['total_minutes'] / 60, 2)
        }
    
    def _analyze_tdd_effectiveness(self, tdd_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze TDD cycle effectiveness."""
        phase_dist = tdd_metrics.get('phase_distribution', {})
        completed_cycles = tdd_metrics.get('completed_cycles', 0)
        
        total_tasks = sum(phase_dist.values())
        
        if total_tasks == 0:
            return {'effectiveness_score': 0, 'balance_score': 0, 'completion_rate': 0}
        
        # Calculate balance score (how evenly distributed across phases)
        ideal_distribution = total_tasks / 3  # Ideal: equal distribution
        balance_score = 100 - sum(abs(count - ideal_distribution) for count in phase_dist.values()) / total_tasks * 100
        
        # Calculate completion rate
        completion_rate = (completed_cycles / total_tasks * 100) if total_tasks > 0 else 0
        
        # Overall effectiveness score
        effectiveness_score = (balance_score * 0.4 + completion_rate * 0.6)
        
        return {
            'effectiveness_score': round(effectiveness_score, 2),
            'balance_score': round(balance_score, 2),
            'completion_rate': round(completion_rate, 2),
            'total_cycles': completed_cycles
        }
    
    def _safe_percentage(self, numerator: int, denominator: int) -> float:
        """Safely calculate percentage avoiding division by zero."""
        return round((numerator / denominator * 100) if denominator > 0 else 0, 2)
    
    def _determine_trend(self, daily_data: List[Dict[str, Any]]) -> str:
        """Determine productivity trend from daily data."""
        if len(daily_data) < 3:
            return 'insufficient_data'
        
        # Simple trend analysis based on last few days
        recent_avg = statistics.mean([row['total_minutes'] for row in daily_data[:3]])
        older_avg = statistics.mean([row['total_minutes'] for row in daily_data[3:6]]) if len(daily_data) > 5 else recent_avg
        
        if recent_avg > older_avg * 1.1:
            return 'improving'
        elif recent_avg < older_avg * 0.9:
            return 'declining'
        else:
            return 'stable'
    
    
    
    def _analyze_project_progress(self, project: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze individual project progress."""
        total_tasks = project.get('total_tasks', 0)
        completed_tasks = project.get('completed_tasks', 0)
        
        progress_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        return {
            'progress_percentage': round(progress_percentage, 2),
            'tasks_remaining': total_tasks - completed_tasks,
            'status': self._determine_project_status(progress_percentage, project.get('project_status'))
        }
    
    def _analyze_project_time(self, project: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze project time metrics."""
        actual_hours = project.get('total_time_minutes', 0) / 60
        estimated_hours = project.get('total_estimated_hours', 0)
        
        if estimated_hours > 0:
            variance = actual_hours - estimated_hours
            variance_percentage = (variance / estimated_hours) * 100
        else:
            variance = None
            variance_percentage = None
        
        return {
            'actual_hours': round(actual_hours, 2),
            'estimated_hours': estimated_hours,
            'variance_hours': round(variance, 2) if variance is not None else None,
            'variance_percentage': round(variance_percentage, 2) if variance_percentage is not None else None
        }
    
    def _assess_project_risks(self, project: Dict[str, Any]) -> Dict[str, str]:
        """Assess project risks based on metrics."""
        risks = []
        
        progress = project.get('completion_percentage', 0)
        if progress < 25:
            risks.append("Low progress - may need additional resources")
        
        return {'identified_risks': risks}
    
    def _generate_project_recommendations(self, project: Dict[str, Any]) -> List[str]:
        """Generate project-specific recommendations."""
        recommendations = []
        
        progress = project.get('completion_percentage', 0)
        if progress < 50:
            recommendations.append("Consider breaking down remaining work into smaller tasks")
        
        return recommendations
    
    def _analyze_daily_productivity(self, daily_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze daily productivity patterns."""
        if not daily_data:
            return {}
        
        total_minutes = [row['total_minutes'] for row in daily_data]
        
        return {
            'avg_daily_minutes': round(statistics.mean(total_minutes), 2),
            'max_daily_minutes': max(total_minutes),
            'min_daily_minutes': min(total_minutes),
            'consistency_score': self._calculate_consistency_score(total_minutes)
        }
    
    def _analyze_focus_patterns(self, focus_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze focus patterns by hour."""
        if not focus_data:
            return {}
        
        peak_hour = max(focus_data, key=lambda x: x['total_minutes'])
        
        return {
            'peak_hour': peak_hour['hour_of_day'],
            'peak_minutes': peak_hour['total_minutes'],
            'most_productive_time': self._categorize_time(peak_hour['hour_of_day'])
        }
    
    def _analyze_estimate_accuracy(self, accuracy_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze estimation accuracy."""
        if not accuracy_data:
            return {'accuracy_score': 0, 'avg_variance': 0}
        
        variances = [row['variance_hours'] for row in accuracy_data]
        avg_variance = statistics.mean(variances)
        
        # Calculate accuracy score (lower variance = higher accuracy)
        accuracy_score = max(0, 100 - (avg_variance / statistics.mean([row['estimated_hours'] for row in accuracy_data]) * 100))
        
        return {
            'accuracy_score': round(accuracy_score, 2),
            'avg_variance_hours': round(avg_variance, 2),
            'total_estimates': len(accuracy_data)
        }
    
    def _analyze_tdd_productivity(self, tdd_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze TDD impact on productivity."""
        completed_cycles = tdd_metrics.get('completed_cycles', 0)
        avg_cycle_time = tdd_metrics.get('avg_cycle_time', 0)
        
        return {
            'cycles_per_day': round(completed_cycles / 30, 2),  # Assuming 30-day period
            'avg_cycle_time_hours': round(avg_cycle_time / 60, 2),
            'productivity_rating': self._rate_tdd_productivity(completed_cycles, avg_cycle_time)
        }
    
    def _calculate_consistency_score(self, values: List[float]) -> float:
        """Calculate consistency score based on standard deviation."""
        if len(values) < 2:
            return 100.0
        
        std_dev = statistics.stdev(values)
        mean_val = statistics.mean(values)
        
        # Lower coefficient of variation = higher consistency
        cv = (std_dev / mean_val) if mean_val > 0 else 0
        consistency = max(0, 100 - (cv * 100))
        
        return round(consistency, 2)
    
    def _categorize_time(self, hour: int) -> str:
        """Categorize hour into time period."""
        if 6 <= hour < 12:
            return "Morning"
        elif 12 <= hour < 18:
            return "Afternoon"
        elif 18 <= hour < 22:
            return "Evening"
        else:
            return "Night"
    
    def _rate_tdd_productivity(self, cycles: int, avg_time: float) -> str:
        """Rate TDD productivity based on cycles and time."""
        if cycles == 0:
            return "No data"
        elif cycles >= 30 and avg_time <= 120:  # 30 cycles in 30 days, avg 2 hours
            return "Excellent"
        elif cycles >= 15 and avg_time <= 180:  # 15 cycles, avg 3 hours
            return "Good"
        elif cycles >= 5:
            return "Fair"
        else:
            return "Needs improvement"
    
    def _determine_project_status(self, progress: float, status: str) -> str:
        """Determine project status based on progress and current status."""
        if status == 'completed':
            return 'completed'
        elif progress >= 75:
            return 'near_completion'
        elif progress >= 25:
            return 'in_progress'
        else:
            return 'getting_started'
    
    def _generate_productivity_insights(self, daily_trends: Dict, focus_patterns: Dict, accuracy: Dict) -> List[str]:
        """Generate productivity insights."""
        insights = []
        
        if daily_trends.get('consistency_score', 0) > 80:
            insights.append("You maintain consistent daily productivity")
        
        if focus_patterns.get('most_productive_time'):
            insights.append(f"Your peak productivity is during {focus_patterns['most_productive_time']}")
        
        if accuracy.get('accuracy_score', 0) > 80:
            insights.append("Your time estimates are highly accurate")
        
        return insights
    
    def _generate_productivity_recommendations(self, daily_trends: Dict, focus_patterns: Dict) -> List[str]:
        """Generate productivity recommendations."""
        recommendations = []
        
        if daily_trends.get('consistency_score', 0) < 60:
            recommendations.append("Try to establish more consistent daily work patterns")
        
        peak_time = focus_patterns.get('most_productive_time')
        if peak_time:
            recommendations.append(f"Schedule your most important work during {peak_time}")
        
        return recommendations
    
    def _analyze_tdd_phases(self, phase_distribution: Dict[str, int]) -> Dict[str, Any]:
        """Analyze TDD phase distribution."""
        total = sum(phase_distribution.values())
        
        if total == 0:
            return {'balance': 'no_data', 'bottleneck': None}
        
        percentages = {phase: (count / total * 100) for phase, count in phase_distribution.items()}
        
        # Identify bottleneck (phase with highest percentage)
        bottleneck = max(percentages, key=percentages.get) if percentages else None
        
        return {
            'balance': 'good' if all(20 <= p <= 40 for p in percentages.values()) else 'imbalanced',
            'bottleneck': bottleneck,
            'percentages': {k: round(v, 2) for k, v in percentages.items()}
        }
    
    def _analyze_tdd_cycles(self, tdd_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze TDD cycle completion."""
        completed = tdd_metrics.get('completed_cycles', 0)
        avg_time = tdd_metrics.get('avg_cycle_time', 0)
        
        return {
            'completion_rate': 'high' if completed >= 20 else 'medium' if completed >= 10 else 'low',
            'cycle_efficiency': 'efficient' if avg_time <= 120 else 'moderate' if avg_time <= 240 else 'slow',
            'recommendations': self._get_cycle_recommendations(completed, avg_time)
        }
    
    def _generate_tdd_recommendations(self, tdd_metrics: Dict[str, Any]) -> List[str]:
        """Generate TDD-specific recommendations."""
        recommendations = []
        
        phase_dist = tdd_metrics.get('phase_distribution', {})
        total = sum(phase_dist.values())
        
        if total == 0:
            recommendations.append("Start using TDD methodology with Red-Green-Refactor cycles")
            return recommendations
        
        # Check for phase imbalances
        red_pct = phase_dist.get('red', 0) / total * 100
        green_pct = phase_dist.get('green', 0) / total * 100
        refactor_pct = phase_dist.get('refactor', 0) / total * 100
        
        if red_pct > 50:
            recommendations.append("Too many tasks stuck in RED phase - focus on making tests pass")
        
        if refactor_pct < 20:
            recommendations.append("Increase refactoring activities to improve code quality")
        
        return recommendations
    
    def _calculate_tdd_score(self, tdd_metrics: Dict[str, Any]) -> float:
        """Calculate overall TDD effectiveness score."""
        phase_dist = tdd_metrics.get('phase_distribution', {})
        completed_cycles = tdd_metrics.get('completed_cycles', 0)
        
        total_tasks = sum(phase_dist.values())
        
        if total_tasks == 0:
            return 0.0
        
        # Balance score (even distribution is better)
        balance_score = 100 - abs(33.33 - (phase_dist.get('red', 0) / total_tasks * 100))
        balance_score -= abs(33.33 - (phase_dist.get('green', 0) / total_tasks * 100))
        balance_score -= abs(33.33 - (phase_dist.get('refactor', 0) / total_tasks * 100))
        balance_score = max(0, balance_score)
        
        # Completion score
        completion_score = min(100, (completed_cycles / total_tasks * 100))
        
        # Combined score
        tdd_score = (balance_score * 0.4 + completion_score * 0.6)
        
        return round(tdd_score, 2)
    
    def _get_cycle_recommendations(self, completed: int, avg_time: float) -> List[str]:
        """Get recommendations for TDD cycle improvement."""
        recommendations = []
        
        if completed < 10:
            recommendations.append("Increase TDD cycle completion rate")
        
        if avg_time > 240:  # 4 hours
            recommendations.append("Break down tasks into smaller, more manageable cycles")
        
        return recommendations
    
    def _analyze_daily_time_patterns(self, daily_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze daily time tracking patterns."""
        if not daily_data:
            return {}
        
        return {
            'total_days': len(daily_data),
            'avg_daily_hours': round(statistics.mean([row['total_minutes'] / 60 for row in daily_data]), 2),
            'most_productive_day': max(daily_data, key=lambda x: x['total_minutes'])
        }
    
    def _analyze_hourly_patterns(self, hourly_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze hourly focus patterns."""
        if not hourly_data:
            return {}
        
        peak_hour = max(hourly_data, key=lambda x: x['total_minutes'])
        
        return {
            'peak_hour': peak_hour['hour_of_day'],
            'peak_productivity_time': self._categorize_time(peak_hour['hour_of_day']),
            'total_focus_hours': round(sum(row['total_minutes'] for row in hourly_data) / 60, 2)
        }
    
    def _identify_optimal_work_times(self, hourly_analysis: Dict[str, Any]) -> List[str]:
        """Identify optimal work times based on patterns."""
        peak_time = hourly_analysis.get('peak_productivity_time')
        optimal_times = []
        
        if peak_time:
            optimal_times.append(f"Peak productivity during {peak_time}")
        
        return optimal_times
    
    def _generate_efficiency_insights(self, daily_analysis: Dict, accuracy_analysis: Dict) -> List[str]:
        """Generate efficiency insights."""
        insights = []
        
        avg_hours = daily_analysis.get('avg_daily_hours', 0)
        if avg_hours > 6:
            insights.append("High daily time investment")
        elif avg_hours < 2:
            insights.append("Low daily time investment - consider increasing focus time")
        
        accuracy = accuracy_analysis.get('accuracy_score', 0)
        if accuracy > 80:
            insights.append("Excellent time estimation accuracy")
        
        return insights
    
    def _generate_time_management_recommendations(self, daily_analysis: Dict, hourly_analysis: Dict) -> List[str]:
        """Generate time management recommendations."""
        recommendations = []
        
        peak_time = hourly_analysis.get('peak_productivity_time')
        if peak_time:
            recommendations.append(f"Schedule important tasks during your {peak_time} peak")
        
        avg_hours = daily_analysis.get('avg_daily_hours', 0)
        if avg_hours < 4:
            recommendations.append("Consider increasing daily focused work time")
        
        return recommendations