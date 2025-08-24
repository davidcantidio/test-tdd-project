#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔐 Google OAuth 2.0 para o TDD Framework (Streamlit Native)

Usando o sistema nativo de autenticação do Streamlit:
- st.login() com persistência adequada de sessão durante redirects
- Proteção CSRF automática que sobrevive redirects externos
- Gerenciamento integrado de estado OAuth
- Tratamento otimizado de sessão de usuário do Streamlit
- Compatibilidade com fallback para padrões de código existentes
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, Any, Optional

# ---- Streamlit Native Authentication --------------------------------
try:
    import streamlit as st
    DEPS = True
except Exception as e:
    logging.info(f"⚠️ Streamlit não disponível: {e}")
    st = None  # type: ignore
    DEPS = False

# Import configuration
try:
    import sys
    import os
    from pathlib import Path
    # Add project root to path to resolve config imports
    project_root = Path(__file__).parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from config.environment import get_config, has_oauth_credentials, is_oauth_enabled
    CONFIG_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Config import failed: {e} - using fallback configuration")
    CONFIG_AVAILABLE = False
    def get_config():
        return type('Config', (), {'google_oauth': type('OAuth', (), {
            'enabled': False,
            'client_id': '',
            'client_secret': ''
        })()})()"
    def has_oauth_credentials(): return False
    def is_oauth_enabled(): return False

logger = logging.getLogger(__name__)

# =============================================================================
# Native Streamlit Authentication Configuration
# =============================================================================

@dataclass
class GoogleOAuthConfig:
    """Configuração OAuth 2.0 para Google usando Streamlit Native Auth."""
    client_id: str = ""
    client_secret: str = ""
    enabled: bool = False
    
    @classmethod
    def from_config_system(cls) -> "GoogleOAuthConfig":
        """Carrega configuração OAuth do sistema de configuração."""
        if not CONFIG_AVAILABLE:
            return cls(enabled=False)
            
        try:
            config = get_config()
            if hasattr(config, 'google_oauth'):
                return cls(
                    client_id=config.google_oauth.client_id,
                    client_secret=config.google_oauth.client_secret,
                    enabled=getattr(config.google_oauth, 'enabled', False)
                )
        except Exception as e:
            logger.warning(f"Erro ao carregar config OAuth: {e}")
        
        return cls(enabled=False)


# =============================================================================
# Streamlit Native OAuth Manager
# =============================================================================

class StreamlitNativeOAuthManager:
    """
    Gerenciador OAuth usando sistema nativo do Streamlit.
    Resolve problemas de persistência de estado CSRF durante redirects.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = GoogleOAuthConfig.from_config_system()
        
        # Verifica se OAuth está configurado
        self.configured = self.config.enabled and bool(self.config.client_id and self.config.client_secret)
        
        if self.configured:
            self.logger.info("🔐 Native OAuth configured and enabled")
        else:
            self.logger.info("🔐 Native OAuth not configured - using fallback authentication")
    
    def is_configured(self) -> bool:
        """Verifica se OAuth está devidamente configurado."""
        return self.configured
    
    def is_authenticated(self) -> bool:
        """
        Verifica se usuário está autenticado usando sistema nativo do Streamlit.
        """
        if not DEPS:
            return False
            
        # Streamlit native authentication check
        if hasattr(st, 'user') and st.user is not None:
            return True
            
        # Fallback for development mode
        if not self.configured and hasattr(st, 'session_state'):
            return st.session_state.get('auth_fallback_user') is not None
            
        return False
    
    def get_user(self) -> Optional[Dict[str, Any]]:
        """
        Obtém dados do usuário autenticado usando sistema nativo do Streamlit.
        """
        if not DEPS:
            return None
            
        # Native Streamlit user data
        if hasattr(st, 'user') and st.user is not None:
            user_data = {
                'id': getattr(st.user, 'id', ''),
                'name': getattr(st.user, 'name', 'User'),
                'email': getattr(st.user, 'email', ''),
                'picture': getattr(st.user, 'picture', ''),
            }
            self.logger.info(f"🔐 Native OAuth user authenticated: {user_data.get('email', 'unknown')}")
            return user_data
            
        # Fallback for development mode
        if not self.configured and hasattr(st, 'session_state'):
            fallback_user = st.session_state.get('auth_fallback_user')
            if fallback_user:
                self.logger.info("🔐 Using fallback authentication")
                return fallback_user
                
        return None
    
    def login(self) -> None:
        """
        Inicia processo de login usando sistema nativo do Streamlit.
        """
        if not DEPS:
            st.error("🚫 Streamlit authentication not available")
            return
            
        if self.configured:
            # Use Streamlit native login
            try:
                # Configure OAuth provider
                st.login(
                    provider="google",
                    oauth_config={
                        "client_id": self.config.client_id,
                        "client_secret": self.config.client_secret,
                        "redirect_uri": "http://localhost:8501",
                        "scope": ["openid", "email", "profile"]
                    }
                )
                self.logger.info("🔐 Native OAuth login initiated")
            except Exception as e:
                self.logger.error(f"🚫 Native OAuth login failed: {e}")
                st.error(f"🚫 OAuth login error: {str(e)}")
        else:
            # Fallback authentication for development
            self._render_fallback_login()
    
    def logout(self) -> None:
        """
        Executa logout usando sistema nativo do Streamlit.
        """
        if not DEPS:
            return
            
        if self.configured and hasattr(st, 'logout'):
            # Use Streamlit native logout
            st.logout()
            self.logger.info("🔐 Native OAuth logout completed")
        else:
            # Fallback logout
            if hasattr(st, 'session_state'):
                st.session_state.pop('auth_fallback_user', None)
                self.logger.info("🔐 Fallback logout completed")
        
        # Force page rerun to update UI
        if hasattr(st, 'rerun'):
            st.rerun()
    
    def _render_fallback_login(self) -> None:
        """
        Renderiza sistema de login alternativo para desenvolvimento.
        """
        st.info("🔐 OAuth não configurado - usando autenticação de desenvolvimento")
        
        with st.form("dev_login_form"):
            st.subheader("🛠️ Login de Desenvolvimento")
            name = st.text_input("Nome", value="Developer")
            email = st.text_input("Email", value="dev@example.com")
            
            if st.form_submit_button("Entrar"):
                fallback_user = {
                    'id': 'dev_user',
                    'name': name or 'Developer',
                    'email': email or 'dev@example.com',
                    'picture': '',
                    'is_fallback': True
                }
                st.session_state['auth_fallback_user'] = fallback_user
                self.logger.info(f"🔐 Fallback authentication: {email}")
                st.rerun()


# =============================================================================
# Compatibility Layer - Maintains existing API patterns
# =============================================================================

# Global manager instance
_oauth_manager = None

def get_oauth_manager() -> StreamlitNativeOAuthManager:
    """Get singleton OAuth manager instance."""
    global _oauth_manager
    if _oauth_manager is None:
        _oauth_manager = StreamlitNativeOAuthManager()
    return _oauth_manager

def is_user_authenticated() -> bool:
    """Check if user is authenticated (compatibility function)."""
    return get_oauth_manager().is_authenticated()

def get_authenticated_user() -> Optional[Dict[str, Any]]:
    """Get authenticated user data (compatibility function)."""
    return get_oauth_manager().get_user()

def render_login_page() -> None:
    """Render login page (compatibility function)."""
    manager = get_oauth_manager()
    
    st.markdown("### 🔐 Autenticação TDD Framework")
    
    if not manager.is_configured():
        st.warning("⚠️ OAuth não configurado - usando modo de desenvolvimento")
    
    # Display login interface
    manager.login()

def handle_logout() -> None:
    """Handle user logout (compatibility function)."""
    get_oauth_manager().logout()


# =============================================================================
# Legacy Compatibility - Maintains GoogleOAuthManager interface
# =============================================================================

class GoogleOAuthManager:
    """
    Compatibility wrapper for legacy code that uses GoogleOAuthManager.
    Delegates to StreamlitNativeOAuthManager.
    """
    
    def __init__(self, cfg=None, store=None):
        self.native_manager = get_oauth_manager()
        self.logger = logging.getLogger(__name__)
    
    def is_authenticated(self) -> bool:
        return self.native_manager.is_authenticated()
    
    def get_user_info(self) -> Optional[Dict[str, Any]]:
        return self.native_manager.get_user()
    
    def get_authorization_url(self) -> tuple[str, str]:
        # Legacy method - not needed with native auth
        self.logger.warning("get_authorization_url() deprecated - use native login flow")
        return ("", "")
    
    def handle_callback(self, code: str, state: str) -> bool:
        # Legacy method - not needed with native auth
        self.logger.warning("handle_callback() deprecated - native auth handles this automatically")
        return self.native_manager.is_authenticated()
    
    def logout(self) -> None:
        self.native_manager.logout()


# =============================================================================
# Debug and Health Check Functions
# =============================================================================

def check_oauth_health() -> Dict[str, Any]:
    """Check OAuth system health and configuration."""
    manager = get_oauth_manager()
    
    health_status = {
        "streamlit_available": DEPS,
        "config_available": CONFIG_AVAILABLE,
        "oauth_configured": manager.is_configured(),
        "user_authenticated": manager.is_authenticated(),
        "timestamp": str(logger.handlers[0].formatter.formatTime(logging.LogRecord('', 0, '', 0, '', (), None)) if logger.handlers else "unknown")
    }
    
    if manager.is_authenticated():
        user = manager.get_user()
        health_status["user_email"] = user.get('email', 'unknown') if user else 'unknown'
        health_status["is_fallback_auth"] = user.get('is_fallback', False) if user else False
    
    return health_status

def debug_oauth_state() -> None:
    """Debug OAuth state for troubleshooting."""
    if not DEPS:
        st.error("Streamlit not available for debugging")
        return
    
    health = check_oauth_health()
    
    st.subheader("🔍 OAuth Debug Information")
    
    for key, value in health.items():
        if value:
            st.success(f"✅ {key}: {value}")
        else:
            st.error(f"❌ {key}: {value}")
    
    # Native Streamlit user information
    if hasattr(st, 'user') and st.user is not None:
        st.success("✅ Streamlit native user detected")
        st.json({
            "user_id": getattr(st.user, 'id', 'N/A'),
            "user_name": getattr(st.user, 'name', 'N/A'),
            "user_email": getattr(st.user, 'email', 'N/A')
        })
    else:
        st.warning("⚠️ No native Streamlit user found")
    
    # Session state information
    if hasattr(st, 'session_state'):
        auth_keys = [key for key in st.session_state.keys() if 'auth' in key.lower()]
        if auth_keys:
            st.info(f"🔍 Auth-related session keys: {auth_keys}")
        else:
            st.info("ℹ️ No auth-related session keys found")


# =============================================================================
# Main API Export
# =============================================================================

__all__ = [
    'GoogleOAuthManager',
    'StreamlitNativeOAuthManager', 
    'is_user_authenticated',
    'get_authenticated_user',
    'render_login_page',
    'handle_logout',
    'check_oauth_health',
    'debug_oauth_state'
]