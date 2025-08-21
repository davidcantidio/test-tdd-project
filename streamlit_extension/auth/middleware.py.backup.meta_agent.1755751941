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
    """Initialize a protected page with authentication checks.
    
    Args:
        page_title: Title to display on the page
        required_roles: Optional list of required roles
    
    Returns:
        Current user if authenticated and authorized, None otherwise
    """
    # TEMPORARY DEV BYPASS - Remove this for production
    environment = os.getenv('TDD_ENVIRONMENT', '').lower()
    if environment in ['development', 'dev', 'testing', 'test']:
        try:
            from .user_model import User, UserRole
            mock_user = User(
                id=1,
                username="dev_user",
                email="dev@example.com",
                role=UserRole.ADMIN,
                is_active=True
            )
            st.session_state.current_user = mock_user
            
            # Show development notice
            with st.sidebar:
                st.warning("🧪 Development Mode - Authentication Bypassed")
            
            return mock_user
        except Exception as e:
            st.error(f"Dev bypass error: {e}")
    
    # Check for development mode bypass
    try:
        from ..config import get_config
        config = get_config()
        is_dev_mode = getattr(config, 'debug_mode', False) or getattr(config, 'testing_mode', False)
        
        # Allow bypass in development/testing mode
        if is_dev_mode:
            # Create mock user for development
            from .user_model import User, UserRole
            mock_user = User(
                id=1,
                username="dev_user",
                email="dev@example.com",
                role=UserRole.ADMIN,
                is_active=True
            )
            st.session_state.current_user = mock_user
            
            # Show development notice
            with st.sidebar:
                st.warning("🧪 Development Mode - Authentication Bypassed")
            
            return mock_user
    except Exception as e:
        # If config fails, continue with normal auth flow
        pass
    
    # Don't call st.set_page_config here since main app already calls it
    # st.set_page_config(page_title=page_title, layout="wide")
    
    # Run authentication middleware
    user = auth_middleware()
    
    if not user:
        st.title("🔐 Authentication Required")
        st.error("Please log in to access this page.")
        
        # Display login form
        from .login_page import render_login_page
        render_login_page()
        return None
    
    # Check role requirements
    if required_roles and user.role not in required_roles:
        st.error(f"🚫 Access denied. Required role: {[r.value for r in required_roles]}")
        st.stop()
    
    # Show user info in sidebar
    show_user_info()
    
    # Display page title
    st.title(page_title)
    
    return user
