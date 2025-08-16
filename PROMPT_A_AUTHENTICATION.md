# 🤖 PROMPT A - AUTHENTICATION SYSTEM

**TASK**: Implementar sistema completo de autenticação para Streamlit  
**ARQUIVOS**: `streamlit_extension/auth/` (ISOLADO - sem interseção com outros prompts)  
**PRIORITY**: P0 - CRITICAL (bloqueador de produção no report.md)  
**CONTEXT**: Sistema de autenticação inexistente, exposição total de dados

---

## 📋 **ARQUIVOS A CRIAR:**

### 1. `streamlit_extension/auth/__init__.py`
```python
"""Authentication package for Streamlit application."""

from .auth_manager import AuthManager, AuthResult
from .session_handler import SessionHandler, SessionData
from .middleware import require_auth, auth_middleware
from .user_model import User, UserRole

__all__ = [
    "AuthManager",
    "AuthResult", 
    "SessionHandler",
    "SessionData",
    "require_auth",
    "auth_middleware",
    "User",
    "UserRole"
]
```

### 2. `streamlit_extension/auth/auth_manager.py`
```python
"""Core authentication management system."""

from __future__ import annotations
import hashlib
import secrets
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import sqlite3

from .user_model import User, UserRole
from .session_handler import SessionHandler, SessionData


@dataclass
class AuthResult:
    """Result of authentication operations."""
    success: bool
    user: Optional[User] = None
    message: str = ""
    session_id: Optional[str] = None


class AuthManager:
    """Manages user authentication, registration, and session lifecycle."""
    
    def __init__(self, db_path: str = "framework.db"):
        self.db_path = db_path
        self.session_handler = SessionHandler()
        self._ensure_auth_tables()
    
    def _ensure_auth_tables(self) -> None:
        """Create authentication tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS auth_users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'user',
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    failed_login_attempts INTEGER DEFAULT 0,
                    locked_until TIMESTAMP NULL
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_auth_users_username ON auth_users(username)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_auth_users_email ON auth_users(email)
            """)
    
    def _hash_password(self, password: str, salt: str) -> str:
        """Hash password with salt using SHA-256."""
        return hashlib.sha256((password + salt).encode()).hexdigest()
    
    def _generate_salt(self) -> str:
        """Generate cryptographically secure salt."""
        return secrets.token_hex(32)
    
    def register_user(self, username: str, email: str, password: str, 
                     role: UserRole = UserRole.USER) -> AuthResult:
        """Register new user with validation."""
        # Input validation
        if len(username) < 3:
            return AuthResult(False, message="Username must be at least 3 characters")
        
        if len(password) < 8:
            return AuthResult(False, message="Password must be at least 8 characters")
        
        if "@" not in email or "." not in email:
            return AuthResult(False, message="Invalid email format")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Check if user exists
                existing = conn.execute(
                    "SELECT id FROM auth_users WHERE username = ? OR email = ?",
                    (username, email)
                ).fetchone()
                
                if existing:
                    return AuthResult(False, message="Username or email already exists")
                
                # Create user
                salt = self._generate_salt()
                password_hash = self._hash_password(password, salt)
                
                cursor = conn.execute("""
                    INSERT INTO auth_users (username, email, password_hash, salt, role)
                    VALUES (?, ?, ?, ?, ?)
                """, (username, email, password_hash, salt, role.value))
                
                user = User(
                    id=cursor.lastrowid,
                    username=username,
                    email=email,
                    role=role,
                    is_active=True,
                    created_at=datetime.now()
                )
                
                return AuthResult(True, user=user, message="User registered successfully")
                
        except Exception as e:
            return AuthResult(False, message=f"Registration failed: {str(e)}")
    
    def authenticate(self, username: str, password: str) -> AuthResult:
        """Authenticate user and create session."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get user data
                row = conn.execute("""
                    SELECT id, username, email, password_hash, salt, role, is_active, 
                           failed_login_attempts, locked_until
                    FROM auth_users WHERE username = ?
                """, (username,)).fetchone()
                
                if not row:
                    return AuthResult(False, message="Invalid credentials")
                
                user_id, username, email, stored_hash, salt, role, is_active, failed_attempts, locked_until = row
                
                # Check if account is locked
                if locked_until and datetime.fromisoformat(locked_until) > datetime.now():
                    return AuthResult(False, message="Account temporarily locked")
                
                # Check if account is active
                if not is_active:
                    return AuthResult(False, message="Account is disabled")
                
                # Verify password
                password_hash = self._hash_password(password, salt)
                if password_hash != stored_hash:
                    # Increment failed attempts
                    failed_attempts += 1
                    lock_time = None
                    if failed_attempts >= 5:
                        lock_time = datetime.now() + timedelta(minutes=15)
                    
                    conn.execute("""
                        UPDATE auth_users 
                        SET failed_login_attempts = ?, locked_until = ?
                        WHERE id = ?
                    """, (failed_attempts, lock_time, user_id))
                    
                    return AuthResult(False, message="Invalid credentials")
                
                # Successful login - reset failed attempts and update last login
                conn.execute("""
                    UPDATE auth_users 
                    SET failed_login_attempts = 0, locked_until = NULL, last_login = ?
                    WHERE id = ?
                """, (datetime.now(), user_id))
                
                # Create user object
                user = User(
                    id=user_id,
                    username=username,
                    email=email,
                    role=UserRole(role),
                    is_active=is_active,
                    last_login=datetime.now()
                )
                
                # Create session
                session_id = self.session_handler.create_session(user)
                
                return AuthResult(True, user=user, session_id=session_id, 
                                message="Login successful")
                
        except Exception as e:
            return AuthResult(False, message=f"Authentication failed: {str(e)}")
    
    def logout(self, session_id: str) -> bool:
        """Logout user and destroy session."""
        return self.session_handler.destroy_session(session_id)
    
    def get_current_user(self, session_id: str) -> Optional[User]:
        """Get current user from session."""
        session_data = self.session_handler.get_session(session_id)
        return session_data.user if session_data else None
    
    def is_authenticated(self, session_id: str) -> bool:
        """Check if session is valid and user is authenticated."""
        return self.session_handler.is_valid_session(session_id)
    
    def change_password(self, user_id: int, old_password: str, new_password: str) -> AuthResult:
        """Change user password with validation."""
        if len(new_password) < 8:
            return AuthResult(False, message="New password must be at least 8 characters")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Verify old password
                row = conn.execute(
                    "SELECT password_hash, salt FROM auth_users WHERE id = ?",
                    (user_id,)
                ).fetchone()
                
                if not row:
                    return AuthResult(False, message="User not found")
                
                stored_hash, salt = row
                old_hash = self._hash_password(old_password, salt)
                
                if old_hash != stored_hash:
                    return AuthResult(False, message="Current password is incorrect")
                
                # Set new password
                new_salt = self._generate_salt()
                new_hash = self._hash_password(new_password, new_salt)
                
                conn.execute("""
                    UPDATE auth_users 
                    SET password_hash = ?, salt = ?
                    WHERE id = ?
                """, (new_hash, new_salt, user_id))
                
                return AuthResult(True, message="Password changed successfully")
                
        except Exception as e:
            return AuthResult(False, message=f"Password change failed: {str(e)}")
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                row = conn.execute("""
                    SELECT id, username, email, role, is_active, created_at, last_login
                    FROM auth_users WHERE id = ?
                """, (user_id,)).fetchone()
                
                if row:
                    return User(
                        id=row[0],
                        username=row[1],
                        email=row[2],
                        role=UserRole(row[3]),
                        is_active=bool(row[4]),
                        created_at=datetime.fromisoformat(row[5]),
                        last_login=datetime.fromisoformat(row[6]) if row[6] else None
                    )
        except Exception:
            pass
        
        return None
```

### 3. `streamlit_extension/auth/session_handler.py`
```python
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
        
        # Update last activity
        session.last_activity = datetime.now()
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
```

### 4. `streamlit_extension/auth/user_model.py`
```python
"""User model and role definitions."""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class UserRole(Enum):
    """User role enumeration."""
    ADMIN = "admin"
    USER = "user"
    READONLY = "readonly"
    
    def __str__(self) -> str:
        return self.value
    
    @property
    def display_name(self) -> str:
        """Get display name for role."""
        return {
            UserRole.ADMIN: "Administrator",
            UserRole.USER: "User", 
            UserRole.READONLY: "Read Only"
        }[self]
    
    def can_edit(self) -> bool:
        """Check if role can edit data."""
        return self in [UserRole.ADMIN, UserRole.USER]
    
    def can_admin(self) -> bool:
        """Check if role has admin privileges."""
        return self == UserRole.ADMIN


@dataclass
class User:
    """User data model."""
    id: int
    username: str
    email: str
    role: UserRole
    is_active: bool = True
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    
    def __post_init__(self):
        """Set defaults after initialization."""
        if self.created_at is None:
            self.created_at = datetime.now()
    
    @property
    def display_name(self) -> str:
        """Get display name (username)."""
        return self.username
    
    @property
    def is_admin(self) -> bool:
        """Check if user is admin."""
        return self.role.can_admin()
    
    @property
    def can_edit(self) -> bool:
        """Check if user can edit data."""
        return self.role.can_edit() and self.is_active
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role.value,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> User:
        """Create from dictionary."""
        return cls(
            id=data["id"],
            username=data["username"],
            email=data["email"],
            role=UserRole(data["role"]),
            is_active=data["is_active"],
            created_at=datetime.fromisoformat(data["created_at"]) if data["created_at"] else None,
            last_login=datetime.fromisoformat(data["last_login"]) if data["last_login"] else None
        )
```

### 5. `streamlit_extension/auth/middleware.py`
```python
"""Authentication middleware and decorators."""

from functools import wraps
from typing import Callable, Optional
import streamlit as st

from .auth_manager import AuthManager
from .user_model import User, UserRole


# Global auth manager instance
_auth_manager: Optional[AuthManager] = None


def get_auth_manager() -> AuthManager:
    """Get global auth manager instance."""
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = AuthManager()
    return _auth_manager


def require_auth(roles: Optional[list[UserRole]] = None):
    """Decorator to require authentication for Streamlit functions."""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Check authentication
            if "session_id" not in st.session_state:
                st.error("🔒 Access denied. Please log in.")
                st.stop()
            
            auth_manager = get_auth_manager()
            user = auth_manager.get_current_user(st.session_state.session_id)
            
            if not user:
                st.error("🔒 Session expired. Please log in again.")
                if "session_id" in st.session_state:
                    del st.session_state.session_id
                st.stop()
            
            # Check role permissions
            if roles and user.role not in roles:
                st.error(f"🔒 Access denied. Required role: {[r.display_name for r in roles]}")
                st.stop()
            
            # Store current user in session state
            st.session_state.current_user = user
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


def require_admin(func: Callable):
    """Decorator to require admin role."""
    return require_auth([UserRole.ADMIN])(func)


def auth_middleware() -> Optional[User]:
    """Middleware to check authentication state."""
    if "session_id" not in st.session_state:
        return None
    
    auth_manager = get_auth_manager()
    user = auth_manager.get_current_user(st.session_state.session_id)
    
    if user:
        st.session_state.current_user = user
        return user
    else:
        # Clean up invalid session
        if "session_id" in st.session_state:
            del st.session_state.session_id
        if "current_user" in st.session_state:
            del st.session_state.current_user
        return None


def get_current_user() -> Optional[User]:
    """Get current authenticated user."""
    return st.session_state.get("current_user")


def is_authenticated() -> bool:
    """Check if current user is authenticated."""
    return get_current_user() is not None


def logout_user():
    """Logout current user."""
    if "session_id" in st.session_state:
        auth_manager = get_auth_manager()
        auth_manager.logout(st.session_state.session_id)
        del st.session_state.session_id
    
    if "current_user" in st.session_state:
        del st.session_state.current_user
    
    st.rerun()
```

### 6. `streamlit_extension/auth/login_page.py`
```python
"""Login and registration page for authentication."""

import streamlit as st
from .auth_manager import AuthManager
from .user_model import UserRole


def render_login_page():
    """Render login/registration page."""
    st.title("🔐 Authentication")
    
    auth_manager = AuthManager()
    
    # Create tabs for login and registration
    login_tab, register_tab = st.tabs(["Login", "Register"])
    
    with login_tab:
        render_login_form(auth_manager)
    
    with register_tab:
        render_registration_form(auth_manager)


def render_login_form(auth_manager: AuthManager):
    """Render login form."""
    st.subheader("Login")
    
    with st.form("login_form"):
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.form_submit_button("Login", type="primary"):
            if username and password:
                result = auth_manager.authenticate(username, password)
                
                if result.success:
                    st.session_state.session_id = result.session_id
                    st.session_state.current_user = result.user
                    st.success(f"Welcome back, {result.user.username}!")
                    st.rerun()
                else:
                    st.error(result.message)
            else:
                st.error("Please enter both username and password.")


def render_registration_form(auth_manager: AuthManager):
    """Render registration form."""
    st.subheader("Register New Account")
    
    with st.form("register_form"):
        username = st.text_input("Username", key="reg_username")
        email = st.text_input("Email", key="reg_email")
        password = st.text_input("Password", type="password", key="reg_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="reg_confirm")
        
        if st.form_submit_button("Register"):
            if not all([username, email, password, confirm_password]):
                st.error("Please fill in all fields.")
            elif password != confirm_password:
                st.error("Passwords do not match.")
            else:
                result = auth_manager.register_user(username, email, password, UserRole.USER)
                
                if result.success:
                    st.success("Registration successful! Please log in.")
                    st.balloons()
                else:
                    st.error(result.message)


def render_user_profile():
    """Render user profile page."""
    if "current_user" not in st.session_state:
        st.error("Please log in to view profile.")
        return
    
    user = st.session_state.current_user
    auth_manager = AuthManager()
    
    st.title("👤 User Profile")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Profile Information")
        st.write(f"**Username:** {user.username}")
        st.write(f"**Email:** {user.email}")
        st.write(f"**Role:** {user.role.display_name}")
        st.write(f"**Account Status:** {'Active' if user.is_active else 'Inactive'}")
        
        if user.created_at:
            st.write(f"**Member Since:** {user.created_at.strftime('%Y-%m-%d')}")
        
        if user.last_login:
            st.write(f"**Last Login:** {user.last_login.strftime('%Y-%m-%d %H:%M')}")
    
    with col2:
        st.subheader("Change Password")
        
        with st.form("change_password_form"):
            old_password = st.text_input("Current Password", type="password")
            new_password = st.text_input("New Password", type="password")
            confirm_new = st.text_input("Confirm New Password", type="password")
            
            if st.form_submit_button("Change Password"):
                if not all([old_password, new_password, confirm_new]):
                    st.error("Please fill in all password fields.")
                elif new_password != confirm_new:
                    st.error("New passwords do not match.")
                else:
                    result = auth_manager.change_password(user.id, old_password, new_password)
                    
                    if result.success:
                        st.success("Password changed successfully!")
                    else:
                        st.error(result.message)
    
    # Logout button
    if st.button("🚪 Logout", type="secondary"):
        if "session_id" in st.session_state:
            auth_manager.logout(st.session_state.session_id)
            del st.session_state.session_id
        
        if "current_user" in st.session_state:
            del st.session_state.current_user
        
        st.success("Logged out successfully!")
        st.rerun()
```

---

## 🔧 **INTEGRATION INSTRUCTIONS:**

### A. Update main `streamlit_app.py`:
```python
# Add to imports at top
from streamlit_extension.auth import auth_middleware, is_authenticated
from streamlit_extension.auth.login_page import render_login_page

# Add authentication check at the beginning of main()
def main():
    # Authentication middleware
    current_user = auth_middleware()
    
    if not is_authenticated():
        render_login_page()
        return
    
    # Rest of existing main() function...
```

### B. Update existing pages to require authentication:
```python
# Add to top of each page file (clients.py, projects.py, etc.)
from streamlit_extension.auth import require_auth

@require_auth()
def render_clients_page():
    # Existing function content...
```

### C. Create admin user on first run:
```python
# Add to main() after auth middleware
if current_user and current_user.is_admin:
    # Show admin functions
    pass
```

---

## ✅ **VERIFICATION CHECKLIST:**

- [ ] All auth files created in `streamlit_extension/auth/`
- [ ] Database tables `auth_users` created automatically
- [ ] Login/registration forms working
- [ ] Session management active
- [ ] Password hashing secure (SHA-256 + salt)
- [ ] Role-based access control implemented
- [ ] Account lockout after failed attempts
- [ ] Session cleanup automatic
- [ ] Integration with existing Streamlit pages
- [ ] Admin user creation process

---

## 🎯 **SUCCESS CRITERIA:**

1. **P0 Critical Issue RESOLVED**: "Missing authentication/authorization across Streamlit pages"
2. **Security Enhancement**: Secure password hashing, session management, role-based access
3. **User Experience**: Clean login/register UI, profile management, logout functionality
4. **Enterprise Ready**: Account lockout, session expiration, admin controls

**RESULTADO ESPERADO**: Sistema de autenticação enterprise-grade completo, eliminando exposição total de dados e habilitando controle de acesso granular por role.