"""
⭐ Points Calculation Module

Handles calculation of recent points from timer sessions and achievements.
Provides scoring system for gamification features.
"""

from typing import List, Dict, Any
from datetime import datetime, timedelta

# Graceful config import
try:
    from ...config import get_config
except ImportError:
    get_config = None


def calculate_recent_points(timer_sessions: List[Dict[str, Any]], achievements: List[Dict[str, Any]]) -> int:
    """Calculate points earned in last 7 days."""
    recent_points = 0
    cutoff_date = (datetime.now() - timedelta(days=7)).isoformat()
    
    # Points from timer sessions (focus time)
    config = get_config() if get_config else None
    points_per_tdd = config.points_per_tdd_cycle if config else 5
    
    for session in timer_sessions:
        if session.get("started_at", "") >= cutoff_date:
            # 1 point per 5 minutes of focus time
            focus_minutes = session.get("planned_duration_minutes", 0)
            recent_points += max(1, focus_minutes // 5)
    
    # Points from recent achievements
    for achievement in achievements:
        if achievement.get("unlocked_at", "") >= cutoff_date:
            # Default achievement points
            recent_points += 10
    
    return recent_points