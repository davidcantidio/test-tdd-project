"""Session management for authentication."""

from __future__ import annotations
import secrets
import time
from dataclasses import dataclass, field
from typing import Dict, Optional
from datetime import datetime, timedelta

from .user_model import User


@dataclass
class SessionData:
    """Session data container."""
    user: User
    created_at: datetime
    last_activity: datetime
    session_id: str
    expires_at: datetime
    data: Dict = field(default_factory=dict)


class SessionHandler:
    """Manages user sessions with automatic cleanup."""
    
    def __init__(self, session_timeout_hours: int = 24):
        self._sessions: Dict[str, SessionData] = {}
        self.session_timeout = timedelta(hours=session_timeout_hours)
        self._last_cleanup = time.time()
    
    def create_session(self, user: User) -> str:
        """Create new session for user."""
        session_id = secrets.token_urlsafe(32)
        now = datetime.now()
        
        session_data = SessionData(
            user=user,
            created_at=now,
            last_activity=now,
            session_id=session_id,
            expires_at=now + self.session_timeout
        )
        
        self._sessions[session_id] = session_data
        self._cleanup_expired_sessions()
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[SessionData]:
        """Get session data if valid."""
        if session_id not in self._sessions:
            return None
        
        session = self._sessions[session_id]

        # Check if expired
        if datetime.now() > session.expires_at:
            del self._sessions[session_id]
            return None

        # Update last activity and extend expiration
        now = datetime.now()
        session.last_activity = now
        session.expires_at = now + self.session_timeout
        return session
    
    def is_valid_session(self, session_id: str) -> bool:
        """Check if session is valid."""
        return self.get_session(session_id) is not None
    
    def destroy_session(self, session_id: str) -> bool:
        """Destroy session."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False
    
    def extend_session(self, session_id: str, hours: int = 24) -> bool:
        """Extend session expiration."""
        if session_id in self._sessions:
            session = self._sessions[session_id]
            session.expires_at = datetime.now() + timedelta(hours=hours)
            return True
        return False
    
    def get_active_sessions_count(self) -> int:
        """Get count of active sessions."""
        self._cleanup_expired_sessions()
        return len(self._sessions)
    
    def _cleanup_expired_sessions(self) -> None:
        """Clean up expired sessions periodically."""
        current_time = time.time()
        
        # Only cleanup every 5 minutes
        if current_time - self._last_cleanup < 300:
            return
        
        now = datetime.now()
        expired_sessions = [
            session_id for session_id, session in self._sessions.items()
            if now > session.expires_at
        ]
        
        for session_id in expired_sessions:
            del self._sessions[session_id]
        
        self._last_cleanup = current_time
    
    def destroy_all_sessions(self) -> int:
        """Destroy all sessions (admin function)."""
        count = len(self._sessions)
        self._sessions.clear()
        return count
    
    def get_user_sessions(self, user_id: int) -> list[SessionData]:
        """Get all active sessions for a user."""
        return [
            session for session in self._sessions.values()
            if session.user.id == user_id
        ]
    
    def destroy_user_sessions(self, user_id: int) -> int:
        """Destroy all sessions for a specific user."""
        user_sessions = [
            session_id for session_id, session in self._sessions.items()
            if session.user.id == user_id
        ]
        
        for session_id in user_sessions:
            del self._sessions[session_id]
        
        return len(user_sessions)
