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
