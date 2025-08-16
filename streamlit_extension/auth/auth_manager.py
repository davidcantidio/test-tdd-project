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
