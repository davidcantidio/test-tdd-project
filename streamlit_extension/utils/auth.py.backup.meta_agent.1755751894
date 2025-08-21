"""
🔐 Google OAuth Authentication System for TDD Framework

This module provides comprehensive Google OAuth 2.0 authentication with:
- Google Workspace integration
- Session management
- User profile handling
- Security features (CSRF protection, secure cookies)
"""

import os
import json
import time
import hashlib
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from urllib.parse import urlencode

try:
    import streamlit as st
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import Flow
    from googleapiclient.discovery import build
    import requests
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Authentication dependencies not available: {e}")
    DEPENDENCIES_AVAILABLE = False
    st = None


class GoogleOAuthManager:
    """Manages Google OAuth 2.0 authentication flow for Streamlit applications."""
    
    def __init__(self):
        """Initialize OAuth manager with configuration from Streamlit secrets."""
        if not DEPENDENCIES_AVAILABLE:
            raise ImportError("Required authentication dependencies not installed")
        
        self.client_id = st.secrets["google"]["client_id"]
        self.client_secret = st.secrets["google"]["client_secret"]
        self.redirect_uri = st.secrets["google"]["redirect_uri"]
        self.scopes = st.secrets["google"]["scopes"]
        
        # Application configuration
        self.app_name = st.secrets["app"]["name"]
        self.require_auth = st.secrets["app"]["require_auth"]
        self.debug = st.secrets["app"]["debug"]
        
        # Session configuration
        self.session_timeout = st.secrets["session"]["timeout_minutes"] * 60  # Convert to seconds
        self.cookie_name = st.secrets["session"]["cookie_name"]
        
    def create_flow(self) -> Flow:
        """Create and configure Google OAuth flow."""
        client_config = {
            "web": {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [self.redirect_uri]
            }
        }
        
        flow = Flow.from_client_config(
            client_config,
            scopes=self.scopes
        )
        flow.redirect_uri = self.redirect_uri
        
        return flow
    
    def get_authorization_url(self) -> Tuple[str, str]:
        """Generate OAuth authorization URL with CSRF protection."""
        flow = self.create_flow()
        
        # Generate CSRF state token
        state = hashlib.sha256(f"{time.time()}{self.client_id}".encode()).hexdigest()
        
        # Store state in session for verification
        st.session_state.oauth_state = state
        
        authorization_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            state=state,
            prompt='consent'  # Force consent screen for refresh tokens
        )
        
        return authorization_url, state
    
    def handle_callback(self, authorization_code: str, state: str) -> Dict[str, Any]:
        """Handle OAuth callback and exchange code for tokens."""
        # Verify CSRF state
        if state != st.session_state.get('oauth_state'):
            raise ValueError("Invalid OAuth state - possible CSRF attack")
        
        flow = self.create_flow()
        
        try:
            # Exchange authorization code for tokens
            flow.fetch_token(code=authorization_code)
            credentials = flow.credentials
            
            # Get user information
            user_info = self.get_user_info(credentials)
            
            # Create authenticated session
            session_data = {
                'user_info': user_info,
                'credentials': {
                    'token': credentials.token,
                    'refresh_token': credentials.refresh_token,
                    'token_uri': credentials.token_uri,
                    'client_id': credentials.client_id,
                    'client_secret': credentials.client_secret,
                    'scopes': credentials.scopes
                },
                'authenticated_at': datetime.now().isoformat(),
                'expires_at': (datetime.now() + timedelta(seconds=self.session_timeout)).isoformat()
            }
            
            # Store in session state
            st.session_state.authenticated = True
            st.session_state.user_session = session_data
            
            # Clear OAuth state
            if 'oauth_state' in st.session_state:
                del st.session_state.oauth_state
            
            return session_data
            
        except Exception as e:
            self.debug_log(f"OAuth callback error: {e}")
            raise Exception(f"Authentication failed: {str(e)}")
    
    def get_user_info(self, credentials: Credentials) -> Dict[str, Any]:
        """Retrieve user information using Google People API."""
        try:
            # Build People API service
            service = build('people', 'v1', credentials=credentials)
            
            # Get user profile
            profile = service.people().get(
                resourceName='people/me',
                personFields='names,emailAddresses,photos,organizations'
            ).execute()
            
            # Extract user information
            user_info = {
                'id': profile.get('resourceName', '').replace('people/', ''),
                'email': None,
                'name': None,
                'picture': None,
                'organization': None
            }
            
            # Extract email
            emails = profile.get('emailAddresses', [])
            if emails:
                user_info['email'] = emails[0].get('value')
            
            # Extract name
            names = profile.get('names', [])
            if names:
                user_info['name'] = names[0].get('displayName')
            
            # Extract profile picture
            photos = profile.get('photos', [])
            if photos:
                user_info['picture'] = photos[0].get('url')
            
            # Extract organization
            organizations = profile.get('organizations', [])
            if organizations:
                user_info['organization'] = organizations[0].get('name')
            
            self.debug_log(f"Retrieved user info for: {user_info.get('email')}")
            return user_info
            
        except Exception as e:
            self.debug_log(f"Error retrieving user info: {e}")
            # Fallback to basic token info
            return {
                'id': 'unknown',
                'email': 'unknown@example.com',
                'name': 'Unknown User',
                'picture': None,
                'organization': None
            }
    
    def is_authenticated(self) -> bool:
        """Check if user is currently authenticated with valid session."""
        if not st.session_state.get('authenticated', False):
            return False
        
        session = st.session_state.get('user_session')
        if not session:
            return False
        
        # Check session expiration
        try:
            expires_at = datetime.fromisoformat(session['expires_at'])
            if datetime.now() > expires_at:
                self.logout()
                return False
        except (KeyError, ValueError):
            self.logout()
            return False
        
        return True
    
    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Get current authenticated user information."""
        if not self.is_authenticated():
            return None
        
        session = st.session_state.get('user_session')
        return session.get('user_info') if session else None
    
    def logout(self):
        """Clear authentication session and logout user."""
        # Clear session state
        keys_to_remove = ['authenticated', 'user_session', 'oauth_state']
        for key in keys_to_remove:
            if key in st.session_state:
                del st.session_state[key]
        
        self.debug_log("User logged out")
    
    def refresh_credentials(self) -> bool:
        """Refresh expired credentials using refresh token."""
        session = st.session_state.get('user_session')
        if not session or 'credentials' not in session:
            return False
        
        try:
            cred_data = session['credentials']
            credentials = Credentials(
                token=cred_data['token'],
                refresh_token=cred_data['refresh_token'],
                token_uri=cred_data['token_uri'],
                client_id=cred_data['client_id'],
                client_secret=cred_data['client_secret'],
                scopes=cred_data['scopes']
            )
            
            # Refresh token
            credentials.refresh(Request())
            
            # Update session with new token
            session['credentials']['token'] = credentials.token
            session['expires_at'] = (datetime.now() + timedelta(seconds=self.session_timeout)).isoformat()
            st.session_state.user_session = session
            
            self.debug_log("Credentials refreshed successfully")
            return True
            
        except Exception as e:
            self.debug_log(f"Failed to refresh credentials: {e}")
            self.logout()
            return False
    
    def debug_log(self, message: str):
        """Log debug messages if debug mode is enabled."""
        if self.debug:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp}] AUTH DEBUG: {message}")


def require_authentication(func):
    """Decorator to require authentication for Streamlit pages."""
    def wrapper(*args, **kwargs):
        if not DEPENDENCIES_AVAILABLE:
            if st is not None:
                st.error("❌ Authentication system not available - dependencies missing")
                st.stop()
            else:
                print("❌ Authentication system not available - dependencies missing")
                return {"error": "Authentication dependencies not available"}
        
        try:
            auth_manager = GoogleOAuthManager()
            
            # Skip authentication if not required
            if not auth_manager.require_auth:
                return func(*args, **kwargs)
            
            # Check if user is authenticated
            if auth_manager.is_authenticated():
                return func(*args, **kwargs)
            
            # Show login page
            render_login_page(auth_manager)
            
        except Exception as e:
            if st is not None:
                st.error(f"❌ Authentication Error: {e}")
                st.error("Please check your configuration and try again.")
                st.stop()
            else:
                print(f"❌ Authentication Error: {e}")
                return {"error": f"Authentication Error: {e}"}
    
    return wrapper


def render_login_page(auth_manager: GoogleOAuthManager):
    """Render the Google OAuth login page."""
    st.title("🔐 TDD Framework - Authentication Required")
    st.markdown("Please sign in with your Google account to access the application.")
    
    # Handle OAuth callback
    query_params = st.query_params
    
    if 'code' in query_params and 'state' in query_params:
        with st.spinner("🔄 Authenticating..."):
            try:
                auth_code = query_params['code']
                state = query_params['state']
                
                # Handle OAuth callback
                session_data = auth_manager.handle_callback(auth_code, state)
                
                # Clear query parameters and redirect
                st.query_params.clear()
                st.success(f"✅ Welcome, {session_data['user_info']['name']}!")
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Authentication failed: {e}")
                st.query_params.clear()
                st.rerun()
    
    else:
        # Show login button
        st.markdown("---")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            if st.button("🔗 Sign in with Google", use_container_width=True, type="primary"):
                with st.spinner("🔄 Redirecting to Google..."):
                    try:
                        auth_url, state = auth_manager.get_authorization_url()
                        
                        # JavaScript redirect to OAuth URL
                        st.markdown(
                            f"""
                            <meta http-equiv="refresh" content="0; url={auth_url}">
                            <script>
                                window.location.href = "{auth_url}";
                            </script>
                            """,
                            unsafe_allow_html=True
                        )
                        
                    except Exception as e:
                        st.error(f"❌ Failed to initiate authentication: {e}")
        
        # Information section
        st.markdown("---")
        with st.expander("ℹ️ About Authentication"):
            st.markdown("""
            **Google OAuth 2.0 Authentication**
            
            This application uses Google OAuth 2.0 for secure authentication:
            
            - ✅ **Secure**: Your password never leaves Google's servers
            - ✅ **Privacy**: We only access basic profile information
            - ✅ **Control**: You can revoke access anytime in your Google account
            
            **What information we access:**
            - Email address (for identification)
            - Display name (for personalization) 
            - Profile picture (optional)
            - Organization (if available)
            
            **Your data is safe:**
            - No passwords are stored
            - Sessions expire automatically
            - All communication is encrypted
            """)


def render_user_menu(auth_manager: GoogleOAuthManager):
    """Render user menu with profile and logout options."""
    if not auth_manager.is_authenticated():
        return
    
    user = auth_manager.get_current_user()
    if not user:
        return
    
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 👤 User Profile")
        
        # User avatar and info
        col1, col2 = st.columns([1, 2])
        
        with col1:
            if user.get('picture'):
                st.image(user['picture'], width=50)
            else:
                st.markdown("👤")
        
        with col2:
            st.markdown(f"**{user.get('name', 'Unknown')}**")
            st.caption(user.get('email', 'No email'))
            if user.get('organization'):
                st.caption(f"🏢 {user['organization']}")
        
        # Logout button
        if st.button("🚪 Logout", use_container_width=True):
            auth_manager.logout()
            st.rerun()


# Utility functions for easy integration
def get_authenticated_user() -> Optional[Dict[str, Any]]:
    """Get the currently authenticated user (utility function)."""
    if not DEPENDENCIES_AVAILABLE:
        return None
    
    try:
        auth_manager = GoogleOAuthManager()
        return auth_manager.get_current_user()
    except:
        return None


def is_user_authenticated() -> bool:
    """Check if user is authenticated (utility function)."""
    if not DEPENDENCIES_AVAILABLE:
        return False
    
    try:
        auth_manager = GoogleOAuthManager()
        return auth_manager.is_authenticated()
    except:
        return False