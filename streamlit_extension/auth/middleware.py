#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔐 Authentication Middleware for Streamlit Pages

Middleware de autenticação com suporte a:
- Checagem de sessão e sincronização do usuário atual
- Controle de acesso baseado em papéis (RBAC)
- Decorators @require_auth e @require_admin
- UX segura: mensagens claras, limpeza de sessão inválida
- Opção de "debug" controlada por variável de ambiente

Compatibilidade: mantém nomes/funções públicas já usadas no projeto
(init_protected_page, require_auth, require_admin, etc.).
"""

from __future__ import annotations

import os
from functools import wraps
from typing import Callable, Optional, Sequence, Any, List

import streamlit as st

from .auth_manager import AuthManager
from .user_model import User, UserRole


# =============================================================================
# Flags/Config
# =============================================================================

# Exibe detalhes técnicos de erro somente se explicitamente habilitado.
_AUTH_DEBUG = os.environ.get("AUTH_DEBUG", "").strip().lower() in {"1", "true", "yes"}


# =============================================================================
# AuthManager Singleton
# =============================================================================

_auth_manager: Optional[AuthManager] = None  # instancia global


def get_auth_manager() -> AuthManager:
    """Retorna a instância global do AuthManager (singleton por processo)."""
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = AuthManager()
    return _auth_manager


# =============================================================================
# Helpers
# =============================================================================

def _safe_error(msg: str, exc: Exception | None = None) -> str:
    """Mensagem de erro com detalhes apenas em modo debug."""
    if _AUTH_DEBUG and exc is not None:
        return f"{msg} (details: {exc})"
    return msg


def _format_roles(roles: Sequence[UserRole]) -> str:
    """Formata lista de papéis para exibição amigável."""
    items: List[str] = []
    for r in roles:
        # usa display_name se existir; senão .name/.value
        display = getattr(r, "display_name", None) or getattr(r, "name", None) or getattr(r, "value", str(r))
        items.append(str(display))
    return ", ".join(items)


def _get_session_id() -> Optional[str]:
    """Obtém o session_id do estado do Streamlit (ou None)."""
    sid = st.session_state.get("session_id")
    return str(sid) if sid else None


def _set_current_user(user: Optional[User]) -> None:
    """Atualiza o usuário atual no estado da sessão."""
    if user is None:
        st.session_state.pop("current_user", None)
    else:
        st.session_state["current_user"] = user


def _check_session_timeout() -> bool:
    """
    TDAH-friendly session timeout check with gentle warnings.
    Returns True if session is still valid, False if expired.
    """
    import time
    
    # Get session timestamp (when user logged in)
    session_start = st.session_state.get("session_start_time")
    if not session_start:
        # No session timestamp, set it now for existing sessions
        st.session_state["session_start_time"] = time.time()
        return True
    
    # Calculate session age (in minutes)
    session_age_minutes = (time.time() - session_start) / 60
    
    # TDAH-friendly timeout: 2 hours with warnings
    if session_age_minutes > 120:  # 2 hours - actual timeout
        return False
    elif session_age_minutes > 100:  # 1h 40min - urgent warning
        st.warning("⏰ **Session expires in 20 minutes.** Please save your work and refresh to extend session.")
        return True
    elif session_age_minutes > 90:  # 1h 30min - gentle warning  
        st.info("💡 **Heads up:** Your session expires in 30 minutes. No action needed yet!")
        return True
    
    return True  # Session is still fresh


# =============================================================================
# Núcleo de autenticação
# =============================================================================

def auth_middleware() -> Optional[User]:
    """
    Middleware para sincronizar estado de autenticação:
    - Carrega usuário a partir do session_id quando existente.
    - Remove sessão inválida de forma segura.
    - Verifica timeout de sessão com avisos TDAH-friendly.
    - Retorna o User atual (ou None).
    """
    session_id = _get_session_id()
    if not session_id:
        _set_current_user(None)
        return None

    # TDAH-friendly session timeout check
    if not _check_session_timeout():
        # Session expired - gentle cleanup
        st.session_state.pop("session_id", None)
        st.session_state.pop("session_start_time", None)
        _set_current_user(None)
        st.info("⏰ **Session expired.** Please log in again to continue. Your work preferences have been saved.")
        return None

    am = get_auth_manager()
    try:
        user = am.get_current_user(session_id)
    except Exception as e:  # robustez contra falhas de backend
        _set_current_user(None)
        st.session_state.pop("session_id", None)
        # Em debug mostramos detalhes; em produção, mensagem neutra
        st.warning(_safe_error("Authentication backend unavailable", e))
        return None

    if not user:
        # sessão expirada/ inválida
        st.session_state.pop("session_id", None)
        st.session_state.pop("session_start_time", None)
        _set_current_user(None)
        return None

    _set_current_user(user)
    return user


def get_current_user() -> Optional[User]:
    """Retorna o usuário autenticado atual (se houver)."""
    user = st.session_state.get("current_user")
    if user is not None:
        return user  # já sincronizado no ciclo
    # tenta sincronizar a partir do session_id se ainda não fez
    return auth_middleware()


def is_authenticated() -> bool:
    """Indica se há um usuário autenticado no contexto atual."""
    return get_current_user() is not None


# =============================================================================
# Decorators
# =============================================================================

def require_auth(roles: Optional[Sequence[UserRole]] = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator para exigir autenticação (e, opcionalmente, papéis específicos).

    Exemplo:
        @require_auth()
        def page():
            ...

        @require_auth([UserRole.ADMIN, UserRole.MANAGER])
        def page_admin_or_manager():
            ...
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # 1) Verifica sessão e sincroniza usuário
            user = auth_middleware()
            if not user:
                # TDAH-friendly error handling: clear message + helpful guidance
                st.error("🔒 Access denied. Please log in to continue.")
                st.info("💡 **Need to access this page?** Please authenticate first using the login form.")
                
                # Show login guidance instead of abrupt termination
                with st.expander("🚀 Quick Login Help"):
                    st.markdown("""
                    1. Click **Login** in the navigation
                    2. Enter your credentials
                    3. Return to this page after authentication
                    """)
                return None  # Graceful exit instead of st.stop()

            # 2) Checa papéis (se solicitados)
            if roles and user.role not in roles:
                # TDAH-friendly role error: encouraging message + clear guidance
                st.error(f"🔒 Access restricted. Required role: {_format_roles(roles)}")
                current_role = getattr(user.role, "display_name", None) or getattr(user.role, "value", None) or str(user.role)
                st.info(f"💼 **Your current role:** {current_role}")
                
                # Provide helpful next steps
                with st.expander("🤝 Request Access"):
                    st.markdown("""
                    **Need access to this feature?**
                    1. Contact your administrator
                    2. Request the required role permissions
                    3. Return after role update
                    """)
                return None  # Graceful exit instead of st.stop()

            # 3) Executa função protegida
            return func(*args, **kwargs)
        return wrapper
    return decorator


def require_admin(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator para exigir papel ADMIN."""
    @wraps(func)
    @require_auth([UserRole.ADMIN])
    def _wrapped(*args: Any, **kwargs: Any) -> Any:
        return func(*args, **kwargs)
    return _wrapped


# =============================================================================
# Fluxos utilitários
# =============================================================================

def logout_user() -> None:
    """Efetua logout do usuário atual (encerra sessão e rerun)."""
    session_id = _get_session_id()
    if session_id:
        try:
            get_auth_manager().logout(session_id)
        except Exception as e:
            # Não impede o logout local; apenas informa em debug
            if _AUTH_DEBUG:
                st.warning(f"Logout backend failed: {e}")

    st.session_state.pop("session_id", None)
    _set_current_user(None)
    st.rerun()


def show_user_info() -> None:
    """Exibe informações do usuário autenticado na sidebar (quando houver)."""
    user = get_current_user()
    if not user:
        return

    with st.sidebar:
        st.markdown("---")
        st.markdown("### 👤 User Info")
        # Usa atributos mais informativos quando disponíveis
        username = getattr(user, "username", None) or getattr(user, "email", None) or "user"
        role_label = getattr(user.role, "display_name", None) or getattr(user.role, "value", None) or str(user.role)
        st.markdown(f"**Username:** {username}")
        st.markdown(f"**Role:** {role_label}")

        if st.button("🚪 Logout", use_container_width=True):
            logout_user()


def init_protected_page(page_title: str, required_roles: Optional[Sequence[UserRole]] = None) -> Optional[User]:
    """
    Inicializa uma página protegida:
    - Define título
    - Verifica autenticação e papéis (se exigidos)
    - Exibe informações do usuário na sidebar
    - Retorna o usuário autenticado ou None (quando acesso negado)

    Args:
        page_title: Título da página
        required_roles: Lista opcional de papéis necessários

    Returns:
        User | None
    """
    # Título da página
    st.title(page_title)

    # Sincroniza usuário a partir da sessão
    user = auth_middleware()
    if not user:
        st.error("🔒 Access denied. Please log in.")
        st.info("Please authenticate to access this page.")
        return None

    # Checa papéis, se fornecidos
    if required_roles and user.role not in required_roles:
        st.error(f"🔒 Access denied. Required role: {_format_roles(required_roles)}")
        current_role = getattr(user.role, "display_name", None) or getattr(user.role, "value", None) or str(user.role)
        st.info(f"Your role: {current_role}")
        return None

    # Exibe informações de usuário
    show_user_info()
    return user


# =============================================================================
# API pública
# =============================================================================

__all__ = [
    # núcleo
    "get_auth_manager",
    "auth_middleware",
    "get_current_user",
    "is_authenticated",
    "logout_user",

    # decorators
    "require_auth",
    "require_admin",

    # páginas
    "init_protected_page",
    "show_user_info",
]
