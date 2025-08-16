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
