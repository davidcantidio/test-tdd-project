"""
🔥 Streaks Calculation Module

Handles calculation of consecutive daily focus streaks.
Analyzes timer sessions to determine current streak status.
"""

from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
# Auth imports
from streamlit_extension.auth.middleware import require_auth, require_admin
from streamlit_extension.auth.user_model import UserRole


def calculate_streaks(timer_sessions: List[Dict[str, Any]]) -> Tuple[int, str]:
    """Calculate current streak from timer sessions."""
    if not timer_sessions:
        return 0, "daily focus"
    
    # Group sessions by date
    sessions_by_date = defaultdict(list)
    
    for session in timer_sessions:
        if session.get("started_at"):
            try:
                date_str = session["started_at"][:10]  # YYYY-MM-DD
                sessions_by_date[date_str].append(session)
            except (KeyError, IndexError):
                continue
    
    # Calculate consecutive days with focus sessions
    dates = sorted(sessions_by_date.keys(), reverse=True)
    streak_count = 0
    
    for i, date in enumerate(dates):
        expected_date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        
        if date == expected_date:
            # Check if there was meaningful focus time (>= 15 minutes)
            daily_focus = sum(s.get("planned_duration_minutes", 0) for s in sessions_by_date[date])
            if daily_focus >= 15:
                streak_count += 1
            else:
                break
        else:
            break
    
    return streak_count, "daily focus"