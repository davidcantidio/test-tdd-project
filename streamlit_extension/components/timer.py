"""
⏱️ Timer Component for TDD Framework

Advanced timer with TDAH-optimized features:
- Pomodoro-style sessions
- Focus tracking
- Break reminders
- Integration with task database
"""

from typing import Optional, Dict, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass

# Graceful imports
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False

# Import database utilities
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


@dataclass
class TimerSession:
    """Represents a timer session."""
    task_id: Optional[str]
    started_at: datetime
    duration_minutes: int
    session_type: str  # 'focus', 'short_break', 'long_break'
    is_active: bool = True
    ended_at: Optional[datetime] = None
    focus_rating: Optional[int] = None  # 1-10
    interruptions: int = 0
    actual_duration_minutes: Optional[int] = None
    notes: Optional[str] = None


class TimerComponent:
    """Advanced timer component with TDAH features."""
    
    def __init__(self):
        self.session_key = "timer_session"
        self.config_key = "timer_config"
        
        # Initialize session state
        if not STREAMLIT_AVAILABLE:
            return
            
        if self.session_key not in st.session_state:
            st.session_state[self.session_key] = None

        if self.config_key not in st.session_state:
            st.session_state[self.config_key] = {
                "focus_duration": 25,
                "short_break_duration": 5,
                "long_break_duration": 15,
                "sessions_until_long_break": 4,
                "completed_sessions": 0
            }
        # tempo acumulado em segundos quando pausado
        st.session_state.setdefault("timer_accum_seconds", 0)
    
    def render(self, container=None) -> Dict[str, Any]:
        """
        Render the timer component.
        
        Args:
            container: Streamlit container to render in (optional)
        
        Returns:
            Dict containing timer state and actions
        """
        if not STREAMLIT_AVAILABLE:
            return {"error": "Streamlit not available"}
        
        # Use provided container or create new one
        if container is None:
            container = st.container()
        
        with container:
            return self._render_timer_interface()
    
    def _render_timer_interface(self) -> Dict[str, Any]:
        """Render the main timer interface."""
        current_session = st.session_state[self.session_key]
        config = st.session_state[self.config_key]
        
        # Timer header
        st.markdown("## ⏱️ Focus Timer")
        
        # Session type indicator
        if current_session:
            session_type = current_session.session_type
            type_emoji = {
                'focus': '🎯',
                'short_break': '☕',
                'long_break': '🌿'
            }.get(session_type, '⏱️')
            
            st.markdown(f"### {type_emoji} {session_type.replace('_', ' ').title()}")
        else:
            st.markdown("### 🎯 Focus Session")
        
        # Timer display
        time_display = self._get_time_display(current_session, config)
        
        # Large time display
        st.markdown(f"""
        <div style="text-align: center; font-size: 3rem; font-weight: bold; 
                    color: #FF6B6B; margin: 1rem 0;">
            {time_display}
        </div>
        """, unsafe_allow_html=True)
        
        # Progress bar
        if current_session and current_session.is_active:
            progress = self._calculate_progress(current_session, config)
            st.progress(progress)
        
        # Control buttons
        col1, col2, col3, col4 = st.columns(4)
        
        actions = {}
        
        with col1:
            if current_session and current_session.is_active:
                if st.button("⏸️ Pause", key="pause_timer"):
                    actions["action"] = "pause"
            else:
                if st.button("▶️ Start", key="start_timer"):
                    actions["action"] = "start"
        
        with col2:
            if st.button("⏹️ Stop", key="stop_timer"):
                actions["action"] = "stop"
        
        with col3:
            if st.button("⏭️ Skip", key="skip_timer"):
                actions["action"] = "skip"
        
        with col4:
            if st.button("➕ Add 5min", key="extend_timer"):
                actions["action"] = "extend"
        
        # Session stats
        if config["completed_sessions"] > 0:
            st.markdown("---")
            st.markdown("### 📊 Today's Sessions")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Completed", config["completed_sessions"])
            
            with col2:
                next_break = "Long" if config["completed_sessions"] % config["sessions_until_long_break"] == 0 else "Short"
                st.metric("Next Break", next_break)
            
            with col3:
                total_focus_time = config["completed_sessions"] * config["focus_duration"]
                st.metric("Focus Time", f"{total_focus_time}min")
        
        # Interruption tracking (for TDAH support)
        if current_session and current_session.is_active and current_session.session_type == 'focus':
            st.markdown("---")
            st.markdown("### 🧠 TDAH Support")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("😵 Distraction", key="add_interruption"):
                    current_session.interruptions += 1
                    st.rerun()
            
            with col2:
                st.metric("Interruptions", current_session.interruptions)
        
        # Configuration panel
        with st.expander("⚙️ Timer Settings"):
            new_focus = st.slider(
                "Focus Duration (minutes)",
                min_value=10, max_value=60,
                value=config["focus_duration"],
                step=5
            )
            
            new_short_break = st.slider(
                "Short Break (minutes)", 
                min_value=3, max_value=15,
                value=config["short_break_duration"],
                step=1
            )
            
            new_long_break = st.slider(
                "Long Break (minutes)",
                min_value=10, max_value=30,
                value=config["long_break_duration"],
                step=5
            )
            
            if st.button("💾 Save Settings"):
                config.update({
                    "focus_duration": new_focus,
                    "short_break_duration": new_short_break,
                    "long_break_duration": new_long_break
                })
                st.success("Settings saved!")
                st.rerun()
        
        # Process actions
        if actions.get("action"):
            self._handle_timer_action(actions["action"], current_session, config)
        
        # Return timer state
        return {
            "current_session": current_session,
            "is_active": current_session.is_active if current_session else False,
            "session_type": current_session.session_type if current_session else None,
            "elapsed_minutes": self._get_elapsed_minutes(current_session) if current_session else 0,
            "interruptions": current_session.interruptions if current_session else 0,
            "completed_sessions": config["completed_sessions"]
        }
    
    def _get_time_display(self, session: Optional[TimerSession], config: Dict) -> str:
        """Get formatted time display."""
        if not session:
            return "00:00"
        total_minutes = int(config.get(f"{session.session_type}_duration", 25))
        # segundos já decorridos = acumulado + (agora - started_at se ativo)
        elapsed = st.session_state.get("timer_accum_seconds", 0)
        if session.is_active and session.started_at:
            elapsed += int((datetime.now() - session.started_at).total_seconds())
        remain = max(0, total_minutes * 60 - elapsed)
        mm, ss = remain // 60, remain % 60
        return f"{mm:02d}:{ss:02d}"
    
    def _calculate_progress(self, session: TimerSession, config: Dict) -> float:
        """Calculate session progress (0.0 to 1.0)."""
        if not session or not session.is_active:
            return 0.0
        
        elapsed = datetime.now() - session.started_at
        elapsed_minutes = elapsed.total_seconds() / 60
        
        total_minutes = config.get(f"{session.session_type}_duration", 25)
        
        return min(1.0, elapsed_minutes / total_minutes)
    
    def _get_elapsed_minutes(self, session: Optional[TimerSession]) -> int:
        """Get elapsed minutes for current session."""
        if not session:
            return 0
        
        if session.ended_at:
            elapsed = session.ended_at - session.started_at
        else:
            elapsed = datetime.now() - session.started_at
        
        return int(elapsed.total_seconds() / 60)
    
    def _handle_timer_action(self, action: str, current_session: Optional[TimerSession], config: Dict):
        """Handle timer actions."""
        if action == "start":
            if current_session and current_session.is_active:
                return  # Already running
            
            # Determine session type
            completed = config["completed_sessions"]
            if completed > 0 and completed % config["sessions_until_long_break"] == 0:
                session_type = "long_break"
            elif completed > 0:
                session_type = "short_break" 
            else:
                session_type = "focus"
            
            # Create new session
            new_session = TimerSession(
                task_id=None,  # TODO: Get from current task selection
                started_at=datetime.now(),
                duration_minutes=config[f"{session_type}_duration"],
                session_type=session_type,
                is_active=True
            )
            
            st.session_state[self.session_key] = new_session
            st.rerun()
        
        elif action == "pause":
            if current_session and current_session.is_active:
                # acumula ao pausar
                st.session_state["timer_accum_seconds"] += int((datetime.now() - current_session.started_at).total_seconds())
                current_session.is_active = False
        
        elif action == "stop":
            if current_session:
                self._end_session(current_session, config)
                st.session_state[self.session_key] = None
                st.session_state["timer_accum_seconds"] = 0
                st.rerun()
        
        elif action == "skip":
            if current_session:
                self._end_session(current_session, config)
                st.session_state[self.session_key] = None
                st.session_state["timer_accum_seconds"] = 0
                st.rerun()
        
        elif action == "extend":
            if current_session and current_session.is_active:
                # Add 5 minutes to duration (by adjusting start time)
                current_session.started_at -= timedelta(minutes=5)
    
    def _end_session(self, session: TimerSession, config: Dict):
        """End a timer session and update stats."""
        session.is_active = False
        session.ended_at = datetime.now()
        # soma acumulado + trecho final
        acc = st.session_state.get("timer_accum_seconds", 0)
        if session.started_at and session.ended_at:
            acc += int((session.ended_at - session.started_at).total_seconds())
        # Calculate actual duration
        if acc:
            actual_duration = acc / 60
            session.actual_duration_minutes = int(actual_duration)
        st.session_state["timer_accum_seconds"] = 0
        
        # Update completed sessions count
        if session.session_type == "focus":
            config["completed_sessions"] += 1
        
        # Save session to database
        self._save_session_to_database(session)
    
    def _save_session_to_database(self, session: TimerSession):
        """Save timer session to database."""
        if not DATABASE_AVAILABLE or not session.ended_at:
            return False
        
        try:
            db_manager = DatabaseManager()
            
            # Only save focus sessions to database (breaks are just UI state)
            if session.session_type == "focus":
                success = db_manager.create_timer_session(
                    task_id=int(session.task_id) if session.task_id and session.task_id.isdigit() else None,
                    duration_minutes=session.duration_minutes,
                    focus_rating=session.focus_rating,
                    interruptions=session.interruptions,
                    actual_duration_minutes=session.actual_duration_minutes,
                    ended_at=session.ended_at.isoformat() if session.ended_at else None,
                    notes=session.notes
                )
                
                if success and STREAMLIT_AVAILABLE:
                    actual_min = session.actual_duration_minutes or session.duration_minutes
                    interruption_text = f", {session.interruptions} interruptions" if session.interruptions > 0 else ""
                    st.success(f"✅ Timer session saved ({actual_min}min{interruption_text})")
                    
                return success
        except Exception as e:
            if STREAMLIT_AVAILABLE:
                st.warning(f"⚠️ Could not save timer session: {str(e)}")
            return False
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of current timer session."""
        if not STREAMLIT_AVAILABLE:
            return {}
        
        current_session = st.session_state.get(self.session_key)
        config = st.session_state.get(self.config_key, {})
        
        return {
            "has_active_session": current_session is not None and current_session.is_active,
            "session_type": current_session.session_type if current_session else None,
            "elapsed_minutes": self._get_elapsed_minutes(current_session),
            "interruptions_today": current_session.interruptions if current_session else 0,
            "completed_sessions_today": config.get("completed_sessions", 0)
        }