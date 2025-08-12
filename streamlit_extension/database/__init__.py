"""
🗄️ Database Package for Streamlit Extension

Provides database models and utilities for the TDD Framework Streamlit extension.
Integrates with existing framework.db and task_timer.db while maintaining compatibility.
"""

try:
    from .models import (
        FrameworkEpic, FrameworkTask, TimerSession,
        UserAchievement, UserStreak, EpicProgress, TimerStats,
        create_database_engine, create_session, initialize_database
    )
    MODELS_AVAILABLE = True
except ImportError:
    MODELS_AVAILABLE = False
    FrameworkEpic = FrameworkTask = TimerSession = None
    UserAchievement = UserStreak = EpicProgress = TimerStats = None
    create_database_engine = create_session = initialize_database = None

__version__ = "1.0.0"
__all__ = [
    "FrameworkEpic", "FrameworkTask", "TimerSession",
    "UserAchievement", "UserStreak", "EpicProgress", "TimerStats",
    "create_database_engine", "create_session", "initialize_database",
    "MODELS_AVAILABLE"
]