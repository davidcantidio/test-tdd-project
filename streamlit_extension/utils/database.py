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
import json

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
    
    @st.cache_data(ttl=300)  # 5 minute cache
    def get_epics(_self) -> List[Dict[str, Any]]:
        """Get all epics with caching."""
        try:
            with _self.get_connection("framework") as conn:
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
    
    @st.cache_data(ttl=300)
    def get_tasks(_self, epic_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get tasks, optionally filtered by epic."""
        try:
            with _self.get_connection("framework") as conn:
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
    
    @st.cache_data(ttl=180)  # 3 minute cache for timer data
    def get_timer_sessions(_self, days: int = 30) -> List[Dict[str, Any]]:
        """Get recent timer sessions."""
        if not _self.timer_db_path.exists():
            return []
        
        try:
            with _self.get_connection("timer") as conn:
                query = """
                    SELECT task_reference, user_identifier, started_at, ended_at,
                           planned_duration_minutes, actual_duration_minutes,
                           focus_rating, energy_level, mood_rating,
                           interruptions_count, notes,
                           created_at
                    FROM timer_sessions
                    WHERE created_at >= DATE('now', '-{} days')
                    ORDER BY created_at DESC
                    LIMIT 1000
                """.format(days)
                
                if SQLALCHEMY_AVAILABLE:
                    result = conn.execute(text(query))
                    return [dict(row._mapping) for row in result]
                else:
                    cursor = conn.cursor()
                    cursor.execute(query)
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
    
    def update_task_status(self, task_id: int, status: str, tdd_phase: Optional[str] = None) -> bool:
        """Update task status and TDD phase."""
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
    
    def create_timer_session(self, task_id: Optional[int], duration_minutes: int, 
                           focus_rating: Optional[int] = None) -> bool:
        """Create a new timer session record."""
        if not self.timer_db_path.exists():
            return False
        
        try:
            with self.get_connection("timer") as conn:
                if SQLALCHEMY_AVAILABLE:
                    conn.execute(text("""
                        INSERT INTO timer_sessions (
                            task_reference, user_identifier, started_at,
                            planned_duration_minutes, focus_rating, created_at
                        ) VALUES (?, 'user1', CURRENT_TIMESTAMP, ?, ?, CURRENT_TIMESTAMP)
                    """), [str(task_id) if task_id else None, duration_minutes, focus_rating])
                    conn.commit()
                else:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO timer_sessions (
                            task_reference, user_identifier, started_at,
                            planned_duration_minutes, focus_rating, created_at
                        ) VALUES (?, 'user1', CURRENT_TIMESTAMP, ?, ?, CURRENT_TIMESTAMP)
                    """, [str(task_id) if task_id else None, duration_minutes, focus_rating])
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
        except:
            pass
        
        # Test timer DB connection
        if self.timer_db_path.exists():
            try:
                with self.get_connection("timer") as conn:
                    if SQLALCHEMY_AVAILABLE:
                        conn.execute(text("SELECT 1"))
                    else:
                        conn.execute("SELECT 1")
                    health["timer_db_connected"] = True
            except:
                pass
        
        return health