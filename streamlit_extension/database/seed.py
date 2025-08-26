from __future__ import annotations

import logging
from typing import Optional, Protocol, runtime_checkable

# Modular imports for data seeding
from .connection import get_connection_context

logger = logging.getLogger(__name__)

# Removed legacy DatabaseManager dependencies


@runtime_checkable
class _DBProto(Protocol):
    def seed_initial_data(self, kind: Optional[str] = None) -> int: ...


def set_database_manager(dbm: Any) -> None:
    """Legacy compatibility function - no longer needed with modular architecture."""
    # This function is kept for API compatibility but does nothing
    pass


# Auth imports removed - using official Streamlit OAuth


def seed_initial_data(kind: Optional[str] = None) -> int:
    """Insere dados de seed usando implementação direta modular."""
    
    try:
        with get_connection_context() as conn:
            records_affected = 0
            
            if kind is None or kind == "achievement_types":
                records_affected += _seed_achievement_types(conn)
            
            if kind is None or kind == "system_settings":
                records_affected += _seed_system_settings(conn)
                
            if kind is None or kind == "default_project":
                records_affected += _seed_default_project(conn)
            
            conn.commit()
            return records_affected
            
    except Exception as e:
        logger.error(f"Seed data insertion failed: {e}", exc_info=True)
        return 0


def _seed_achievement_types(conn: Any) -> int:
    """Seed achievement types for gamification."""
    
    achievement_types = [
        ("TDD_MASTER", "Complete 50 TDD cycles", "🏆", 100),
        ("FOCUS_WARRIOR", "Complete 10 focused work sessions", "🎯", 50),
        ("EARLY_BIRD", "Start work before 8 AM", "🌅", 25),
        ("NIGHT_OWL", "Complete work after 10 PM", "🦉", 25),
        ("STREAK_KEEPER", "Maintain 7-day work streak", "🔥", 75),
        ("TASK_CRUSHER", "Complete 100 tasks", "💪", 150),
        ("EPIC_FINISHER", "Complete an entire epic", "⭐", 200),
        ("TIME_TRACKER", "Log 100 hours of work", "⏱️", 125),
        ("CONSISTENT", "Work 5 days in a row", "📅", 60),
        ("PRODUCTIVE", "Complete 10 tasks in one day", "🚀", 80)
    ]
    
    records_inserted = 0
    for name, description, icon, points in achievement_types:
        try:
            conn.execute("""
                INSERT OR IGNORE INTO achievement_types (name, description, icon, points)
                VALUES (?, ?, ?, ?)
            """, (name, description, icon, points))
            if conn.total_changes > 0:
                records_inserted += 1
        except Exception:
            pass  # Ignore duplicates
    
    return records_inserted


def _seed_system_settings(conn: Any) -> int:
    """Seed system configuration settings."""
    
    settings = [
        ("app_version", "1.0.0", "Current application version"),
        ("tdd_default_phase", "Red", "Default TDD phase for new tasks"),
        ("work_session_default_minutes", "25", "Default pomodoro duration"),
        ("focus_score_threshold", "7", "Minimum focus score for good session"),
        ("gamification_enabled", "true", "Enable achievement system"),
        ("auto_save_interval", "30", "Auto-save interval in seconds"),
        ("theme", "default", "Application theme"),
        ("timezone", "UTC", "Default timezone for timestamps")
    ]
    
    records_inserted = 0
    for key, value, description in settings:
        try:
            conn.execute("""
                INSERT OR IGNORE INTO system_settings (key, value, description)
                VALUES (?, ?, ?)
            """, (key, value, description))
            if conn.total_changes > 0:
                records_inserted += 1
        except Exception:
            pass  # Ignore duplicates
    
    return records_inserted


def _seed_default_project(conn: Any) -> int:
    """Seed a default project with sample data."""
    
    records_inserted = 0
    
    try:
        # Insert default project
        conn.execute("""
            INSERT OR IGNORE INTO framework_projects (project_key, name, description, status)
            VALUES (?, ?, ?, ?)
        """, ("DEMO", "Demo Project", "Default project for getting started", "active"))
        
        if conn.total_changes > 0:
            records_inserted += 1
            
            # Get project ID
            cursor = conn.execute("SELECT id FROM framework_projects WHERE project_key = 'DEMO'")
            project_row = cursor.fetchone()
            
            if project_row:
                project_id = project_row[0]
                
                # Insert default epic
                conn.execute("""
                    INSERT OR IGNORE INTO framework_epics 
                    (epic_key, project_id, name, description, status, priority, duration_days, progress)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, ("DEMO-E1", project_id, "Getting Started Epic", 
                     "Learn the TDD workflow with sample tasks", "active", 1, 7, 0.0))
                
                if conn.total_changes > 0:
                    records_inserted += 1
                    
                    # Get epic ID
                    cursor = conn.execute("SELECT id FROM framework_epics WHERE epic_key = 'DEMO-E1'")
                    epic_row = cursor.fetchone()
                    
                    if epic_row:
                        epic_id = epic_row[0]
                        
                        # Insert sample tasks
                        sample_tasks = [
                            ("DEMO-T1", "Write your first test", "Create a failing test (Red phase)", "Red", 30),
                            ("DEMO-T2", "Make the test pass", "Implement minimum code to pass (Green phase)", "Red", 45),
                            ("DEMO-T3", "Refactor the code", "Clean up and improve the code (Refactor phase)", "Red", 20)
                        ]
                        
                        for task_key, title, description, tdd_phase, estimate in sample_tasks:
                            conn.execute("""
                                INSERT OR IGNORE INTO framework_tasks 
                                (task_key, epic_id, title, description, tdd_phase, status, estimate_minutes)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                            """, (task_key, epic_id, title, description, tdd_phase, "active", estimate))
                            
                            if conn.total_changes > 0:
                                records_inserted += 1
                    
    except Exception as e:
        logger.warning(f"Failed to seed default project: {e}")
    
    return records_inserted