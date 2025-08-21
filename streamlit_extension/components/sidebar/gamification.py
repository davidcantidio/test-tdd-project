"""
🏆 Gamification Module

Handles achievements, emoji mapping, and progress calculation.
Provides gamification data processing and next achievement suggestions.
"""

from typing import Dict, Any, List, Optional
from .fallback import get_fallback_gamification_data
from .streaks import calculate_streaks
from .points import calculate_recent_points

# Graceful imports for database
try:
    from ...database.queries import get_user_stats, get_achievements, list_timer_sessions
    DATABASE_AVAILABLE = True
except ImportError:
    try:
        from streamlit_extension.database.queries import get_user_stats, get_achievements, list_timer_sessions
        DATABASE_AVAILABLE = True
    except ImportError:
        get_user_stats = None
        get_achievements = None
        list_timer_sessions = None
        DATABASE_AVAILABLE = False


def get_gamification_data(user_id: int = 1) -> Dict[str, Any]:
    """Get real gamification data from database."""
    if not DATABASE_AVAILABLE:
        return get_fallback_gamification_data()

    try:
        if DATABASE_AVAILABLE:
            # Get user stats (points, completed tasks)
            user_stats = get_user_stats(user_id)
            # Get achievements
            achievements = get_achievements(user_id)
        
        # Get timer sessions for streak calculation
        timer_sessions = list_timer_sessions(days=30) if list_timer_sessions else []
        
        # Calculate streaks
        current_streak, streak_type = calculate_streaks(timer_sessions)
        
        # Calculate recent points (last 7 days)
        recent_points = calculate_recent_points(timer_sessions, achievements)
        
        return {
            "total_points": user_stats.get("total_points", 0),
            "recent_points": recent_points,
            "current_streak": current_streak,
            "streak_type": streak_type,
            "recent_achievements": achievements[:5],  # Last 5 achievements
            "completed_tasks": user_stats.get("completed_tasks", 0),
            "active_streaks": user_stats.get("active_streaks", 0)
        }
        
    except Exception as e:
        logging.info(f"Error loading gamification data: {e}")
        return get_fallback_gamification_data()


def get_achievement_emoji(achievement_code: str) -> str:
    """Get emoji for achievement code."""
    emoji_map = {
        "FIRST_EPIC_COMPLETE": "🏁",
        "TDD_MASTER": "🥷",
        "SPRINT_CHAMPION": "🏃‍♂️",
        "FOCUS_WARRIOR": "🎯",
        "EARLY_BIRD": "🐦",
        "NIGHT_OWL": "🦉",
        "BUG_SQUASHER": "🐛",
        "REFACTOR_EXPERT": "🔨",
        "DOCUMENTATION_HERO": "📚",
        "COLLABORATION_STAR": "⭐"
    }
    return emoji_map.get(achievement_code, "🏅")


def get_next_achievement_progress(gamification_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Calculate progress toward next achievement."""
    completed_tasks = gamification_data.get("completed_tasks", 0)
    current_streak = gamification_data.get("current_streak", 0)
    
    # Define next achievable goals
    next_goals = []
    
    # Task-based achievements
    if completed_tasks < 10:
        next_goals.append({
            "name": "Task Master",
            "description": "Complete 10 tasks",
            "progress": completed_tasks,
            "target": 10,
            "type": "tasks"
        })
    elif completed_tasks < 50:
        next_goals.append({
            "name": "Productivity Expert",
            "description": "Complete 50 tasks",
            "progress": completed_tasks,
            "target": 50,
            "type": "tasks"
        })
    
    # Streak-based achievements
    if current_streak < 7:
        next_goals.append({
            "name": "Week Warrior",
            "description": "Maintain 7-day focus streak",
            "progress": current_streak,
            "target": 7,
            "type": "streak"
        })
    elif current_streak < 30:
        next_goals.append({
            "name": "Month Master",
            "description": "Maintain 30-day focus streak",
            "progress": current_streak,
            "target": 30,
            "type": "streak"
        })
    
    # Return the closest achievement
    if next_goals:
        # Sort by progress percentage
        next_goals.sort(key=lambda x: (x["progress"] / x["target"]), reverse=True)
        return next_goals[0]
    
    return None