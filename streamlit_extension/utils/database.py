"""
🗄️ Database Management Utilities

Streamlit-optimized database operations with:
- Connection pooling
- Caching strategies
- SQLAlchemy integration
- Error handling
"""

import sqlite3
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
from contextlib import contextmanager
from datetime import datetime
import json
import logging

# Graceful imports
try:
    import sqlalchemy as sa
    from sqlalchemy import create_engine, text
    from sqlalchemy.pool import StaticPool
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    sa = None
    create_engine = None
    text = None
    StaticPool = None
    SQLALCHEMY_AVAILABLE = False

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    pd = None
    PANDAS_AVAILABLE = False

try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    st = None
    STREAMLIT_AVAILABLE = False

# Import timezone utilities
try:
    from ..config.streamlit_config import format_datetime_user_tz, format_time_ago_user_tz
    TIMEZONE_UTILS_AVAILABLE = True
except ImportError:
    TIMEZONE_UTILS_AVAILABLE = False
    format_datetime_user_tz = None
    format_time_ago_user_tz = None

# Import duration system for FASE 2.3 extension
try:
    from duration_system.duration_calculator import DurationCalculator
    from duration_system.duration_formatter import DurationFormatter
    DURATION_SYSTEM_AVAILABLE = True
except ImportError:
    DurationCalculator = None
    DurationFormatter = None
    DURATION_SYSTEM_AVAILABLE = False

# Import caching system
try:
    from .cache import cache_database_query, invalidate_cache_on_change, get_cache
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False
    cache_database_query = invalidate_cache_on_change = get_cache = None

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Streamlit-optimized database manager."""
    
    def __init__(self, framework_db_path: str = "framework.db", timer_db_path: str = "task_timer.db"):
        self.framework_db_path = Path(framework_db_path)
        self.timer_db_path = Path(timer_db_path)
        self.engines = {}
        
        if SQLALCHEMY_AVAILABLE:
            self._initialize_engines()
    
    def _initialize_engines(self):
        """Initialize SQLAlchemy engines with optimized settings."""
        if not SQLALCHEMY_AVAILABLE:
            return
        
        # Framework database engine
        if self.framework_db_path.exists():
            framework_url = f"sqlite:///{self.framework_db_path}"
            self.engines["framework"] = create_engine(
                framework_url,
                poolclass=StaticPool,
                connect_args={
                    "check_same_thread": False,
                    "timeout": 20
                },
                echo=False
            )
        
        # Timer database engine  
        if self.timer_db_path.exists():
            timer_url = f"sqlite:///{self.timer_db_path}"
            self.engines["timer"] = create_engine(
                timer_url,
                poolclass=StaticPool,
                connect_args={
                    "check_same_thread": False,
                    "timeout": 20
                },
                echo=False
            )
    
    @contextmanager
    def get_connection(self, db_name: str = "framework"):
        """Get database connection with context manager."""
        if SQLALCHEMY_AVAILABLE and db_name in self.engines:
            # Use SQLAlchemy engine
            conn = self.engines[db_name].connect()
            try:
                yield conn
            finally:
                conn.close()
        else:
            # Fallback to sqlite3
            db_path = self.framework_db_path if db_name == "framework" else self.timer_db_path
            if not db_path.exists():
                raise FileNotFoundError(f"Database not found: {db_path}")
            
            conn = sqlite3.connect(str(db_path), timeout=20)
            conn.row_factory = sqlite3.Row
            try:
                yield conn
            finally:
                conn.close()
    
    @cache_database_query("get_epics", ttl=300) if CACHE_AVAILABLE else lambda f: f
    def get_epics(self) -> List[Dict[str, Any]]:
        """Get all epics with intelligent caching."""
        try:
            with self.get_connection("framework") as conn:
                if SQLALCHEMY_AVAILABLE:
                    result = conn.execute(text("""
                        SELECT id, epic_key, name, description, status, 
                               created_at, updated_at, completed_at,
                               points_earned, difficulty_level
                        FROM framework_epics 
                        WHERE deleted_at IS NULL
                        ORDER BY created_at DESC
                    """))
                    return [dict(row._mapping) for row in result]
                else:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT id, epic_key, name, description, status,
                               created_at, updated_at, completed_at,
                               points_earned, difficulty_level
                        FROM framework_epics 
                        WHERE deleted_at IS NULL
                        ORDER BY created_at DESC
                    """)
                    return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error loading epics: {e}")
            return []
    
    @cache_database_query("get_tasks", ttl=300) if CACHE_AVAILABLE else lambda f: f
    def get_tasks(self, epic_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get tasks with intelligent caching, optionally filtered by epic."""
        try:
            with self.get_connection("framework") as conn:
                query = """
                    SELECT t.id, t.epic_id, t.title, t.description, t.status,
                           t.estimate_minutes, t.tdd_phase, t.priority,
                           t.created_at, t.updated_at, t.completed_at,
                           e.name as epic_name, e.epic_key
                    FROM framework_tasks t
                    JOIN framework_epics e ON t.epic_id = e.id
                    WHERE t.deleted_at IS NULL
                """
                
                params = []
                if epic_id:
                    query += " AND t.epic_id = ?"
                    params.append(epic_id)
                
                query += " ORDER BY t.priority DESC, t.created_at DESC"
                
                if SQLALCHEMY_AVAILABLE:
                    result = conn.execute(text(query), params)
                    return [dict(row._mapping) for row in result]
                else:
                    cursor = conn.cursor()
                    cursor.execute(query, params)
                    return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error loading tasks: {e}")
            return []
    
    @cache_database_query("get_timer_sessions", ttl=60) if CACHE_AVAILABLE else lambda f: f
    def get_timer_sessions(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get recent timer sessions with short-term caching."""
        if not self.timer_db_path.exists():
            return []
        
        try:
            with self.get_connection("timer") as conn:
                query = """
                    SELECT task_reference, user_identifier, started_at, ended_at,
                           planned_duration_minutes, actual_duration_minutes,
                           focus_rating, energy_level, mood_rating,
                           interruptions_count,
                           created_at
                    FROM timer_sessions
                    WHERE created_at >= DATE('now', ? || ' days')
                    ORDER BY created_at DESC
                    LIMIT 1000
                """
                
                if SQLALCHEMY_AVAILABLE:
                    result = conn.execute(text(query), [f"-{days}"])
                    return [dict(row._mapping) for row in result]
                else:
                    cursor = conn.cursor()
                    cursor.execute(query, [f"-{days}"])
                    return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error loading timer sessions: {e}")
            return []
    
    def get_user_stats(self, user_id: int = 1) -> Dict[str, Any]:
        """Get user statistics and gamification data."""
        try:
            with self.get_connection("framework") as conn:
                stats = {}
                
                # Basic stats
                if SQLALCHEMY_AVAILABLE:
                    # Tasks completed
                    result = conn.execute(text("""
                        SELECT COUNT(*) as completed_tasks
                        FROM framework_tasks 
                        WHERE status = 'completed' AND deleted_at IS NULL
                    """))
                    stats["completed_tasks"] = result.scalar()
                    
                    # Total points
                    result = conn.execute(text("""
                        SELECT COALESCE(SUM(points_earned), 0) as total_points
                        FROM framework_epics WHERE deleted_at IS NULL
                    """))
                    stats["total_points"] = result.scalar()
                    
                    # Active streaks
                    result = conn.execute(text("""
                        SELECT COUNT(*) as active_streaks
                        FROM user_streaks 
                        WHERE user_id = ? AND current_count > 0
                    """), [user_id])
                    stats["active_streaks"] = result.scalar()
                    
                else:
                    cursor = conn.cursor()
                    
                    # Tasks completed
                    cursor.execute("""
                        SELECT COUNT(*) FROM framework_tasks 
                        WHERE status = 'completed' AND deleted_at IS NULL
                    """)
                    stats["completed_tasks"] = cursor.fetchone()[0]
                    
                    # Total points
                    cursor.execute("""
                        SELECT COALESCE(SUM(points_earned), 0) 
                        FROM framework_epics WHERE deleted_at IS NULL
                    """)
                    stats["total_points"] = cursor.fetchone()[0]
                    
                    # Active streaks
                    cursor.execute("""
                        SELECT COUNT(*) FROM user_streaks 
                        WHERE user_id = ? AND current_count > 0
                    """, [user_id])
                    stats["active_streaks"] = cursor.fetchone()[0]
                
                return stats
                
        except Exception as e:
            print(f"Error loading user stats: {e}")
            return {
                "completed_tasks": 0,
                "total_points": 0,
                "active_streaks": 0
            }
    
    def get_achievements(self, user_id: int = 1) -> List[Dict[str, Any]]:
        """Get user achievements."""
        try:
            with self.get_connection("framework") as conn:
                query = """
                    SELECT at.code, at.name, at.description, at.category,
                           at.points_reward, at.rarity, ua.unlocked_at
                    FROM user_achievements ua
                    JOIN achievement_types at ON ua.achievement_code = at.code
                    WHERE ua.user_id = ?
                    ORDER BY ua.unlocked_at DESC
                """
                
                if SQLALCHEMY_AVAILABLE:
                    result = conn.execute(text(query), [user_id])
                    return [dict(row._mapping) for row in result]
                else:
                    cursor = conn.cursor()
                    cursor.execute(query, [user_id])
                    return [dict(row) for row in cursor.fetchall()]
                    
        except Exception as e:
            print(f"Error loading achievements: {e}")
            return []
    
    @invalidate_cache_on_change("db_query:get_tasks:", "db_query:get_epics:") if CACHE_AVAILABLE else lambda f: f
    def update_task_status(self, task_id: int, status: str, tdd_phase: Optional[str] = None) -> bool:
        """Update task status and TDD phase with cache invalidation."""
        try:
            with self.get_connection("framework") as conn:
                if SQLALCHEMY_AVAILABLE:
                    query = "UPDATE framework_tasks SET status = ?, updated_at = CURRENT_TIMESTAMP"
                    params = [status]
                    
                    if tdd_phase:
                        query += ", tdd_phase = ?"
                        params.append(tdd_phase)
                    
                    if status == 'completed':
                        query += ", completed_at = CURRENT_TIMESTAMP"
                    
                    query += " WHERE id = ?"
                    params.append(task_id)
                    
                    conn.execute(text(query), params)
                    conn.commit()
                else:
                    cursor = conn.cursor()
                    query = "UPDATE framework_tasks SET status = ?, updated_at = CURRENT_TIMESTAMP"
                    params = [status]
                    
                    if tdd_phase:
                        query += ", tdd_phase = ?"
                        params.append(tdd_phase)
                    
                    if status == 'completed':
                        query += ", completed_at = CURRENT_TIMESTAMP"
                    
                    query += " WHERE id = ?"
                    params.append(task_id)
                    
                    cursor.execute(query, params)
                    conn.commit()
                
                return True
                
        except Exception as e:
            print(f"Error updating task status: {e}")
            return False
    
    @invalidate_cache_on_change("db_query:get_timer_sessions:") if CACHE_AVAILABLE else lambda f: f
    def create_timer_session(self, task_id: Optional[int], duration_minutes: int, 
                           focus_rating: Optional[int] = None, interruptions: int = 0,
                           actual_duration_minutes: Optional[int] = None,
                           ended_at: Optional[str] = None, notes: Optional[str] = None) -> bool:
        """Create a new timer session record with cache invalidation."""
        if not self.timer_db_path.exists():
            return False
        
        try:
            with self.get_connection("timer") as conn:
                if SQLALCHEMY_AVAILABLE:
                    conn.execute(text("""
                        INSERT INTO timer_sessions (
                            task_reference, user_identifier, started_at, ended_at,
                            planned_duration_minutes, actual_duration_minutes,
                            focus_rating, interruptions_count, notes, created_at
                        ) VALUES (?, 'user1', CURRENT_TIMESTAMP, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """), [
                        str(task_id) if task_id else None,
                        ended_at,
                        duration_minutes,
                        actual_duration_minutes or duration_minutes,
                        focus_rating,
                        interruptions,
                        notes
                    ])
                    conn.commit()
                else:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO timer_sessions (
                            task_reference, user_identifier, started_at, ended_at,
                            planned_duration_minutes, actual_duration_minutes,
                            focus_rating, interruptions_count, notes, created_at
                        ) VALUES (?, 'user1', CURRENT_TIMESTAMP, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """, [
                        str(task_id) if task_id else None,
                        ended_at,
                        duration_minutes,
                        actual_duration_minutes or duration_minutes,
                        focus_rating,
                        interruptions,
                        notes
                    ])
                    conn.commit()
                
                return True
                
        except Exception as e:
            print(f"Error creating timer session: {e}")
            return False
    
    def get_epic_progress(self, epic_id: int) -> Dict[str, Any]:
        """Get detailed progress for an epic."""
        try:
            with self.get_connection("framework") as conn:
                if SQLALCHEMY_AVAILABLE:
                    # Get epic info
                    epic_result = conn.execute(text("""
                        SELECT id, epic_key, name, status, points_earned
                        FROM framework_epics WHERE id = ?
                    """), [epic_id])
                    epic = dict(epic_result.fetchone()._mapping)
                    
                    # Get task counts
                    task_result = conn.execute(text("""
                        SELECT 
                            COUNT(*) as total_tasks,
                            SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_tasks,
                            SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress_tasks
                        FROM framework_tasks WHERE epic_id = ? AND deleted_at IS NULL
                    """), [epic_id])
                    tasks = dict(task_result.fetchone()._mapping)
                    
                else:
                    cursor = conn.cursor()
                    
                    # Get epic info
                    cursor.execute("""
                        SELECT id, epic_key, name, status, points_earned
                        FROM framework_epics WHERE id = ?
                    """, [epic_id])
                    epic = dict(cursor.fetchone())
                    
                    # Get task counts
                    cursor.execute("""
                        SELECT 
                            COUNT(*) as total_tasks,
                            SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_tasks,
                            SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress_tasks
                        FROM framework_tasks WHERE epic_id = ? AND deleted_at IS NULL
                    """, [epic_id])
                    tasks = dict(cursor.fetchone())
                
                # Calculate progress
                total = tasks["total_tasks"] or 0
                completed = tasks["completed_tasks"] or 0
                progress_pct = (completed / total * 100) if total > 0 else 0
                
                return {
                    **epic,
                    **tasks,
                    "progress_percentage": round(progress_pct, 1)
                }
                
        except Exception as e:
            print(f"Error getting epic progress: {e}")
            return {}
    
    def check_database_health(self) -> Dict[str, Any]:
        """Check database connectivity and basic health."""
        health = {
            "framework_db_exists": self.framework_db_path.exists(),
            "timer_db_exists": self.timer_db_path.exists(),
            "framework_db_connected": False,
            "timer_db_connected": False,
            "sqlalchemy_available": SQLALCHEMY_AVAILABLE,
            "pandas_available": PANDAS_AVAILABLE
        }
        
        # Test framework DB connection
        try:
            with self.get_connection("framework") as conn:
                if SQLALCHEMY_AVAILABLE:
                    conn.execute(text("SELECT 1"))
                else:
                    conn.execute("SELECT 1")
                health["framework_db_connected"] = True
        except Exception as e:
            # Log database connection failure for debugging
            import logging
            logging.getLogger(__name__).debug(f"Framework DB connection failed: {e}")
            health["framework_db_connected"] = False
        
        # Test timer DB connection
        if self.timer_db_path.exists():
            try:
                with self.get_connection("timer") as conn:
                    if SQLALCHEMY_AVAILABLE:
                        conn.execute(text("SELECT 1"))
                    else:
                        conn.execute("SELECT 1")
                    health["timer_db_connected"] = True
            except Exception as e:
                # Log timer database connection failure for debugging
                import logging
                logging.getLogger(__name__).debug(f"Timer DB connection failed: {e}")
                health["timer_db_connected"] = False
        
        return health
    
    def format_database_datetime(self, dt_string: str, format_type: str = "full") -> str:
        """Format database datetime string with user timezone."""
        if not dt_string or not TIMEZONE_UTILS_AVAILABLE:
            return dt_string or "Unknown"
        
        try:
            # Parse database datetime (assume UTC/ISO format)
            if 'T' in dt_string:
                dt = datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
            else:
                dt = datetime.strptime(dt_string, "%Y-%m-%d %H:%M:%S")
            
            if format_type == "ago":
                return format_time_ago_user_tz(dt)
            elif format_type == "date":
                return format_datetime_user_tz(dt, "%Y-%m-%d")
            elif format_type == "time":
                return format_datetime_user_tz(dt, "%H:%M")
            elif format_type == "short":
                return format_datetime_user_tz(dt, "%m/%d %H:%M")
            else:  # full
                return format_datetime_user_tz(dt, "%Y-%m-%d %H:%M:%S")
                
        except (ValueError, TypeError) as e:
            return dt_string or "Invalid date"
    
    def get_formatted_epic_data(self) -> List[Dict[str, Any]]:
        """Get epics with formatted datetime fields."""
        epics = self.get_epics()
        
        for epic in epics:
            if 'created_at' in epic:
                epic['created_at_formatted'] = self.format_database_datetime(epic['created_at'], "short")
                epic['created_at_ago'] = self.format_database_datetime(epic['created_at'], "ago")
            
            if 'updated_at' in epic:
                epic['updated_at_formatted'] = self.format_database_datetime(epic['updated_at'], "short")
                epic['updated_at_ago'] = self.format_database_datetime(epic['updated_at'], "ago")
            
            if 'completed_at' in epic and epic['completed_at']:
                epic['completed_at_formatted'] = self.format_database_datetime(epic['completed_at'], "short")
                epic['completed_at_ago'] = self.format_database_datetime(epic['completed_at'], "ago")
        
        return epics
    
    def get_formatted_timer_sessions(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get timer sessions with formatted datetime fields."""
        sessions = self.get_timer_sessions(days)
        
        for session in sessions:
            if 'started_at' in session:
                session['started_at_formatted'] = self.format_database_datetime(session['started_at'], "short")
                session['started_at_ago'] = self.format_database_datetime(session['started_at'], "ago")
            
            if 'ended_at' in session and session['ended_at']:
                session['ended_at_formatted'] = self.format_database_datetime(session['ended_at'], "short")
                session['ended_at_ago'] = self.format_database_datetime(session['ended_at'], "ago")
            
            if 'created_at' in session:
                session['created_at_formatted'] = self.format_database_datetime(session['created_at'], "short")
                session['created_at_ago'] = self.format_database_datetime(session['created_at'], "ago")
        
        return sessions
    
    def clear_cache(self):
        """Clear all database query caches."""
        if CACHE_AVAILABLE:
            cache = get_cache()
            # Clear all database query caches
            cache.invalidate_pattern("db_query:")
            print("Database cache cleared")
        else:
            print("Cache not available")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get database cache statistics."""
        if CACHE_AVAILABLE:
            from .cache import get_cache_statistics
            return get_cache_statistics()
        else:
            return {"cache_available": False}
    
    @cache_database_query("get_productivity_stats", ttl=60) if CACHE_AVAILABLE else lambda f: f
    def get_productivity_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get productivity statistics for the last N days."""
        stats = {
            "activity_by_date": {},
            "tasks_completed_total": 0,
            "focus_time_total": 0,
            "average_daily_tasks": 0,
            "average_focus_time": 0,
            "most_productive_day": None,
            "current_streak": 0,
            "best_streak": 0
        }
        
        try:
            # Get task activity for last N days
            with self.get_connection("framework") as conn:
                if SQLALCHEMY_AVAILABLE:
                    result = conn.execute(text("""
                        SELECT DATE(updated_at) as date, COUNT(*) as count
                        FROM framework_tasks
                        WHERE updated_at >= DATE('now', :days)
                        AND status = 'completed'
                        GROUP BY DATE(updated_at)
                        ORDER BY date DESC
                    """), {"days": f"-{days} days"})
                    
                    for row in result:
                        date_str = str(row[0])  # Access by index for compatibility
                        count = row[1]
                        stats["activity_by_date"][date_str] = count
                        stats["tasks_completed_total"] += count
                else:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT DATE(updated_at) as date, COUNT(*) as count
                        FROM framework_tasks
                        WHERE updated_at >= DATE('now', ?)
                        AND status = 'completed'
                        GROUP BY DATE(updated_at)
                        ORDER BY date DESC
                    """, (f"-{days} days",))
                    
                    for row in cursor.fetchall():
                        date_str = row[0]
                        stats["activity_by_date"][date_str] = row[1]
                        stats["tasks_completed_total"] += row[1]
            
            # Get focus time from timer database
            if self.timer_db_path.exists():
                with self.get_connection("timer") as conn:
                    if SQLALCHEMY_AVAILABLE:
                        result = conn.execute(text("""
                            SELECT DATE(started_at) as date, 
                                   SUM(actual_duration_minutes) as total_minutes
                            FROM timer_sessions
                            WHERE started_at >= DATE('now', :days)
                            GROUP BY DATE(started_at)
                        """), {"days": f"-{days} days"})
                        
                        for row in result:
                            stats["focus_time_total"] += row[1] or 0  # Access by index for compatibility
                    else:
                        cursor = conn.cursor()
                        cursor.execute("""
                            SELECT DATE(started_at) as date,
                                   SUM(actual_duration_minutes) as total_minutes
                            FROM timer_sessions
                            WHERE started_at >= DATE('now', ?)
                            GROUP BY DATE(started_at)
                        """, (f"-{days} days",))
                        
                        for row in cursor.fetchall():
                            stats["focus_time_total"] += row[1] or 0
            
            # Calculate averages
            if days > 0:
                stats["average_daily_tasks"] = round(stats["tasks_completed_total"] / days, 1)
                stats["average_focus_time"] = round(stats["focus_time_total"] / days, 1)
            
            # Find most productive day
            if stats["activity_by_date"]:
                most_productive = max(stats["activity_by_date"].items(), key=lambda x: x[1])
                stats["most_productive_day"] = most_productive[0]
            
            # Calculate streaks
            stats["current_streak"] = self._calculate_current_streak()
            stats["best_streak"] = self._get_best_streak()
            
        except Exception as e:
            print(f"Error getting productivity stats: {e}")
        
        return stats
    
    @cache_database_query("get_daily_summary", ttl=60) if CACHE_AVAILABLE else lambda f: f
    def get_daily_summary(self) -> Dict[str, Any]:
        """Get today's activity summary."""
        summary = {
            "tasks_completed": 0,
            "tasks_in_progress": 0,
            "tasks_created": 0,
            "focus_time_minutes": 0,
            "timer_sessions": 0,
            "achievements_today": 0,
            "streak_days": 0,
            "points_earned_today": 0
        }
        
        today = datetime.now().date().isoformat()
        
        try:
            with self.get_connection("framework") as conn:
                if SQLALCHEMY_AVAILABLE:
                    # Tasks completed today
                    result = conn.execute(text("""
                        SELECT COUNT(*) FROM framework_tasks
                        WHERE DATE(updated_at) = :today AND status = 'completed'
                    """), {"today": today})
                    summary["tasks_completed"] = result.scalar() or 0
                    
                    # Tasks in progress
                    result = conn.execute(text("""
                        SELECT COUNT(*) FROM framework_tasks
                        WHERE status = 'in_progress'
                    """))
                    summary["tasks_in_progress"] = result.scalar() or 0
                    
                    # Tasks created today
                    result = conn.execute(text("""
                        SELECT COUNT(*) FROM framework_tasks
                        WHERE DATE(created_at) = :today
                    """), {"today": today})
                    summary["tasks_created"] = result.scalar() or 0
                    
                    # Points earned today
                    result = conn.execute(text("""
                        SELECT SUM(points_value) FROM framework_tasks
                        WHERE DATE(completed_at) = :today AND status = 'completed'
                    """), {"today": today})
                    summary["points_earned_today"] = result.scalar() or 0
                    
                    # Achievements unlocked today
                    result = conn.execute(text("""
                        SELECT COUNT(*) FROM user_achievements
                        WHERE DATE(unlocked_at) = :today
                    """), {"today": today})
                    summary["achievements_today"] = result.scalar() or 0
                    
                    # Current streak
                    result = conn.execute(text("""
                        SELECT current_streak FROM user_streaks
                        WHERE user_id = 1 AND streak_type = 'daily_tasks'
                        ORDER BY updated_at DESC LIMIT 1
                    """))
                    row = result.fetchone()
                    if row:
                        summary["streak_days"] = row[0] or 0
                else:
                    cursor = conn.cursor()
                    
                    # Tasks completed today
                    cursor.execute("""
                        SELECT COUNT(*) FROM framework_tasks
                        WHERE DATE(updated_at) = ? AND status = 'completed'
                    """, (today,))
                    summary["tasks_completed"] = cursor.fetchone()[0] or 0
                    
                    # Tasks in progress
                    cursor.execute("""
                        SELECT COUNT(*) FROM framework_tasks
                        WHERE status = 'in_progress'
                    """)
                    summary["tasks_in_progress"] = cursor.fetchone()[0] or 0
                    
                    # Tasks created today
                    cursor.execute("""
                        SELECT COUNT(*) FROM framework_tasks
                        WHERE DATE(created_at) = ?
                    """, (today,))
                    summary["tasks_created"] = cursor.fetchone()[0] or 0
            
            # Get timer data if available
            if self.timer_db_path.exists():
                with self.get_connection("timer") as conn:
                    if SQLALCHEMY_AVAILABLE:
                        result = conn.execute(text("""
                            SELECT COUNT(*) as sessions, 
                                   SUM(actual_duration_minutes) as total_minutes
                            FROM timer_sessions
                            WHERE DATE(started_at) = :today
                        """), {"today": today})
                        row = result.fetchone()
                        if row:
                            summary["timer_sessions"] = row[0] or 0
                            summary["focus_time_minutes"] = row[1] or 0
                    else:
                        cursor = conn.cursor()
                        cursor.execute("""
                            SELECT COUNT(*) as sessions,
                                   SUM(actual_duration_minutes) as total_minutes
                            FROM timer_sessions
                            WHERE DATE(started_at) = ?
                        """, (today,))
                        row = cursor.fetchone()
                        if row:
                            summary["timer_sessions"] = row[0] or 0
                            summary["focus_time_minutes"] = row[1] or 0
        
        except Exception as e:
            print(f"Error getting daily summary: {e}")
        
        return summary
    
    @cache_database_query("get_pending_notifications", ttl=30) if CACHE_AVAILABLE else lambda f: f
    def get_pending_notifications(self) -> List[Dict[str, Any]]:
        """Get pending notifications for the user."""
        notifications = []
        
        try:
            with self.get_connection("framework") as conn:
                # Check for overdue tasks
                if SQLALCHEMY_AVAILABLE:
                    result = conn.execute(text("""
                        SELECT title, due_date FROM framework_tasks
                        WHERE status != 'completed' 
                        AND due_date IS NOT NULL
                        AND DATE(due_date) <= DATE('now')
                        LIMIT 5
                    """))
                    
                    for row in result:
                        notifications.append({
                            "type": "warning",
                            "title": "Task Overdue",
                            "message": f"{row[0]} was due {row[1]}",
                            "timestamp": datetime.now()
                        })
                
                # Check for long-running tasks
                if SQLALCHEMY_AVAILABLE:
                    result = conn.execute(text("""
                        SELECT title FROM framework_tasks
                        WHERE status = 'in_progress'
                        AND julianday('now') - julianday(updated_at) > 3
                        LIMIT 3
                    """))
                    
                    for row in result:
                        notifications.append({
                            "type": "info",
                            "title": "Long Running Task",
                            "message": f"{row[0]} has been in progress for over 3 days",
                            "timestamp": datetime.now()
                        })
        
        except Exception as e:
            print(f"Error getting notifications: {e}")
        
        return notifications
    
    @cache_database_query("get_user_achievements", ttl=300) if CACHE_AVAILABLE else lambda f: f
    def get_user_achievements(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get user achievements."""
        achievements = []
        
        try:
            with self.get_connection("framework") as conn:
                if SQLALCHEMY_AVAILABLE:
                    result = conn.execute(text("""
                        SELECT at.name, at.description, at.icon, at.points_value,
                               ua.unlocked_at, ua.progress_value
                        FROM achievement_types at
                        LEFT JOIN user_achievements ua ON at.id = ua.achievement_id
                        WHERE at.is_active = TRUE
                        ORDER BY ua.unlocked_at DESC NULLS LAST
                        LIMIT :limit
                    """), {"limit": limit})
                    
                    for row in result:
                        achievements.append({
                            "name": row[0],
                            "description": row[1], 
                            "icon": row[2] or "🏆",
                            "points": row[3],
                            "unlocked": row[4] is not None,
                            "unlocked_at": row[4],
                            "progress": row[5]
                        })
                else:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT at.name, at.description, at.icon, at.points_value,
                               ua.unlocked_at, ua.progress_value
                        FROM achievement_types at
                        LEFT JOIN user_achievements ua ON at.id = ua.achievement_id
                        WHERE at.is_active = 1
                        ORDER BY ua.unlocked_at DESC
                        LIMIT ?
                    """, (limit,))
                    
                    for row in cursor.fetchall():
                        achievements.append({
                            "name": row[0],
                            "description": row[1],
                            "icon": row[2] or "🏆",
                            "points": row[3],
                            "unlocked": row[4] is not None,
                            "unlocked_at": row[4],
                            "progress": row[5]
                        })
        
        except Exception as e:
            print(f"Error getting achievements: {e}")
        
        return achievements
    
    def _calculate_current_streak(self) -> int:
        """Calculate current task completion streak."""
        try:
            with self.get_connection("framework") as conn:
                if SQLALCHEMY_AVAILABLE:
                    result = conn.execute(text("""
                        SELECT current_streak FROM user_streaks
                        WHERE user_id = 1 AND streak_type = 'daily_tasks'
                        ORDER BY updated_at DESC LIMIT 1
                    """))
                    row = result.fetchone()
                    return row[0] if row else 0
                else:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT current_streak FROM user_streaks
                        WHERE user_id = 1 AND streak_type = 'daily_tasks'
                        ORDER BY updated_at DESC LIMIT 1
                    """)
                    row = cursor.fetchone()
                    return row[0] if row else 0
        except Exception:
            return 0
    
    def _get_best_streak(self) -> int:
        """Get best streak record."""
        try:
            with self.get_connection("framework") as conn:
                if SQLALCHEMY_AVAILABLE:
                    result = conn.execute(text("""
                        SELECT best_streak FROM user_streaks
                        WHERE user_id = 1 AND streak_type = 'daily_tasks'
                        ORDER BY best_streak DESC LIMIT 1
                    """))
                    row = result.fetchone()
                    return row[0] if row else 0
                else:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT best_streak FROM user_streaks
                        WHERE user_id = 1 AND streak_type = 'daily_tasks'
                        ORDER BY best_streak DESC LIMIT 1
                    """)
                    row = cursor.fetchone()
                    return row[0] if row else 0
        except Exception:
            return 0
    
    # CRUD Operations for Tasks
    
    def create_task(self, title: str, epic_id: int, description: str = "", 
                   tdd_phase: str = "", priority: int = 2, 
                   estimate_minutes: int = 0) -> Optional[int]:
        """Create a new task in the database.
        
        Args:
            title: Task title
            epic_id: ID of the associated epic
            description: Optional task description
            tdd_phase: TDD phase (red, green, refactor)
            priority: Task priority (1=High, 2=Medium, 3=Low)
            estimate_minutes: Estimated time in minutes
            
        Returns:
            Task ID if successful, None otherwise
        """
        try:
            with self.get_connection("framework") as conn:
                if SQLALCHEMY_AVAILABLE:
                    result = conn.execute(text("""
                        INSERT INTO framework_tasks 
                        (title, description, epic_id, tdd_phase, priority, 
                         estimate_minutes, status, created_at, updated_at)
                        VALUES (:title, :description, :epic_id, :tdd_phase, 
                               :priority, :estimate_minutes, 'todo', 
                               datetime('now'), datetime('now'))
                    """), {
                        "title": title,
                        "description": description,
                        "epic_id": epic_id,
                        "tdd_phase": tdd_phase,
                        "priority": priority,
                        "estimate_minutes": estimate_minutes
                    })
                    conn.commit()
                    return result.lastrowid
                else:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO framework_tasks 
                        (title, description, epic_id, tdd_phase, priority, 
                         estimate_minutes, status, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, 'todo', datetime('now'), datetime('now'))
                    """, (title, description, epic_id, tdd_phase, priority, estimate_minutes))
                    conn.commit()
                    return cursor.lastrowid
        except Exception as e:
            print(f"Error creating task: {e}")
            return None
    
    def update_task(self, task_id: int, title: str = None, description: str = None,
                   tdd_phase: str = None, priority: int = None, 
                   estimate_minutes: int = None) -> bool:
        """Update task details.
        
        Args:
            task_id: ID of the task to update
            title: New title (optional)
            description: New description (optional)
            tdd_phase: New TDD phase (optional)
            priority: New priority (optional)
            estimate_minutes: New estimate (optional)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Build dynamic update query
            updates = []
            params = {"task_id": task_id}
            
            if title is not None:
                updates.append("title = :title")
                params["title"] = title
            
            if description is not None:
                updates.append("description = :description")
                params["description"] = description
                
            if tdd_phase is not None:
                updates.append("tdd_phase = :tdd_phase")
                params["tdd_phase"] = tdd_phase
                
            if priority is not None:
                updates.append("priority = :priority")
                params["priority"] = priority
                
            if estimate_minutes is not None:
                updates.append("estimate_minutes = :estimate_minutes")
                params["estimate_minutes"] = estimate_minutes
            
            if not updates:
                return True  # Nothing to update
                
            updates.append("updated_at = datetime('now')")
            # Security: Column names are hardcoded in this function, safe from SQL injection
            query = f"UPDATE framework_tasks SET {', '.join(updates)} WHERE id = :task_id"  # nosec B608
            
            with self.get_connection("framework") as conn:
                if SQLALCHEMY_AVAILABLE:
                    conn.execute(text(query), params)
                    conn.commit()
                else:
                    # Convert to positional parameters for sqlite3
                    positional_params = []
                    positional_query = query.replace(":title", "?").replace(":description", "?")
                    positional_query = positional_query.replace(":tdd_phase", "?").replace(":priority", "?")
                    positional_query = positional_query.replace(":estimate_minutes", "?").replace(":task_id", "?")
                    
                    for key in ["title", "description", "tdd_phase", "priority", "estimate_minutes"]:
                        if key in params:
                            positional_params.append(params[key])
                    positional_params.append(task_id)
                    
                    cursor = conn.cursor()
                    cursor.execute(positional_query, positional_params)
                    conn.commit()
                
                return True
        except Exception as e:
            print(f"Error updating task {task_id}: {e}")
            return False
    
    def delete_task(self, task_id: int, soft_delete: bool = True) -> bool:
        """Delete a task (soft delete by default).
        
        Args:
            task_id: ID of the task to delete
            soft_delete: If True, mark as deleted; if False, actually delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.get_connection("framework") as conn:
                if soft_delete:
                    # Soft delete: mark as deleted
                    if SQLALCHEMY_AVAILABLE:
                        conn.execute(text("""
                            UPDATE framework_tasks 
                            SET deleted_at = datetime('now'), updated_at = datetime('now')
                            WHERE id = :task_id
                        """), {"task_id": task_id})
                        conn.commit()
                    else:
                        cursor = conn.cursor()
                        cursor.execute("""
                            UPDATE framework_tasks 
                            SET deleted_at = datetime('now'), updated_at = datetime('now')
                            WHERE id = ?
                        """, (task_id,))
                        conn.commit()
                else:
                    # Hard delete: actually remove from database
                    if SQLALCHEMY_AVAILABLE:
                        conn.execute(text("DELETE FROM framework_tasks WHERE id = :task_id"), 
                                   {"task_id": task_id})
                        conn.commit()
                    else:
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM framework_tasks WHERE id = ?", (task_id,))
                        conn.commit()
                
                return True
        except Exception as e:
            print(f"Error deleting task {task_id}: {e}")
            return False
    
    @cache_database_query("get_kanban_tasks", ttl=60) if CACHE_AVAILABLE else lambda f: f
    def get_kanban_tasks(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get tasks optimized for Kanban board display (grouped by status)."""
        try:
            with self.get_connection("framework") as conn:
                query = """
                    SELECT t.id, t.epic_id, t.title, t.description, t.status,
                           t.estimate_minutes, t.tdd_phase, t.priority,
                           t.created_at, t.updated_at, t.completed_at,
                           e.name as epic_name, e.epic_key
                    FROM framework_tasks t
                    LEFT JOIN framework_epics e ON t.epic_id = e.id
                    WHERE t.deleted_at IS NULL
                    ORDER BY t.status ASC, t.priority ASC, t.created_at DESC
                """
                
                if SQLALCHEMY_AVAILABLE:
                    result = conn.execute(text(query))
                    tasks = [dict(row._mapping) for row in result]
                else:
                    cursor = conn.cursor()
                    cursor.execute(query)
                    tasks = [dict(zip([col[0] for col in cursor.description], row)) 
                           for row in cursor.fetchall()]
                
                # Group by status for Kanban display
                grouped = {"todo": [], "in_progress": [], "completed": []}
                for task in tasks:
                    status = task.get("status", "todo")
                    if status in grouped:
                        grouped[status].append(task)
                    else:
                        grouped["todo"].append(task)  # Default fallback
                
                return grouped
                
        except Exception as e:
            print(f"Error loading kanban tasks: {e}")
            return {"todo": [], "in_progress": [], "completed": []}
    
    def get_task_statistics(self) -> Dict[str, int]:
        """Get quick statistics for tasks (used by dashboard widgets)."""
        try:
            with self.get_connection("framework") as conn:
                if SQLALCHEMY_AVAILABLE:
                    result = conn.execute(text("""
                        SELECT status, COUNT(*) as count
                        FROM framework_tasks
                        WHERE deleted_at IS NULL
                        GROUP BY status
                    """))
                    
                    stats = {"todo": 0, "in_progress": 0, "completed": 0, "total": 0}
                    total = 0
                    for row in result:
                        status = row[0] or "todo"
                        count = row[1]
                        if status in stats:
                            stats[status] = count
                        total += count
                    stats["total"] = total
                    
                    return stats
                else:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT status, COUNT(*) as count
                        FROM framework_tasks
                        WHERE deleted_at IS NULL
                        GROUP BY status
                    """)
                    
                    stats = {"todo": 0, "in_progress": 0, "completed": 0, "total": 0}
                    total = 0
                    for row in cursor.fetchall():
                        status = row[0] or "todo"
                        count = row[1]
                        if status in stats:
                            stats[status] = count
                        total += count
                    stats["total"] = total
                    
                    return stats
                    
        except Exception as e:
            print(f"Error getting task statistics: {e}")
            return {"todo": 0, "in_progress": 0, "completed": 0, "total": 0}
    
    # ==================================================================================
    # DURATION SYSTEM EXTENSION METHODS (FASE 2.3)
    # ==================================================================================
    
    @cache_database_query("calculate_epic_duration", ttl=300) if CACHE_AVAILABLE else lambda f: f
    def calculate_epic_duration(self, epic_id: int) -> float:
        """Calculate total duration for an epic based on task dates.
        
        Args:
            epic_id: ID of the epic to calculate duration for
            
        Returns:
            Duration in days (float), or 0.0 if calculation fails
        """
        if not DURATION_SYSTEM_AVAILABLE:
            logger.warning("Duration system not available - install duration_system package")
            return 0.0
        
        try:
            with self.get_connection("framework") as conn:
                # Get epic with date fields
                if SQLALCHEMY_AVAILABLE:
                    result = conn.execute(text("""
                        SELECT planned_start_date, planned_end_date, 
                               actual_start_date, actual_end_date,
                               calculated_duration_days
                        FROM framework_epics 
                        WHERE id = :epic_id AND deleted_at IS NULL
                    """), {"epic_id": epic_id})
                    epic_row = result.fetchone()
                else:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT planned_start_date, planned_end_date,
                               actual_start_date, actual_end_date,
                               calculated_duration_days
                        FROM framework_epics 
                        WHERE id = ? AND deleted_at IS NULL
                    """, (epic_id,))
                    epic_row = cursor.fetchone()
                
                if not epic_row:
                    return 0.0
                
                calculator = DurationCalculator()
                
                # Try to use existing calculated duration first
                if epic_row[4] is not None:  # calculated_duration_days
                    return float(epic_row[4])
                
                # Calculate from actual dates if available
                if epic_row[2] and epic_row[3]:  # actual_start_date, actual_end_date
                    return calculator.calculate_duration_days(epic_row[2], epic_row[3])
                
                # Fall back to planned dates
                if epic_row[0] and epic_row[1]:  # planned_start_date, planned_end_date
                    return calculator.calculate_duration_days(epic_row[0], epic_row[1])
                
                # If no dates available, sum task durations
                return self._calculate_epic_duration_from_tasks(epic_id)
                
        except Exception as e:
            logger.error("Error calculating epic duration for %s: %s", epic_id, e)
            return 0.0
    
    @invalidate_cache_on_change("db_query:get_epics:", "db_query:calculate_epic_duration:") if CACHE_AVAILABLE else lambda f: f
    def update_duration_description(self, epic_id: int, description: str) -> bool:
        """Update the duration description for an epic.
        
        Args:
            epic_id: ID of the epic to update
            description: New duration description (e.g., "1.5 dias", "1 semana")
            
        Returns:
            True if successful, False otherwise
        """
        if not DURATION_SYSTEM_AVAILABLE:
            logger.warning("Duration system not available")
            return False
        
        try:
            # Parse and validate duration description
            calculator = DurationCalculator()
            duration_days = calculator.parse_and_convert_to_days(description)

            with self.get_connection("framework") as conn:
                try:
                    if SQLALCHEMY_AVAILABLE:
                        conn.execute(text("""
                            UPDATE framework_epics
                            SET duration_description = :description,
                                calculated_duration_days = :duration_days,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE id = :epic_id
                        """), {
                            "description": description,
                            "duration_days": duration_days,
                            "epic_id": epic_id
                        })
                        conn.commit()
                    else:
                        cursor = conn.cursor()
                        cursor.execute("""
                            UPDATE framework_epics
                            SET duration_description = ?, calculated_duration_days = ?,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE id = ?
                        """, (description, duration_days, epic_id))
                        conn.commit()
                except Exception:
                    conn.rollback()
                    raise

            return True

        except Exception as e:
            logger.error("Error updating duration description for epic %s: %s", epic_id, e)
            return False
    
    @cache_database_query("get_epic_timeline", ttl=180) if CACHE_AVAILABLE else lambda f: f
    def get_epic_timeline(self, epic_id: int) -> Dict[str, Any]:
        """Get comprehensive timeline information for an epic.
        
        Args:
            epic_id: ID of the epic to get timeline for
            
        Returns:
            Dictionary with timeline data including dates, durations, and validation
        """
        if not DURATION_SYSTEM_AVAILABLE:
            return {"error": "Duration system not available"}
        
        try:
            with self.get_connection("framework") as conn:
                # Get epic timeline data
                if SQLALCHEMY_AVAILABLE:
                    result = conn.execute(text("""
                        SELECT id, epic_key, name, status,
                               planned_start_date, planned_end_date,
                               actual_start_date, actual_end_date,
                               calculated_duration_days, duration_description,
                               created_at, updated_at, completed_at
                        FROM framework_epics 
                        WHERE id = :epic_id AND deleted_at IS NULL
                    """), {"epic_id": epic_id})
                    epic_data = dict(result.fetchone()._mapping) if result.rowcount > 0 else None
                else:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT id, epic_key, name, status,
                               planned_start_date, planned_end_date,
                               actual_start_date, actual_end_date,
                               calculated_duration_days, duration_description,
                               created_at, updated_at, completed_at
                        FROM framework_epics 
                        WHERE id = ? AND deleted_at IS NULL
                    """, (epic_id,))
                    row = cursor.fetchone()
                    if row:
                        epic_data = dict(zip([col[0] for col in cursor.description], row))
                    else:
                        epic_data = None
                
                if not epic_data:
                    return {"error": f"Epic {epic_id} not found"}
                
                calculator = DurationCalculator()
                formatter = DurationFormatter()
                
                # Calculate durations and validate consistency
                validation = calculator.validate_date_consistency(
                    planned_start=epic_data.get('planned_start_date'),
                    planned_end=epic_data.get('planned_end_date'),
                    actual_start=epic_data.get('actual_start_date'),
                    actual_end=epic_data.get('actual_end_date'),
                    duration_days=epic_data.get('calculated_duration_days')
                )
                
                # Format duration descriptions
                timeline_data = {
                    "epic": epic_data,
                    "validation": validation,
                    "duration_info": {
                        "calculated_days": epic_data.get('calculated_duration_days', 0),
                        "description": epic_data.get('duration_description', ''),
                        "formatted": formatter.format(epic_data.get('calculated_duration_days', 0)) if epic_data.get('calculated_duration_days') else '',
                    },
                    "dates": {
                        "planned_start": epic_data.get('planned_start_date'),
                        "planned_end": epic_data.get('planned_end_date'),
                        "actual_start": epic_data.get('actual_start_date'),
                        "actual_end": epic_data.get('actual_end_date'),
                    },
                    "status_info": {
                        "status": epic_data.get('status', 'unknown'),
                        "is_completed": epic_data.get('status') == 'completed',
                        "completion_date": epic_data.get('completed_at'),
                    }
                }
                
                # Add task timeline if needed
                timeline_data["tasks"] = self._get_epic_task_timeline(epic_id)
                
                return timeline_data
                
        except Exception as e:
            print(f"Error getting epic timeline for {epic_id}: {e}")
            return {"error": str(e)}
    
    def validate_date_consistency(self, epic_id: int) -> bool:
        """Validate date consistency for an epic.
        
        Args:
            epic_id: ID of the epic to validate
            
        Returns:
            True if dates are consistent, False otherwise
        """
        if not DURATION_SYSTEM_AVAILABLE:
            return False
        
        try:
            with self.get_connection("framework") as conn:
                if SQLALCHEMY_AVAILABLE:
                    result = conn.execute(text("""
                        SELECT planned_start_date, planned_end_date,
                               actual_start_date, actual_end_date,
                               calculated_duration_days
                        FROM framework_epics 
                        WHERE id = :epic_id AND deleted_at IS NULL
                    """), {"epic_id": epic_id})
                    row = result.fetchone()
                else:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT planned_start_date, planned_end_date,
                               actual_start_date, actual_end_date,
                               calculated_duration_days
                        FROM framework_epics 
                        WHERE id = ? AND deleted_at IS NULL
                    """, (epic_id,))
                    row = cursor.fetchone()
                
                if not row:
                    return False
                
                calculator = DurationCalculator()
                validation = calculator.validate_date_consistency(
                    planned_start=row[0],
                    planned_end=row[1],
                    actual_start=row[2],
                    actual_end=row[3],
                    duration_days=row[4]
                )
                
                return validation["is_valid"]
                
        except Exception as e:
            print(f"Error validating date consistency for epic {epic_id}: {e}")
            return False
    
    # Helper methods for duration system
    
    def _calculate_epic_duration_from_tasks(self, epic_id: int) -> float:
        """Calculate epic duration by summing task durations."""
        try:
            with self.get_connection("framework") as conn:
                if SQLALCHEMY_AVAILABLE:
                    result = conn.execute(text("""
                        SELECT SUM(estimate_minutes) 
                        FROM framework_tasks 
                        WHERE epic_id = :epic_id AND deleted_at IS NULL
                    """), {"epic_id": epic_id})
                    total_minutes = result.scalar() or 0
                else:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT SUM(estimate_minutes) 
                        FROM framework_tasks 
                        WHERE epic_id = ? AND deleted_at IS NULL
                    """, (epic_id,))
                    total_minutes = cursor.fetchone()[0] or 0
                
                # Convert minutes to days (8 hours = 1 work day)
                return round(total_minutes / (8 * 60), 2)
                
        except Exception:
            return 0.0
    
    def _get_epic_task_timeline(self, epic_id: int) -> List[Dict[str, Any]]:
        """Get timeline information for tasks within an epic."""
        try:
            with self.get_connection("framework") as conn:
                if SQLALCHEMY_AVAILABLE:
                    result = conn.execute(text("""
                        SELECT id, title, status, tdd_phase, estimate_minutes,
                               created_at, updated_at, completed_at, priority
                        FROM framework_tasks 
                        WHERE epic_id = :epic_id AND deleted_at IS NULL
                        ORDER BY priority ASC, created_at ASC
                    """), {"epic_id": epic_id})
                    return [dict(row._mapping) for row in result]
                else:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT id, title, status, tdd_phase, estimate_minutes,
                               created_at, updated_at, completed_at, priority
                        FROM framework_tasks 
                        WHERE epic_id = ? AND deleted_at IS NULL
                        ORDER BY priority ASC, created_at ASC
                    """, (epic_id,))
                    
                    return [dict(zip([col[0] for col in cursor.description], row)) 
                           for row in cursor.fetchall()]
                           
        except Exception:
            return []