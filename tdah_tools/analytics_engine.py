#!/usr/bin/env python3
"""
📊 TDD Analytics Engine - TDAH Time Tracking Analytics

Advanced analytics for TDAH-optimized TDD workflow including:
- Time estimation accuracy analysis
- Focus pattern identification
- Productivity insights
- Pomodoro-style break recommendations
- Epic completion predictions
"""

import sqlite3
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

# Import standardized error handling
from .error_handler import (
    get_error_handler, handle_error, log_info, log_warning, log_error,
    AnalyticsError, FileSystemError, DependencyError, ErrorSeverity
)
# Import performance utilities
from .performance_utils import (
    get_performance_monitor, cached, performance_critical,
    LRUCache, DataStreamProcessor
)

# Optional dependencies with graceful degradation
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    pd = None
    PANDAS_AVAILABLE = False

try:
    import plotly.graph_objects as go
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    go = None
    px = None
    PLOTLY_AVAILABLE = False

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    np = None
    NUMPY_AVAILABLE = False


@dataclass 
class ProductivityMetrics:
    """Productivity metrics for TDAH analysis."""
    focus_score: float
    accuracy_score: float
    consistency_score: float
    break_adherence: float
    optimal_work_duration: int  # minutes
    recommended_break_frequency: int  # minutes
    

class TDDAHAnalytics:
    """Analytics engine for TDAH-optimized TDD workflow with performance optimizations."""
    
    def __init__(self, db_path: str = "task_timer.db", enable_caching: bool = True):
        self.db_path = Path(db_path)
        self.data_cache = {}
        self.enable_caching = enable_caching
        self.performance_monitor = get_performance_monitor()
        
        # Advanced caching for large datasets
        if enable_caching:
            self.lru_cache = LRUCache(max_size=1000, ttl_seconds=1800)
        else:
            self.lru_cache = None
        
    @performance_critical("load_session_data")
    @cached(ttl_seconds=1800, use_persistent=True)
    def load_session_data(self, days: int = 30) -> Any:
        """Load task session data with performance optimizations."""
        if not self._check_analytics_dependencies():
            return self._load_session_data_basic(days)
        
        # Check advanced cache first
        if self.lru_cache:
            cache_key = f"sessions_df_{days}"
            cached_result = self.lru_cache.get(cache_key)
            if cached_result is not None:
                log_info("Cache hit for session data", {"days": days, "size": len(cached_result)})
                return cached_result
            
        if f"sessions_{days}" in self.data_cache:
            return self.data_cache[f"sessions_{days}"]
            
        cutoff = datetime.now() - timedelta(days=days)
        
        with sqlite3.connect(self.db_path) as conn:
            # Optimized query with proper indexing hints
            query = """
                SELECT 
                    task_id, epic_id, start_time, end_time,
                    estimate_minutes, actual_seconds, status,
                    paused_duration, created_at,
                    datetime(start_time, 'unixepoch') as start_datetime,
                    datetime(end_time, 'unixepoch') as end_datetime,
                    strftime('%H', datetime(start_time, 'unixepoch')) as start_hour,
                    strftime('%w', datetime(start_time, 'unixepoch')) as weekday
                FROM task_sessions 
                WHERE created_at >= ?
                ORDER BY start_time
            """
            
            df = pd.read_sql_query(query, conn, params=(cutoff,))
            
        # Add calculated columns using vectorized operations for better performance
        if not df.empty:
            df['actual_minutes'] = df['actual_seconds'] / 60.0
            # Avoid division by zero with numpy where
            df['accuracy_ratio'] = np.where(
                df['estimate_minutes'] > 0,
                df['actual_minutes'] / df['estimate_minutes'],
                1.0
            )
            df['overrun_minutes'] = df['actual_minutes'] - df['estimate_minutes']
            df['is_accurate'] = (df['accuracy_ratio'] <= 1.1) & (df['accuracy_ratio'] >= 0.9)
            df['focus_quality'] = self._calculate_focus_quality(df)
        
        # Cache results
        self.data_cache[f"sessions_{days}"] = df
        if self.lru_cache:
            self.lru_cache.set(cache_key, df)
            
        log_info(f"Loaded session data", {"rows": len(df), "days": days})
        return df
    
    def _check_analytics_dependencies(self) -> bool:
        """Check if all analytics dependencies are available."""
        return PANDAS_AVAILABLE and PLOTLY_AVAILABLE and NUMPY_AVAILABLE
    
    def _load_session_data_basic(self, days: int = 30) -> List[Dict]:
        """Load session data as basic Python data structures when pandas unavailable."""
        log_warning(
            "Advanced analytics unavailable",
            {"missing_deps": ["pandas", "plotly", "numpy"], "fallback": "basic_mode"}
        )
        print("⚠️ Advanced analytics unavailable. Install pandas, plotly, and numpy for full functionality.")
        
        if f"sessions_basic_{days}" in self.data_cache:
            return self.data_cache[f"sessions_basic_{days}"]
            
        cutoff = datetime.now() - timedelta(days=days)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = """
                SELECT 
                    task_id, epic_id, start_time, end_time,
                    estimate_minutes, actual_seconds, status,
                    paused_duration, created_at
                FROM task_sessions 
                WHERE created_at >= ?
                ORDER BY start_time
            """
            
            cursor.execute(query, (cutoff,))
            rows = cursor.fetchall()
            
            # Convert to list of dictionaries with basic calculations
            sessions = []
            for row in rows:
                session = dict(row)
                session['actual_minutes'] = session['actual_seconds'] / 60.0
                session['accuracy_ratio'] = session['actual_minutes'] / session['estimate_minutes'] if session['estimate_minutes'] > 0 else 1.0
                session['overrun_minutes'] = session['actual_minutes'] - session['estimate_minutes']
                session['is_accurate'] = 0.9 <= session['accuracy_ratio'] <= 1.1
                
                # Basic focus quality calculation
                pause_ratio = (session['paused_duration'] or 0) / session['actual_seconds'] if session['actual_seconds'] > 0 else 0
                accuracy_penalty = abs(session['accuracy_ratio'] - 1.0)
                session['focus_quality'] = max(0, 1.0 - pause_ratio * 0.4 - accuracy_penalty * 0.6)
                
                sessions.append(session)
            
        self.data_cache[f"sessions_basic_{days}"] = sessions
        return sessions
    
    def _calculate_focus_quality(self, df):
        """Calculate focus quality score based on pauses and overruns."""
        if not PANDAS_AVAILABLE:
            # This method should only be called when pandas is available
            return [0.5] * len(df)  # Fallback values
            
        # Lower pause time = better focus
        pause_score = 1.0 - (df['paused_duration'] / df['actual_seconds']).fillna(0)
        
        # Accuracy close to 1.0 = better focus 
        accuracy_score = 1.0 - abs(df['accuracy_ratio'] - 1.0).fillna(1.0)
        
        # Combined focus quality (0-1 scale)
        return (pause_score * 0.4 + accuracy_score * 0.6).clip(0, 1)
    
    @performance_critical("generate_productivity_metrics")
    @cached(ttl_seconds=900)  # 15 minute cache for metrics
    def generate_productivity_metrics(self, days: int = 30) -> ProductivityMetrics:
        """Generate comprehensive productivity metrics with performance optimization."""
        data = self.load_session_data(days)
        
        if not self._check_analytics_dependencies():
            return self._generate_productivity_metrics_basic(data)
        
        if data.empty:
            return ProductivityMetrics(0, 0, 0, 0, 25, 5)  # Default values
        
        # Use efficient pandas operations
        completed_mask = data['status'] == 'completed'
        completed_df = data[completed_mask]
        
        if completed_df.empty:
            return ProductivityMetrics(0, 0, 0, 0, 25, 5)
        
        # Vectorized calculations for better performance
        focus_values = completed_df['focus_quality'].values
        accuracy_values = completed_df['accuracy_ratio'].values
        is_accurate_values = completed_df['is_accurate'].values
        
        # Focus score (using numpy for speed)
        focus_score = np.mean(focus_values) if len(focus_values) > 0 else 0.0
        
        # Accuracy score (percentage of tasks within 10% of estimate)
        accuracy_score = np.mean(is_accurate_values) if len(is_accurate_values) > 0 else 0.0
        
        # Consistency score (inverse of standard deviation of accuracy)
        accuracy_std = np.std(accuracy_values) if len(accuracy_values) > 1 else 0.0
        consistency_score = 1.0 / (1.0 + accuracy_std) if accuracy_std > 0 else 1.0
        
        # Break adherence (placeholder - would require break tracking)
        break_adherence = 0.8  # Default assumption
        
        # Optimal work duration analysis using efficient filtering
        high_focus_mask = completed_df['focus_quality'] > 0.7
        if high_focus_mask.any():
            optimal_duration = int(np.median(completed_df.loc[high_focus_mask, 'actual_minutes'].values))
        else:
            optimal_duration = 25
        
        # Recommended break frequency (every 25-45 mins for TDAH)
        recommended_break = min(max(optimal_duration, 15), 45)
        
        return ProductivityMetrics(
            focus_score=float(focus_score),
            accuracy_score=float(accuracy_score), 
            consistency_score=float(consistency_score),
            break_adherence=break_adherence,
            optimal_work_duration=optimal_duration,
            recommended_break_frequency=recommended_break
        )
    
    def _generate_productivity_metrics_basic(self, sessions: List[Dict]) -> ProductivityMetrics:
        """Generate basic productivity metrics without pandas."""
        if not sessions:
            return ProductivityMetrics(0, 0, 0, 0, 25, 5)
        
        completed_sessions = [s for s in sessions if s['status'] == 'completed']
        
        if not completed_sessions:
            return ProductivityMetrics(0, 0, 0, 0, 25, 5)
        
        # Calculate basic metrics
        focus_scores = [s['focus_quality'] for s in completed_sessions]
        accuracy_ratios = [s['accuracy_ratio'] for s in completed_sessions]
        accurate_count = sum(1 for s in completed_sessions if s['is_accurate'])
        
        focus_score = sum(focus_scores) / len(focus_scores) if focus_scores else 0
        accuracy_score = accurate_count / len(completed_sessions) if completed_sessions else 0
        
        # Basic standard deviation calculation
        mean_accuracy = sum(accuracy_ratios) / len(accuracy_ratios) if accuracy_ratios else 1.0
        variance = sum((ratio - mean_accuracy) ** 2 for ratio in accuracy_ratios) / len(accuracy_ratios) if accuracy_ratios else 0
        accuracy_std = variance ** 0.5
        consistency_score = 1.0 / (1.0 + accuracy_std) if accuracy_std > 0 else 1.0
        
        # Optimal duration from high focus sessions
        high_focus_sessions = [s for s in completed_sessions if s['focus_quality'] > 0.7]
        if high_focus_sessions:
            durations = sorted([s['actual_minutes'] for s in high_focus_sessions])
            optimal_duration = int(durations[len(durations) // 2])  # Median
        else:
            optimal_duration = 25
        
        recommended_break = min(max(optimal_duration, 15), 45)
        
        return ProductivityMetrics(
            focus_score=focus_score,
            accuracy_score=accuracy_score,
            consistency_score=consistency_score,
            break_adherence=0.8,  # Default
            optimal_work_duration=optimal_duration,
            recommended_break_frequency=recommended_break
        )
    
    def analyze_time_patterns(self, days: int = 30) -> Dict:
        """Analyze optimal time patterns for TDAH productivity."""
        data = self.load_session_data(days)
        
        if not self._check_analytics_dependencies():
            return self._analyze_time_patterns_basic(data)
        
        completed_df = data[data['status'] == 'completed']
        
        if completed_df.empty:
            return {"error": "No completed sessions found"}
        
        # Hour of day analysis
        hourly_focus = completed_df.groupby('start_hour').agg({
            'focus_quality': 'mean',
            'accuracy_ratio': 'mean',
            'task_id': 'count'
        }).round(3)
        
        # Day of week analysis  
        daily_focus = completed_df.groupby('weekday').agg({
            'focus_quality': 'mean',
            'accuracy_ratio': 'mean', 
            'task_id': 'count'
        }).round(3)
        
        # Find optimal time windows
        best_hours = hourly_focus.nlargest(3, 'focus_quality').index.tolist()
        best_days = daily_focus.nlargest(3, 'focus_quality').index.tolist()
        
        return {
            "optimal_hours": [int(h) for h in best_hours],
            "optimal_weekdays": [int(d) for d in best_days],
            "hourly_stats": hourly_focus.to_dict(),
            "daily_stats": daily_focus.to_dict(),
            "recommendations": self._generate_time_recommendations(best_hours, best_days)
        }
    
    def _analyze_time_patterns_basic(self, sessions: List[Dict]) -> Dict:
        """Analyze time patterns using basic Python when pandas unavailable."""
        completed_sessions = [s for s in sessions if s['status'] == 'completed']
        
        if not completed_sessions:
            return {"error": "No completed sessions found"}
        
        # Group by hour and calculate basic stats
        hourly_stats = {}
        daily_stats = {}
        
        # Group sessions by start hour (extract from timestamp)
        for session in completed_sessions:
            start_time = datetime.fromtimestamp(session['start_time'])
            hour = start_time.hour
            weekday = start_time.weekday()
            
            # Hourly grouping
            if hour not in hourly_stats:
                hourly_stats[hour] = {'focus_scores': [], 'accuracy_ratios': [], 'count': 0}
            hourly_stats[hour]['focus_scores'].append(session['focus_quality'])
            hourly_stats[hour]['accuracy_ratios'].append(session['accuracy_ratio'])
            hourly_stats[hour]['count'] += 1
            
            # Daily grouping
            if weekday not in daily_stats:
                daily_stats[weekday] = {'focus_scores': [], 'accuracy_ratios': [], 'count': 0}
            daily_stats[weekday]['focus_scores'].append(session['focus_quality'])
            daily_stats[weekday]['accuracy_ratios'].append(session['accuracy_ratio'])
            daily_stats[weekday]['count'] += 1
        
        # Calculate averages and find best times
        hourly_averages = {}
        for hour, data in hourly_stats.items():
            hourly_averages[hour] = {
                'focus_quality': sum(data['focus_scores']) / len(data['focus_scores']),
                'accuracy_ratio': sum(data['accuracy_ratios']) / len(data['accuracy_ratios']),
                'task_id': data['count']
            }
        
        daily_averages = {}
        for day, data in daily_stats.items():
            daily_averages[day] = {
                'focus_quality': sum(data['focus_scores']) / len(data['focus_scores']),
                'accuracy_ratio': sum(data['accuracy_ratios']) / len(data['accuracy_ratios']),
                'task_id': data['count']
            }
        
        # Find top 3 hours and days by focus quality
        best_hours = sorted(hourly_averages.keys(), 
                           key=lambda h: hourly_averages[h]['focus_quality'], reverse=True)[:3]
        best_days = sorted(daily_averages.keys(), 
                          key=lambda d: daily_averages[d]['focus_quality'], reverse=True)[:3]
        
        return {
            "optimal_hours": best_hours,
            "optimal_weekdays": best_days,
            "hourly_stats": hourly_averages,
            "daily_stats": daily_averages,
            "recommendations": self._generate_time_recommendations(best_hours, best_days)
        }
    
    def _generate_time_recommendations(self, best_hours: List, best_days: List) -> Dict:
        """Generate specific time-based recommendations for TDAH."""
        hour_names = {
            9: "Morning (9 AM)", 10: "Mid-Morning (10 AM)", 11: "Late Morning (11 AM)",
            14: "Early Afternoon (2 PM)", 15: "Mid-Afternoon (3 PM)", 16: "Late Afternoon (4 PM)",
            19: "Early Evening (7 PM)", 20: "Evening (8 PM)", 21: "Late Evening (9 PM)"
        }
        
        day_names = {
            1: "Monday", 2: "Tuesday", 3: "Wednesday", 4: "Thursday", 
            5: "Friday", 6: "Saturday", 0: "Sunday"
        }
        
        recommendations = {
            "peak_hours": [hour_names.get(int(h), f"{h}:00") for h in best_hours],
            "peak_days": [day_names.get(int(d), f"Day {d}") for d in best_days],
            "schedule_suggestion": self._create_optimal_schedule(best_hours),
            "break_strategy": self._recommend_break_strategy()
        }
        
        return recommendations
    
    def _create_optimal_schedule(self, best_hours: List) -> List[str]:
        """Create optimal daily schedule recommendations."""
        schedule = []
        
        if any(h in [9, 10, 11] for h in best_hours):
            schedule.append("🌅 Morning deep work: 9-11 AM (complex TDD tasks)")
        
        if any(h in [14, 15, 16] for h in best_hours):
            schedule.append("☀️ Afternoon focus: 2-4 PM (implementation & refactoring)")
            
        if any(h in [19, 20, 21] for h in best_hours):
            schedule.append("🌙 Evening review: 7-9 PM (documentation & planning)")
        
        return schedule or ["📋 Track more sessions to generate personalized schedule"]
    
    def _recommend_break_strategy(self) -> List[str]:
        """Recommend TDAH-optimized break strategies."""
        return [
            "🍅 Pomodoro: 25 min work + 5 min break",
            "🚶‍♂️ Physical movement during breaks", 
            "💧 Hydration reminder every hour",
            "🧘‍♂️ Mindfulness: 2-minute breathing exercises",
            "🌿 Nature break: Look outside/go outdoors",
            "📱 Avoid social media during breaks"
        ]
    
    def predict_epic_completion(self, epic_id: str) -> Dict:
        """Predict epic completion based on historical data."""
        data = self.load_session_data(90)  # Use 3 months of data
        
        if not self._check_analytics_dependencies():
            return self._predict_epic_completion_basic(data, epic_id)
        
        epic_df = data[data['epic_id'] == epic_id]
        
        if epic_df.empty:
            return {"error": f"No data found for epic {epic_id}"}
        
        # Calculate progress metrics
        completed_tasks = epic_df[epic_df['status'] == 'completed']
        total_tasks = len(epic_df)
        completed_count = len(completed_tasks)
        
        # Estimate remaining time based on historical accuracy
        avg_accuracy = completed_tasks['accuracy_ratio'].mean() if not completed_tasks.empty else 1.2
        
        # Load epic definition to get remaining tasks
        remaining_estimate = self._get_remaining_epic_estimate(epic_id)
        adjusted_estimate = remaining_estimate * avg_accuracy
        
        # Calculate completion percentage
        completion_pct = (completed_count / total_tasks * 100) if total_tasks > 0 else 0
        
        return {
            "epic_id": epic_id,
            "completion_percentage": round(completion_pct, 1),
            "completed_tasks": completed_count,
            "total_tasks": total_tasks,
            "estimated_remaining_hours": round(adjusted_estimate / 60, 1),
            "accuracy_factor": round(avg_accuracy, 2),
            "predicted_completion": self._predict_completion_date(adjusted_estimate)
        }
    
    def _predict_epic_completion_basic(self, sessions: List[Dict], epic_id: str) -> Dict:
        """Predict epic completion using basic Python when pandas unavailable."""
        epic_sessions = [s for s in sessions if s['epic_id'] == epic_id]
        
        if not epic_sessions:
            return {"error": f"No data found for epic {epic_id}"}
        
        # Calculate basic metrics
        completed_tasks = [s for s in epic_sessions if s['status'] == 'completed']
        total_tasks = len(epic_sessions)
        completed_count = len(completed_tasks)
        
        # Average accuracy
        if completed_tasks:
            avg_accuracy = sum(s['accuracy_ratio'] for s in completed_tasks) / len(completed_tasks)
        else:
            avg_accuracy = 1.2  # Default assumption
        
        # Load epic definition to get remaining tasks
        remaining_estimate = self._get_remaining_epic_estimate(epic_id)
        adjusted_estimate = remaining_estimate * avg_accuracy
        
        # Calculate completion percentage
        completion_pct = (completed_count / total_tasks * 100) if total_tasks > 0 else 0
        
        return {
            "epic_id": epic_id,
            "completion_percentage": round(completion_pct, 1),
            "completed_tasks": completed_count,
            "total_tasks": total_tasks,
            "estimated_remaining_hours": round(adjusted_estimate / 60, 1),
            "accuracy_factor": round(avg_accuracy, 2),
            "predicted_completion": self._predict_completion_date(adjusted_estimate)
        }
    
    def _get_remaining_epic_estimate(self, epic_id: str) -> int:
        """Get remaining time estimate for epic from JSON files."""
        for epic_file in Path(".").glob("epic*.json"):
            try:
                with open(epic_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                epic_data = data.get('epic', {})
                if str(epic_data.get('id', '')) == epic_id:
                    total_estimate = 0
                    for task in epic_data.get('tasks', []):
                        total_estimate += task.get('estimate_minutes', 10)
                    return total_estimate
                    
            except Exception as e:
                handle_error(
                    exception=e,
                    severity=ErrorSeverity.DEBUG,
                    context={"epic_file": str(epic_file)},
                    user_action="Check epic file format"
                )
                continue
        
        return 60  # Default estimate
    
    def _predict_completion_date(self, remaining_minutes: int) -> str:
        """Predict completion date based on historical productivity."""
        # Assume 2 hours of focused work per day on average (TDAH-realistic)
        daily_minutes = 120
        days_remaining = max(1, int(remaining_minutes / daily_minutes))
        
        completion_date = datetime.now() + timedelta(days=days_remaining)
        return completion_date.strftime("%Y-%m-%d")
    
    @performance_critical("create_focus_dashboard")
    def create_focus_dashboard(self, output_path: str = "focus_dashboard.html") -> str:
        """Create interactive focus analytics dashboard with performance optimization."""
        if not PLOTLY_AVAILABLE:
            return self._create_dashboard_fallback(output_path)
        
        # Check cache for dashboard data
        cache_key = f"dashboard_data_{hash(output_path)}"
        if self.lru_cache:
            cached_data = self.lru_cache.get(cache_key)
            if cached_data:
                log_info("Using cached dashboard data")
                return self._render_dashboard_from_cache(cached_data, output_path)
        
        data = self.load_session_data(30)
        
        if not self._check_analytics_dependencies():
            return self._create_dashboard_fallback(output_path)
        
        if data.empty:
            return "No data available for dashboard"
        
        completed_df = data[data['status'] == 'completed'] 
        
        if completed_df.empty:
            return self._create_empty_dashboard(output_path)
        
        # Create subplot dashboard
        from plotly.subplots import make_subplots
        
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=("Focus Quality Over Time", "Time Accuracy Analysis", 
                          "Hourly Productivity", "Epic Progress"),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # Focus quality timeline
        fig.add_trace(
            go.Scatter(x=pd.to_datetime(completed_df['start_datetime']), 
                      y=completed_df['focus_quality'],
                      mode='lines+markers', name='Focus Quality',
                      line=dict(color='#2E8B57')),
            row=1, col=1
        )
        
        # Accuracy scatter plot
        fig.add_trace(
            go.Scatter(x=completed_df['estimate_minutes'], 
                      y=completed_df['actual_minutes'],
                      mode='markers', name='Actual vs Estimated',
                      marker=dict(color=completed_df['focus_quality'], 
                                 colorscale='RdYlGn', size=8)),
            row=1, col=2
        )
        
        # Add perfect accuracy line
        max_time = max(completed_df['estimate_minutes'].max(), 
                      completed_df['actual_minutes'].max())
        fig.add_trace(
            go.Scatter(x=[0, max_time], y=[0, max_time],
                      mode='lines', name='Perfect Accuracy',
                      line=dict(dash='dash', color='gray')),
            row=1, col=2
        )
        
        # Hourly productivity heatmap
        hourly_data = completed_df.groupby('start_hour')['focus_quality'].mean()
        fig.add_trace(
            go.Bar(x=hourly_data.index, y=hourly_data.values,
                   name='Hourly Focus', marker_color='#4169E1'),
            row=2, col=1
        )
        
        # Epic progress
        epic_progress = completed_df.groupby('epic_id').size()
        fig.add_trace(
            go.Bar(x=epic_progress.index, y=epic_progress.values,
                   name='Tasks by Epic', marker_color='#FFD700'),
            row=2, col=2
        )
        
        # Update layout
        fig.update_layout(
            height=800,
            title_text="🧠 TDAH TDD Focus Analytics Dashboard",
            title_x=0.5,
            showlegend=True
        )
        
        # Cache dashboard data for future use
        if self.lru_cache:
            dashboard_data = {
                'completed_df': completed_df,
                'generated_at': datetime.now().isoformat()
            }
            self.lru_cache.set(cache_key, dashboard_data)
        
        # Save dashboard with optimized settings
        config = {
            'displayModeBar': True,
            'displaylogo': False,
            'modeBarButtonsToRemove': ['pan2d', 'lasso2d'],
            'responsive': True
        }
        fig.write_html(output_path, config=config)
        
        log_info(f"Dashboard created", {"output": output_path, "sessions": len(completed_df)})
        return f"Dashboard saved to {output_path}"
    
    def _create_dashboard_fallback(self, output_path: str) -> str:
        """Create a basic HTML dashboard when Plotly is unavailable."""
        log_warning(
            "Advanced dashboard unavailable", 
            {"missing_deps": ["plotly"], "fallback": "html_report"}
        )
        print("📊 Advanced dashboard unavailable. Install plotly for interactive visualizations.")
        
        # Create basic HTML report
        data = self.load_session_data(30)
        
        if not data:
            return "No data available for dashboard"
        
        completed_sessions = [s for s in data if s['status'] == 'completed'] if isinstance(data, list) else []
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>🧠 TDAH TDD Focus Analytics</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; }}
        .metric {{ background: #e8f4f8; padding: 15px; margin: 10px 0; border-radius: 8px; }}
        .metric h3 {{ margin: 0 0 10px 0; color: #2c3e50; }}
        .value {{ font-size: 24px; font-weight: bold; color: #3498db; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🧠 TDAH TDD Focus Analytics Dashboard</h1>
        <p><em>Basic view - install plotly, pandas, and numpy for interactive charts</em></p>
        
        <div class="metric">
            <h3>📊 Session Summary</h3>
            <div class="value">{len(completed_sessions)} completed sessions</div>
        </div>
        
        <div class="metric">
            <h3>⏱️ Average Focus Quality</h3>
            <div class="value">{sum(s['focus_quality'] for s in completed_sessions) / len(completed_sessions) if completed_sessions else 0:.2f}</div>
        </div>
        
        <div class="metric">
            <h3>🎯 Accuracy Rate</h3>
            <div class="value">{sum(1 for s in completed_sessions if s['is_accurate']) / len(completed_sessions) * 100 if completed_sessions else 0:.1f}%</div>
        </div>
        
        <div class="metric">
            <h3>⚡ Recommendations</h3>
            <ul>
                <li>🍅 Use 25-minute focused work sessions</li>
                <li>🚶‍♂️ Take regular movement breaks</li>
                <li>📈 Track your patterns consistently</li>
                <li>💡 Install analytics dependencies for advanced insights</li>
            </ul>
        </div>
    </div>
</body>
</html>"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return f"Basic dashboard saved to {output_path}"
    
    @performance_critical("export_analytics_report")
    def export_analytics_report(self, output_path: str = "tdah_analytics_report.json") -> str:
        """Export comprehensive analytics report with performance monitoring."""
        metrics = self.generate_productivity_metrics()
        time_patterns = self.analyze_time_patterns()
        
        # Add performance metrics to report
        perf_report = self.performance_monitor.get_performance_report() if self.performance_monitor else {}
        
        report = {
            "generated_at": datetime.now().isoformat(),
            "productivity_metrics": {
                "focus_score": metrics.focus_score,
                "accuracy_score": metrics.accuracy_score,
                "consistency_score": metrics.consistency_score,
                "optimal_work_duration": metrics.optimal_work_duration,
                "recommended_break_frequency": metrics.recommended_break_frequency
            },
            "time_patterns": time_patterns,
            "recommendations": {
                "immediate_actions": [
                    f"Schedule focused work during {time_patterns.get('recommendations', {}).get('peak_hours', [])}",
                    f"Use {metrics.optimal_work_duration}-minute work sessions",
                    f"Take breaks every {metrics.recommended_break_frequency} minutes"
                ],
                "long_term_goals": [
                    "Increase accuracy score above 0.8",
                    "Improve focus consistency",
                    "Track break adherence"
                ]
            }
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        return f"Analytics report saved to {output_path}"


def main():
    """CLI interface for analytics engine."""
    import argparse
    
    parser = argparse.ArgumentParser(description="📊 TDAH TDD Analytics Engine")
    parser.add_argument("command", choices=["metrics", "patterns", "predict", "dashboard", "report"])
    parser.add_argument("--epic", help="Epic ID for prediction")
    parser.add_argument("--days", type=int, default=30, help="Days of data to analyze")
    parser.add_argument("--output", help="Output file path")
    
    args = parser.parse_args()
    
    # Check for optional dependencies and warn user
    missing_deps = []
    if not PANDAS_AVAILABLE:
        missing_deps.append("pandas")
    if not PLOTLY_AVAILABLE:
        missing_deps.append("plotly")
    if not NUMPY_AVAILABLE:
        missing_deps.append("numpy")
    
    if missing_deps:
        print(f"⚠️  Optional dependencies missing: {', '.join(missing_deps)}")
        print("   Install with: pip install pandas plotly numpy")
        print("   Running in basic mode...\n")
    
    analytics = TDDAHAnalytics()
    
    try:
        if args.command == "metrics":
            metrics = analytics.generate_productivity_metrics(args.days)
            print(f"📊 Productivity Metrics ({args.days} days)")
            print(f"Focus Score: {metrics.focus_score:.2f}")
            print(f"Accuracy Score: {metrics.accuracy_score:.2f}")
            print(f"Consistency Score: {metrics.consistency_score:.2f}")
            print(f"Optimal Work Duration: {metrics.optimal_work_duration} minutes")
            
        elif args.command == "patterns":
            patterns = analytics.analyze_time_patterns(args.days)
            if "error" in patterns:
                print(f"❌ {patterns['error']}")
                return 1
            print("⏰ Optimal Time Patterns")
            print(f"Peak Hours: {patterns.get('recommendations', {}).get('peak_hours', [])}")
            print(f"Peak Days: {patterns.get('recommendations', {}).get('peak_days', [])}")
            
        elif args.command == "predict":
            if not args.epic:
                print("❌ Epic ID required for prediction")
                return 1
            prediction = analytics.predict_epic_completion(args.epic)
            if "error" in prediction:
                print(f"❌ {prediction['error']}")
                return 1
            print(f"🔮 Epic {args.epic} Prediction")
            print(f"Completion: {prediction['completion_percentage']}%")
            print(f"Estimated remaining: {prediction['estimated_remaining_hours']} hours")
            
        elif args.command == "dashboard":
            output = args.output or "focus_dashboard.html"
            result = analytics.create_focus_dashboard(output)
            print(f"📈 {result}")
            
        elif args.command == "report":
            output = args.output or "tdah_analytics_report.json"  
            result = analytics.export_analytics_report(output)
            print(f"📋 {result}")
            
    except Exception as e:
        error_report = handle_error(
            exception=e,
            user_action="Check analytics configuration and data files",
            context={"command": args.command, "args": vars(args)}
        )
        print(f"❌ Error running analytics: {error_report.message}")
        return 1
    
    return 0


if __name__ == "__main__":
    main()