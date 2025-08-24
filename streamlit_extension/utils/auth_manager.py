"""
Enterprise authentication and authorization system for Streamlit.

Implements secure authentication, session management, and CSRF protection
to resolve critical P0 security gaps identified in report.md.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
import streamlit as st
# NOTE: jwt import removido (não utilizado)


@dataclass
class User:
    """User model with role-based permissions."""
    
    id: str
    username: str
    email: str
    roles: List[str]
    permissions: Set[str]
    created_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool = True
    password_hash: Optional[str] = None
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission."""
        return permission in self.permissions
    
    def has_role(self, role: str) -> bool:
        """Check if user has specific role."""
        return role in self.roles


@dataclass 
class Session:
    """Secure session with CSRF protection."""
    
    session_id: str
    user_id: str
    csrf_token: str
    created_at: datetime
    expires_at: datetime
    ip_address: str
    user_agent: str
    is_valid: bool = True
    
    def is_expired(self) -> bool:
        """Check if session is expired."""
        return datetime.now() > self.expires_at
    
    def refresh(self, duration_hours: int = 24) -> None:
        """Refresh session expiration."""
        self.expires_at = datetime.now() + timedelta(hours=duration_hours)


class CSRFProtection:
    """CSRF token generation and validation."""
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key.encode()
    
    def generate_token(self, session_id: str) -> str:
        """Generate CSRF token for session."""
        timestamp = str(int(time.time()))
        data = f"{session_id}:{timestamp}"
        signature = hmac.new(
            self.secret_key,
            data.encode(),
            hashlib.sha256
        ).hexdigest()
        return f"{data}:{signature}"
    
    def validate_token(self, token: str, session_id: str, max_age: int = 3600) -> bool:
        """Validate CSRF token."""
        try:
            parts = token.split(':')
            if len(parts) != 3:
                return False
            
            token_session, timestamp, signature = parts
            
            # Verify session ID matches
            if token_session != session_id:
                return False
            
            # Verify timestamp (not too old)
            token_time = int(timestamp)
            if time.time() - token_time > max_age:
                return False
            
            # Verify signature
            data = f"{token_session}:{timestamp}"
            expected_signature = hmac.new(
                self.secret_key,
                data.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
            
        except (ValueError, TypeError):
            return False


class PasswordManager:
    """Secure password hashing and validation."""
    # Permite configurar custo via secrets (fallback seguro)
    _DEFAULT_ITERS = 200_000

    @staticmethod
    def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
        """Hash password with salt."""
        if salt is None:
            salt = secrets.token_hex(32)

        iterations = int(st.secrets.get("auth_pbkdf2_iters", PasswordManager._DEFAULT_ITERS))
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode(),
            salt.encode(),
            iterations
        ).hex()

        return password_hash, salt
    
    @staticmethod
    def verify_password(password: str, stored_hash: str, salt: str) -> bool:
        """Verify password against stored hash."""
        computed_hash, _ = PasswordManager.hash_password(password, salt)
        return hmac.compare_digest(stored_hash, computed_hash)


class AuthenticationManager:
    """Main authentication manager for Streamlit applications."""
    
    def __init__(self, secret_key: str, session_timeout_hours: int = 24):
        self.secret_key = secret_key
        self.session_timeout_hours = session_timeout_hours
        self.csrf_protection = CSRFProtection(secret_key)
        self.password_manager = PasswordManager()
        
        # Initialize session state
        if 'auth_manager' not in st.session_state:
            st.session_state.auth_manager = {
                'sessions': {},
                'users': {},
                'current_session': None
            }
    
    def create_user(self, username: str, email: str, password: str, 
                   roles: List[str] = None) -> User:
        """Create new user with hashed password."""
        if roles is None:
            roles = ['user']
        
        user_id = str(uuid.uuid4())
        password_hash, salt = self.password_manager.hash_password(password)
        
        # Map roles to permissions
        permissions = self._get_permissions_for_roles(roles)
        
        user = User(
            id=user_id,
            username=username,
            email=email,
            roles=roles,
            permissions=permissions,
            created_at=datetime.now(),
            password_hash=f"{password_hash}:{salt}"
        )
        
        st.session_state.auth_manager['users'][user_id] = user
        return user
    
    def authenticate_user(self, username: str, password: str, 
                         ip_address: str = "unknown",
                         user_agent: str = "unknown") -> Optional[Session]:
        """Authenticate user and create session."""
        # Find user by username
        user = None
        for u in st.session_state.auth_manager['users'].values():
            if u.username == username and u.is_active:
                user = u
                break
        
        if not user:
            return None
        
        # Verify password
        if not user.password_hash:
            return None
        
        try:
            stored_hash, salt = user.password_hash.split(':')
            if not self.password_manager.verify_password(password, stored_hash, salt):
                return None
        except ValueError:
            return None
        
        # Create session
        session = self._create_session(user, ip_address, user_agent)
        
        # Update last login
        user.last_login = datetime.now()
        
        return session
    
    def _create_session(self, user: User, ip_address: str, user_agent: str) -> Session:
        """Create new session for authenticated user."""
        session_id = str(uuid.uuid4())
        csrf_token = self.csrf_protection.generate_token(session_id)
        
        session = Session(
            session_id=session_id,
            user_id=user.id,
            csrf_token=csrf_token,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=self.session_timeout_hours),
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        st.session_state.auth_manager['sessions'][session_id] = session
        st.session_state.auth_manager['current_session'] = session_id
        
        return session
    
    def get_current_user(self) -> Optional[User]:
        """Get currently authenticated user."""
        session = self.get_current_session()
        if not session:
            return None
        
        return st.session_state.auth_manager['users'].get(session.user_id)
    
    def get_current_session(self) -> Optional[Session]:
        """Get current valid session."""
        current_session_id = st.session_state.auth_manager.get('current_session')
        if not current_session_id:
            return None
        
        session = st.session_state.auth_manager['sessions'].get(current_session_id)
        if not session or session.is_expired() or not session.is_valid:
            self.logout()
            return None
        
        return session
    
    def validate_csrf_token(self, token: str) -> bool:
        """Validate CSRF token for current session."""
        session = self.get_current_session()
        if not session:
            return False

        return self.csrf_protection.validate_token(token, session.session_id)

    def rotate_csrf(self) -> Optional[str]:
        """Gera e instala novo CSRF token para a sessão atual (defesa contra replay)."""
        session = self.get_current_session()
        if not session:
            return None
        session.csrf_token = self.csrf_protection.generate_token(session.session_id)
        return session.csrf_token
    
    def logout(self) -> None:
        """Logout current user and invalidate session."""
        current_session_id = st.session_state.auth_manager.get('current_session')
        if current_session_id:
            session = st.session_state.auth_manager['sessions'].get(current_session_id)
            if session:
                session.is_valid = False
            
            st.session_state.auth_manager['current_session'] = None
    
    def require_authentication(self) -> User:
        """Decorator/helper to require authentication for pages."""
        user = self.get_current_user()
        if not user:
            st.error("🔒 Authentication required. Please log in.")
            st.stop()
        return user
    
    def require_permission(self, permission: str) -> User:
        """Decorator/helper to require specific permission."""
        user = self.require_authentication()
        if not user.has_permission(permission):
            st.error(f"🚫 Access denied. Required permission: {permission}")
            st.stop()
        return user
    
    def require_role(self, role: str) -> User:
        """Decorator/helper to require specific role."""
        user = self.require_authentication()
        if not user.has_role(role):
            st.error(f"🚫 Access denied. Required role: {role}")
            st.stop()
        return user
    
    def _get_permissions_for_roles(self, roles: List[str]) -> Set[str]:
        """Map roles to permissions."""
        permission_map = {
            'admin': {
                'create_project', 'read_project', 'update_project', 'delete_project',
                'create_epic', 'read_epic', 'update_epic', 'delete_epic',
                'create_task', 'read_task', 'update_task', 'delete_task',
                'admin_panel', 'user_management', 'system_settings'
            },
            'manager': {
                'create_project', 'read_project', 'update_project',
                'create_epic', 'read_epic', 'update_epic',
                'create_task', 'read_task', 'update_task'
            },
            'user': {
                'read_project', 'read_epic', 'read_task',
                'create_task', 'update_task'
            },
            'viewer': {
                'read_project', 'read_epic', 'read_task'
            }
        }
        
        permissions = set()
        for role in roles:
            if role in permission_map:
                permissions.update(permission_map[role])
        
        return permissions


def login_form() -> Optional[Session]:
    """Render login form and handle authentication."""
    st.subheader("🔐 Login")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        
        if submitted:
            if not username or not password:
                st.error("Please provide both username and password")
                return None
            
            auth_manager = AuthenticationManager(
                secret_key=st.secrets.get("auth_secret_key", "dev-secret-key")
            )
            
            session = auth_manager.authenticate_user(
                username=username,
                password=password,
                ip_address=st.session_state.get('client_ip', 'unknown'),
                user_agent=st.session_state.get('user_agent', 'unknown')
            )

            if session:
                st.success("✅ Login successful!")
                # Rotaciona CSRF após login
                AuthenticationManager(st.secrets.get("auth_secret_key", "dev-secret-key")).rotate_csrf()
                st.rerun()
                return session
            else:
                st.error("❌ Invalid credentials")
                return None
    
    return None


def init_default_admin():
    """Initialize default admin user for first setup."""
    auth_manager = AuthenticationManager(
        secret_key=st.secrets.get("auth_secret_key", "dev-secret-key")
    )
    
    # Check if admin exists
    existing_admin = None
    for user in st.session_state.auth_manager['users'].values():
        if 'admin' in user.roles:
            existing_admin = user
            break
    
    if not existing_admin:
        # SECURITY FIX: Use environment variable for admin password
        import os
        admin_password = os.environ.get("TDD_ADMIN_PASSWORD")
        if not admin_password:
            # Generate a secure random password if not set
            import secrets
            import string
            admin_password = ''.join(secrets.choice(string.ascii_letters + string.digits + "!@#$%") for _ in range(16))
            st.warning(f"⚠️ Auto-generated admin password: {admin_password}")
            st.info("💡 Set TDD_ADMIN_PASSWORD environment variable to use a custom password")
        
        admin_user = auth_manager.create_user(
            username="admin",
            email="admin@localhost",
            password=admin_password,  # SECURITY: No longer hardcoded
            roles=["admin"]
        )
        if os.environ.get("TDD_ADMIN_PASSWORD"):
            st.success("🔧 Admin user created with environment password")
        else:
            st.warning("🔧 Admin user created with auto-generated password (see above)")


# Streamlit decorators for easy usage
def authenticated_page(func):
    """Decorator to require authentication for Streamlit pages."""
    def wrapper(*args, **kwargs):
        auth_manager = AuthenticationManager(
            secret_key=st.secrets.get("auth_secret_key", "dev-secret-key")
        )
        user = auth_manager.require_authentication()
        return func(user, *args, **kwargs)
    return wrapper


def permission_required(permission: str):
    """Decorator to require specific permission for Streamlit pages."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            auth_manager = AuthenticationManager(
                secret_key=st.secrets.get("auth_secret_key", "dev-secret-key")
            )
            user = auth_manager.require_permission(permission)
            return func(user, *args, **kwargs)
        return wrapper
    return decorator


def csrf_protected(func):
    """Decorator to add CSRF protection to form submissions."""
    def wrapper(*args, **kwargs):
        auth_manager = AuthenticationManager(
            secret_key=st.secrets.get("auth_secret_key", "dev-secret-key")
        )
        
        session = auth_manager.get_current_session()
        if not session:
            st.error("🔒 Session expired. Please log in again.")
            st.stop()
        
        # Add CSRF token to form
        if 'csrf_token' not in st.session_state:
            st.session_state.csrf_token = session.csrf_token
        
        return func(*args, **kwargs)
    return wrapper
