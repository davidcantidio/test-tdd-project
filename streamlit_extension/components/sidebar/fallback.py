"""
🛡️ Fallback Data Module

Provides fallback gamification data when database is unavailable.
Simple mock data for development and error scenarios.
"""

from typing import Dict, Any
# Auth imports
from streamlit_extension.auth.middleware import require_auth, require_admin
from streamlit_extension.auth.user_model import UserRole


def get_fallback_gamification_data() -> Dict[str, Any]:
    """Fallback gamification data when database unavailable."""
    return {
        "total_points": 125,
        "recent_points": 25,
        "current_streak": 3,
        "streak_type": "daily focus",
        "recent_achievements": [
            {"code": "FIRST_EPIC_COMPLETE", "name": "Epic Starter", "description": "Completed first epic"},
            {"code": "FOCUS_WARRIOR", "name": "Focus Warrior", "description": "25min focused session"}
        ],
        "completed_tasks": 8,
        "active_streaks": 2
    }