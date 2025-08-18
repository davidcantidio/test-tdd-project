"""
🎛️ Streamlit Sidebar Component

Persistent sidebar with timer controls and navigation.
"""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta

# Graceful imports
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False

try:
    from ..config import get_config
except ImportError:
    get_config = None

# Import database utilities for real data
try:
    from ..utils.database import DatabaseManager
    DATABASE_AVAILABLE = True
except ImportError:
    try:
        from streamlit_extension.utils.database import DatabaseManager
        DATABASE_AVAILABLE = True
    except ImportError:
        DatabaseManager = None
        DATABASE_AVAILABLE = False


def render_sidebar() -> Dict[str, Any]:
    """
    Render the persistent sidebar with timer and navigation.
    
    Returns:
        Dict containing sidebar state and user actions
    """
    if not STREAMLIT_AVAILABLE:
        return {"error": "Streamlit not available"}
    
    sidebar_state = {}
    
    with st.sidebar:
        # Header
        st.markdown("# 🚀 TDD Framework")
        st.markdown("---")
        
        # Timer Section (placeholder for now)
        st.markdown("## ⏱️ Timer")
        
        # Initialize timer state
        if "timer_running" not in st.session_state:
            st.session_state.timer_running = False
            st.session_state.timer_start_time = None
            st.session_state.current_task = None
            st.session_state.elapsed_seconds = 0  # acumulado quando pausado
        
        # Task selection (placeholder)
        current_task = st.selectbox(
            "Current Task",
            ["No task selected", "Task 1", "Task 2", "Task 3"],
            index=0
        )
        
        if current_task != "No task selected":
            st.session_state.current_task = current_task
        
        # Timer controls
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("▶️ Start" if not st.session_state.timer_running else "⏸️ Pause"):
                if not st.session_state.timer_running:
                    st.session_state.timer_running = True
                    # retoma mantendo acumulado; se estava parado, reinicia start
                    st.session_state.timer_start_time = datetime.now()
                else:
                    # pausa: acumula
                    st.session_state.timer_running = False
                    if st.session_state.timer_start_time:
                        st.session_state.elapsed_seconds += int((datetime.now() - st.session_state.timer_start_time).total_seconds())
                        st.session_state.timer_start_time = None
                st.rerun()
        
        with col2:
            if st.button("⏹️ Stop"):
                st.session_state.timer_running = False
                st.session_state.timer_start_time = None
                st.session_state.elapsed_seconds = 0
                st.rerun()
        
        # display considera acumulado + sessão atual
        total_secs = st.session_state.elapsed_seconds
        if st.session_state.timer_running and st.session_state.timer_start_time:
            total_secs += int((datetime.now() - st.session_state.timer_start_time).total_seconds())
        minutes, seconds = total_secs // 60, total_secs % 60
        st.markdown(f"### ⏰ {minutes:02d}:{seconds:02d}")
        
        sidebar_state["timer_running"] = st.session_state.timer_running
        sidebar_state["current_task"] = st.session_state.current_task
        sidebar_state["elapsed_seconds"] = st.session_state.elapsed_seconds
        
        st.markdown("---")
        
        # Epic Progress Section (placeholder)
        st.markdown("## 📊 Current Epic")
        
        # Progress bar (placeholder)
        progress_value = 0.65  # 65% completion
        st.progress(progress_value)
        st.markdown(f"**Progress:** {int(progress_value * 100)}%")
        
        # Stats
        st.markdown("### 📈 Today's Stats")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Tasks Done", "3", "1")
        with col2:
            st.metric("Focus Time", "2.5h", "0.5h")
        
        st.markdown("---")
        
        # Gamification Section (real data)
        cfg = get_config() if get_config else None
        if cfg and getattr(cfg, "enable_gamification", False):
            st.markdown("## 🏆 Achievements")
            
            # Get real gamification data
            gamification_data = _get_gamification_data()
            
            # Points display
            total_points = gamification_data.get("total_points", 0)
            recent_points = gamification_data.get("recent_points", 0)
            st.metric("🌟 Total Points", f"{total_points:,}", f"+{recent_points}" if recent_points > 0 else None)
            
            # Streak
            current_streak = gamification_data.get("current_streak", 0)
            streak_type = gamification_data.get("streak_type", "daily focus")
            st.metric("🔥 Current Streak", f"{current_streak} days", f"{streak_type}")
            
            # Recent achievements
            achievements = gamification_data.get("recent_achievements", [])
            if achievements:
                st.markdown("### 🏅 Recent Badges")
                for achievement in achievements[:3]:  # Show last 3
                    badge_emoji = _get_achievement_emoji(achievement.get("code", ""))
                    st.markdown(f"{badge_emoji} **{achievement.get('name', 'Achievement')}** - {achievement.get('description', '')}")
            else:
                st.markdown("### 🏅 Keep working to unlock badges!")
            
            # Progress to next achievement
            next_achievement = _get_next_achievement_progress(gamification_data)
            if next_achievement:
                st.markdown("### 🎯 Next Goal")
                progress_pct = next_achievement.get("progress", 0) / 100
                st.progress(progress_pct)
                st.markdown(f"**{next_achievement.get('name', 'Next Achievement')}**")
                st.markdown(f"{next_achievement.get('progress', 0)}/{next_achievement.get('target', 100)} - {next_achievement.get('description', '')}")
            
            st.markdown("---")
        
        # Settings quick access
        st.markdown("## ⚙️ Quick Settings")
        
        # Theme toggle (placeholder)
        if st.button("🌙 Toggle Theme"):
            # This would toggle theme in actual implementation
            st.info("Theme toggle coming soon!")
        
        # GitHub sync status
        st.markdown("### 🐙 GitHub Sync")
        if cfg and hasattr(cfg, "is_github_configured") and cfg.is_github_configured():
            st.success("✅ Connected")
            if st.button("🔄 Sync Now"):
                st.info("Sync functionality coming in Task 1.2.8")
        else:
            st.warning("⚠️ Not configured")

        sidebar_state["github_configured"] = bool(cfg and hasattr(cfg, "is_github_configured") and cfg.is_github_configured())
        
        st.markdown("---")
        
        # Footer
        st.markdown("### 🤖 Framework Info")
        st.markdown("**Version:** 1.0.0")
        st.markdown("**Phase:** 1.2 Development")
    
    return sidebar_state


def render_timer_controls() -> Dict[str, Any]:
    """
    Render just the timer controls (for embedding in other components).
    
    Returns:
        Dict containing timer state
    """
    if not STREAMLIT_AVAILABLE:
        return {"error": "Streamlit not available"}
    
    # This would be a more focused timer component
    # Implementation would be similar to the sidebar version
    # but optimized for embedding in other pages
    
    return {
        "timer_running": False,
        "elapsed_time": "00:00",
        "current_task": None
    }


def _get_gamification_data() -> Dict[str, Any]:
    """Get real gamification data from database."""
    if not DATABASE_AVAILABLE:
        return _get_fallback_gamification_data()
    
    try:
        db_manager = DatabaseManager()
        
        # Get user stats (points, completed tasks)
        user_stats = db_manager.get_user_stats()
        
        # Get achievements
        achievements = db_manager.get_achievements()
        
        # Get timer sessions for streak calculation
        timer_sessions = db_manager.get_timer_sessions(days=30)
        
        # Calculate streaks
        current_streak, streak_type = _calculate_streaks(timer_sessions)
        
        # Calculate recent points (last 7 days)
        recent_points = _calculate_recent_points(timer_sessions, achievements)
        
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
        print(f"Error loading gamification data: {e}")
        return _get_fallback_gamification_data()


def _get_fallback_gamification_data() -> Dict[str, Any]:
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


def _calculate_streaks(timer_sessions: list) -> tuple[int, str]:
    """Calculate current streak from timer sessions."""
    if not timer_sessions:
        return 0, "daily focus"
    
    # Group sessions by date
    from collections import defaultdict
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
    today = datetime.now().strftime("%Y-%m-%d")
    
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


def _calculate_recent_points(timer_sessions: list, achievements: list) -> int:
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


def _get_achievement_emoji(achievement_code: str) -> str:
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


def _get_next_achievement_progress(gamification_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
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
