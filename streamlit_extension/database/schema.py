from __future__ import annotations

import threading
import logging
from typing import Optional, Protocol, runtime_checkable

# Modular imports for schema management
from .connection import get_connection_context

logger = logging.getLogger(__name__)

# Removed legacy DatabaseManager dependencies


@runtime_checkable
class _SchemaCreator(Protocol):
    def create_schema_if_needed(self, *, verbose: bool = False) -> None: ...


def set_database_manager(dbm: Optional[Any]) -> None:
    """
    Legacy compatibility function - no longer needed with modular architecture.
    
    Args:
        dbm: Ignored in modular architecture.
    """
    logger.debug("set_database_manager called - no-op in modular architecture")


def get_database_manager() -> Any:
    """Legacy compatibility function - returns None in modular architecture."""
    logger.warning("get_database_manager is deprecated - use modular schema functions instead")
    return None


# Removed database_singleton dependency - using direct modular implementation


def create_schema_if_needed(verbose: bool = False) -> None:
    """
    Cria o schema do banco usando implementação direta modular.
    """
    try:
        with get_connection_context() as conn:
            if verbose:
                logger.info("Creating/upgrading schema via modular direct implementation...")
            
            # Enable foreign keys
            conn.execute("PRAGMA foreign_keys = ON")
            
            # Create core framework tables
            _create_framework_tables(conn, verbose)
            
            # Create gamification tables 
            _create_gamification_tables(conn, verbose)
            
            # Create work session tables
            _create_work_session_tables(conn, verbose)
            
            # Create system tables
            _create_system_tables(conn, verbose)
            
            # Create indexes for performance
            _create_indexes(conn, verbose)
            
            conn.commit()
            
            if verbose:
                logger.info("Schema created/verified successfully via modular implementation.")
                
    except Exception as e:
        logger.error(f"Schema creation failed: {e}", exc_info=verbose)
        raise RuntimeError(f"Failed to create database schema: {e}") from e


def _create_framework_tables(conn: Any, verbose: bool = False) -> None:
    """Create core framework tables (projects, epics, tasks)."""
    
    # Framework projects table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS framework_projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_key TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Framework epics table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS framework_epics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            epic_key TEXT UNIQUE NOT NULL,
            project_id INTEGER,
            name TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'active',
            priority INTEGER DEFAULT 5,
            duration_days INTEGER,
            progress REAL DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES framework_projects (id) ON DELETE CASCADE
        )
    """)
    
    # Framework tasks table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS framework_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_key TEXT UNIQUE NOT NULL,
            epic_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            tdd_phase TEXT DEFAULT 'Red',
            status TEXT DEFAULT 'active',
            estimate_minutes INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (epic_id) REFERENCES framework_epics (id) ON DELETE CASCADE
        )
    """)
    
    if verbose:
        logger.info("Created framework tables (projects, epics, tasks)")


def _create_gamification_tables(conn: Any, verbose: bool = False) -> None:
    """Create gamification tables (achievements, streaks)."""
    
    # Achievement types
    conn.execute("""
        CREATE TABLE IF NOT EXISTS achievement_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            icon TEXT,
            points INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # User achievements
    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL DEFAULT 1,
            achievement_type_id INTEGER NOT NULL,
            earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (achievement_type_id) REFERENCES achievement_types (id) ON DELETE CASCADE
        )
    """)
    
    # User streaks
    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_streaks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL DEFAULT 1,
            streak_type TEXT NOT NULL,
            current_count INTEGER DEFAULT 0,
            best_count INTEGER DEFAULT 0,
            last_activity_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    if verbose:
        logger.info("Created gamification tables (achievements, streaks)")


def _create_work_session_tables(conn: Any, verbose: bool = False) -> None:
    """Create work session tables for TDD and time tracking."""
    
    # Work sessions
    conn.execute("""
        CREATE TABLE IF NOT EXISTS work_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            end_time TIMESTAMP,
            duration_minutes INTEGER,
            session_type TEXT DEFAULT 'work',
            focus_score REAL,
            interruption_count INTEGER DEFAULT 0,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (task_id) REFERENCES framework_tasks (id) ON DELETE CASCADE
        )
    """)
    
    if verbose:
        logger.info("Created work session tables")


def _create_system_tables(conn: Any, verbose: bool = False) -> None:
    """Create system and configuration tables."""
    
    # System settings
    conn.execute("""
        CREATE TABLE IF NOT EXISTS system_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # GitHub sync log
    conn.execute("""
        CREATE TABLE IF NOT EXISTS github_sync_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sync_type TEXT NOT NULL,
            status TEXT NOT NULL,
            message TEXT,
            sync_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    if verbose:
        logger.info("Created system tables")


def _create_indexes(conn: Any, verbose: bool = False) -> None:
    """Create indexes for better performance."""
    
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_epics_project_id ON framework_epics (project_id)",
        "CREATE INDEX IF NOT EXISTS idx_tasks_epic_id ON framework_tasks (epic_id)", 
        "CREATE INDEX IF NOT EXISTS idx_tasks_status ON framework_tasks (status)",
        "CREATE INDEX IF NOT EXISTS idx_tasks_tdd_phase ON framework_tasks (tdd_phase)",
        "CREATE INDEX IF NOT EXISTS idx_work_sessions_task_id ON work_sessions (task_id)",
        "CREATE INDEX IF NOT EXISTS idx_work_sessions_start_time ON work_sessions (start_time)",
        "CREATE INDEX IF NOT EXISTS idx_user_achievements_user_id ON user_achievements (user_id)",
        "CREATE INDEX IF NOT EXISTS idx_user_streaks_user_id ON user_streaks (user_id)"
    ]
    
    for index_sql in indexes:
        try:
            conn.execute(index_sql)
        except Exception as e:
            if verbose:
                logger.warning(f"Failed to create index: {e}")
    
    if verbose:
        logger.info("Created performance indexes")