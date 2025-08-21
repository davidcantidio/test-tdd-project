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
    """Refactored method with extracted responsibilities."""
    render_user_profile_data_access()
    render_user_profile_ui_interaction()
    render_user_profile_validation()
    render_user_profile_logging()
    render_user_profile_formatting()
    pass  # TODO: Integrate extracted method results # Tracked: 2025-08-21

def render_user_profile_data_access():
    """
    Extracted method handling data_access operations.
    Original responsibility: Data Access operations
    """
    # TODO: Extract specific logic from lines [87, 88, 89, 90, 93, 96] # Tracked: 2025-08-21
    pass

def render_user_profile_ui_interaction():
    """
    Extracted method handling ui_interaction operations.
    Original responsibility: Ui Interaction operations
    """
    # TODO: Extract specific logic from lines [72, 73, 74, 75, 78, 81, 83, 86, 87, 88, 89, 90, 93, 96, 99, 101, 102, 103, 104, 106, 108, 110, 115, 117, 121, 123] # Tracked: 2025-08-21
    pass

def render_user_profile_validation():
    """
    Extracted method handling validation operations.
    Original responsibility: Validation operations
    """
    # TODO: Extract specific logic from lines [107] # Tracked: 2025-08-21
    pass

def render_user_profile_logging():
    """
    Extracted method handling logging operations.
    Original responsibility: Logging operations
    """
    # TODO: Extract specific logic from lines [75, 108, 110, 117] # Tracked: 2025-08-21
    pass

def render_user_profile_formatting():
    """
    Extracted method handling formatting operations.
    Original responsibility: Formatting operations
    """
    # TODO: Extract specific logic from lines [87, 88, 89, 90, 93, 96] # Tracked: 2025-08-21
    pass