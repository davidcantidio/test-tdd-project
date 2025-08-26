#!/usr/bin/env python3
"""
🔐 Streamlit Native OAuth Implementation
Following official Streamlit documentation for Google OAuth authentication.
https://docs.streamlit.io/develop/tutorials/authentication/google
"""

from __future__ import annotations

import streamlit as st
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

def login_screen():
    """Display login screen with official Streamlit OAuth button."""
    st.header("🔐 TDD Framework Login")
    st.subheader("Please authenticate with your Google account.")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.button(
            "🔐 Log in with Google", 
            on_click=st.login,
            type="primary",
            use_container_width=True
        )
    
    st.markdown("---")
    st.caption("🔒 Secure authentication powered by Google OAuth 2.0")

def is_user_authenticated() -> bool:
    """Check if user is authenticated using native Streamlit API."""
    try:
        return st.user.is_logged_in if hasattr(st, 'user') else False
    except Exception as e:
        logger.debug(f"Authentication check failed: {e}")
        return False

def get_authenticated_user() -> Optional[Dict[str, Any]]:
    """Get authenticated user data using native Streamlit API."""
    try:
        if not is_user_authenticated():
            return None
        
        # Return user data from native Streamlit API
        user_data = {
            'id': getattr(st.user, 'id', 'native_user'),
            'name': getattr(st.user, 'name', 'User'),
            'email': getattr(st.user, 'email', ''),
            'picture': getattr(st.user, 'picture', ''),
            'auth_method': 'streamlit_native_oauth',
            'is_logged_in': st.user.is_logged_in
        }
        
        logger.info(f"✅ User authenticated via Streamlit native OAuth: {user_data.get('email', 'unknown')}")
        return user_data
        
    except Exception as e:
        logger.error(f"Failed to get user data: {e}")
        return None

def handle_logout():
    """Handle user logout using native Streamlit API."""
    try:
        st.logout()
        logger.info("🔐 User logged out via Streamlit native OAuth")
        st.success("✅ Logout successful!")
        st.rerun()
    except Exception as e:
        logger.error(f"Logout failed: {e}")
        st.error("❌ Logout failed. Please try again.")

def render_login_page():
    """Render complete login page with native Streamlit authentication."""
    if not is_user_authenticated():
        login_screen()
    else:
        # User is already authenticated, show user info
        user = get_authenticated_user()
        if user:
            st.success(f"✅ Welcome, {user.get('name', 'User')}!")
            st.button("🔓 Log out", on_click=handle_logout)

def get_user_info_widget() -> Dict[str, str]:
    """Get user info for sidebar display."""
    user = get_authenticated_user()
    if user:
        return {
            'username': user.get('name', 'User'),
            'email': user.get('email', ''),
            'role': 'User',  # Default role - can be enhanced later
            'picture': user.get('picture', '')
        }
    return {
        'username': 'Not logged in',
        'email': '',
        'role': 'Guest',
        'picture': ''
    }

# Compatibility functions for existing codebase
def render_user_info():
    """Render user information in sidebar (compatibility function)."""
    user = get_authenticated_user()
    if user:
        st.sidebar.success(f"👤 {user['name']}")
        if user.get('email'):
            st.sidebar.text(f"📧 {user['email']}")
        st.sidebar.button("🔓 Logout", on_click=handle_logout)
    else:
        st.sidebar.warning("🔐 Not authenticated")

__all__ = [
    'is_user_authenticated',
    'get_authenticated_user', 
    'render_login_page',
    'handle_logout',
    'get_user_info_widget',
    'render_user_info'
]