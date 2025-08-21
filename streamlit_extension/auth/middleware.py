"""
🔐 Authentication Middleware for Streamlit Pages

Enhanced authentication middleware that integrates with the DRY form components
and provides comprehensive page protection with role-based access control.
"""

import os
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
        # Singleton instância única
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
    session_id = st.session_state.get("session_id")
    if not session_id:
        return None
    auth_manager = get_auth_manager()
    user = auth_manager.get_current_user(session_id)
    if not user:
        st.session_state.pop("session_id", None)
        st.session_state.pop("current_user", None)
        return None
    st.session_state.current_user = user
    return user


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


def show_user_info():
    """Display current user information in sidebar."""
    user = get_current_user()
    if user:
        with st.sidebar:
            st.markdown("---")
            st.markdown("### 👤 User Info")
            st.markdown(f"**Username:** {user.username}")
            st.markdown(f"**Role:** {user.role.value}")
            
            if st.button("🚪 Logout", use_container_width=True):
                logout_user()


def init_protected_page(page_title: str, required_roles: Optional[list[UserRole]] = None):
    """Refactored method with extracted responsibilities."""
    init_protected_page_ui_interaction()
    init_protected_page_validation()
    init_protected_page_logging()
    init_protected_page_error_handling()
    init_protected_page_configuration()
    init_protected_page_formatting()
    pass  # TODO: Integrate extracted method results # Tracked: 2025-08-21

def init_protected_page_ui_interaction():
    """
    Extracted method handling ui_interaction operations.
    Original responsibility: Ui Interaction operations
    """
    # TODO: Extract specific logic from lines [141, 144, 145, 149, 168, 171, 172, 179, 180, 186, 187, 190, 191, 196, 197, 203] # Tracked: 2025-08-21
    pass

def init_protected_page_validation():
    """
    Extracted method handling validation operations.
    Original responsibility: Validation operations
    """
    # TODO: Extract specific logic from lines [185] # Tracked: 2025-08-21
    pass

def init_protected_page_logging():
    """
    Extracted method handling logging operations.
    Original responsibility: Logging operations
    """
    # TODO: Extract specific logic from lines [145, 149, 172, 187, 196] # Tracked: 2025-08-21
    pass

def init_protected_page_error_handling():
    """
    Extracted method handling error_handling operations.
    Original responsibility: Error Handling operations
    """
    # TODO: Extract specific logic from lines [132, 148, 152, 175] # Tracked: 2025-08-21
    pass

def init_protected_page_configuration():
    """
    Extracted method handling configuration operations.
    Original responsibility: Configuration operations
    """
    # TODO: Extract specific logic from lines [130, 131, 153, 154, 155, 176, 179, 180] # Tracked: 2025-08-21
    pass

def init_protected_page_formatting():
    """
    Extracted method handling formatting operations.
    Original responsibility: Formatting operations
    """
    # TODO: Extract specific logic from lines [130, 149, 196] # Tracked: 2025-08-21
    pass