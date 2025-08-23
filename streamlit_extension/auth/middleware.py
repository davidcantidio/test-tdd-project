#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔐 Authentication Middleware for Streamlit Pages (Refined)

- Mantém API pública: get_auth_manager, auth_middleware, get_current_user,
  is_authenticated, logout_user, require_auth, require_admin, init_protected_page, show_user_info.
- Melhora RBAC (hierarquia), sessões, testabilidade e coesão.
"""

from __future__ import annotations

import os
import time
from functools import lru_cache, wraps
from typing import Callable, Optional, Sequence, Any, List, Protocol, runtime_checkable

import streamlit as st
from .auth_manager import AuthManager
from .user_model import User, UserRole


# =============================================================================
# Flags/Config
# =============================================================================

_AUTH_DEBUG = os.environ.get("AUTH_DEBUG", "").strip().lower() in {"1", "true", "yes"}


# =============================================================================
# UI Abstractions (para facilitar testes/headless)
# =============================================================================

@runtime_checkable
class UINotifier(Protocol):
    def info(self, msg: str) -> None: ...
    def warning(self, msg: str) -> None: ...
    def error(self, msg: str) -> None: ...
    def sidebar_separator(self) -> None: ...
    def rerun(self) -> None: ...

class _StreamlitNotifier:
    def info(self, msg: str) -> None: st.info(msg)
    def warning(self, msg: str) -> None: st.warning(msg)
    def error(self, msg: str) -> None: st.error(msg)
    def sidebar_separator(self) -> None:
        with st.sidebar: st.markdown("---")
    def rerun(self) -> None: st.rerun()

_ui: UINotifier = _StreamlitNotifier()


# =============================================================================
# AuthManager Singleton (cacheado)
# =============================================================================

@lru_cache(maxsize=1)
def get_auth_manager() -> AuthManager:
    """Instância singleton cacheada por processo (mais robusto em reruns)."""
    return AuthManager()


# =============================================================================
# Helpers
# =============================================================================

def _safe_error(msg: str, exc: Exception | None = None) -> str:
    return f"{msg} (details: {exc})" if (_AUTH_DEBUG and exc is not None) else msg

def _format_roles(roles: Sequence[UserRole]) -> str:
    items: List[str] = []
    for r in roles:
        display = getattr(r, "display_name", None) or getattr(r, "name", None) or getattr(r, "value", str(r))
        items.append(str(display))
    return ", ".join(items)

def _get_session_id() -> Optional[str]:
    sid = st.session_state.get("session_id")
    return str(sid) if sid else None

def _set_current_user(user: Optional[User]) -> None:
    if user is None:
        st.session_state.pop("current_user", None)
    else:
        st.session_state["current_user"] = user

def _clear_session(expired: bool = False) -> None:
    """Limpa sessão local de forma uniforme."""
    st.session_state.pop("session_id", None)
    st.session_state.pop("session_start_time", None)
    if expired:
        st.session_state.pop("session_extended", None)
        st.session_state.pop("session_duration", None)
    _set_current_user(None)

def _role_satisfies(required: Sequence[UserRole], actual: UserRole) -> bool:
    """
    RBAC simples com hierarquia: ADMIN > MANAGER > USER (ajuste se houver mais papéis).
    Se 'required' estiver vazio→libera. Se contiver ADMIN, exige ADMIN.
    """
    if not required:
        return True
    # mapa de nível (quanto maior, mais privilégio)
    level = {
        getattr(UserRole, "USER", "USER"): 1,
        getattr(UserRole, "MANAGER", "MANAGER"): 2,
        getattr(UserRole, "ADMIN", "ADMIN"): 3,
    }
    req_max = max(level.get(r, 0) for r in required)
    return level.get(actual, 0) >= req_max

def _emit_session_expiry_warnings() -> None:
    """
    Mensagens TDAH-friendly — não retorna nada, apenas emite UI quando aplicável.
    """
    start = st.session_state.get("session_start_time")
    if not start:
        st.session_state["session_start_time"] = time.time()
        return

    duration = int(st.session_state.get("session_duration", 2 * 60 * 60))  # 2h padrão
    extended = bool(st.session_state.get("session_extended", False))
    age = time.time() - float(start)

    if age >= duration:
        return  # expirado: a limpeza ocorre em _check_session_timeout()

    if extended:
        # avisos a 24h e 12h
        if age > duration - (24 * 60 * 60):
            _ui.info("💡 **Sua sessão estendida expira em 24h.** Sem ação necessária por enquanto.")
        if age > duration - (12 * 60 * 60):
            _ui.warning("⏰ **Sessão estendida expira em 12h.** Atualize para estender.")
    else:
        # avisos a 30min e 20min
        mins_left = (duration - age) / 60
        if mins_left <= 30:
            _ui.info("💡 **Sua sessão expira em 30 min.**")
        if mins_left <= 20:
            _ui.warning("⏰ **Sessão expira em 20 min.** Salve seu trabalho e atualize para estender.")


def _check_session_timeout() -> bool:
    """
    Retorna True se sessão ainda válida; False se expirada (sem efeitos colaterais além de avisos).
    """
    start = st.session_state.get("session_start_time")
    duration = int(st.session_state.get("session_duration", 2 * 60 * 60))
    if not start:
        st.session_state["session_start_time"] = time.time()
        return True

    age = time.time() - float(start)
    if age > duration:
        return False

    # Emite avisos amigáveis (não quebra fluxo)
    _emit_session_expiry_warnings()
    return True


# =============================================================================
# Núcleo de autenticação
# =============================================================================

def auth_middleware() -> Optional[User]:
    """
    Sincroniza estado de autenticação:
    - Carrega usuário a partir do session_id quando existente.
    - Remove sessão inválida/expirada de forma segura.
    - Emite avisos TDAH-friendly.
    - Retorna o User atual (ou None).
    """
    session_id = _get_session_id()
    if not session_id:
        _set_current_user(None)
        return None

    if not _check_session_timeout():
        _clear_session(expired=True)
        _ui.info("⏰ **Sessão expirada.** Faça login novamente. Suas preferências foram mantidas.")
        return None

    am = get_auth_manager()
    try:
        user = am.get_current_user(session_id)
    except Exception as e:
        # Backend indisponível — limpa somente o local; não insiste
        _clear_session()
        _ui.warning(_safe_error("Authentication backend unavailable", e))
        return None

    if not user:
        _clear_session()
        return None

    _set_current_user(user)
    return user


def get_current_user() -> Optional[User]:
    user = st.session_state.get("current_user")
    return user if user is not None else auth_middleware()


def is_authenticated() -> bool:
    return get_current_user() is not None


# =============================================================================
# Decorators
# =============================================================================

def require_auth(roles: Optional[Sequence[UserRole]] = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Exige autenticação e (opcionalmente) papéis mínimos, com hierarquia.
    Ex.: @require_auth(), @require_auth([UserRole.MANAGER]), @require_auth([UserRole.ADMIN])
    """
    roles = roles or []

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            user = auth_middleware()
            if not user:
                _ui.error("🔒 Acesso negado. Faça login para continuar.")
                with st.expander("🚀 Como entrar"):
                    st.markdown("1) Abra **Login** • 2) Autentique • 3) Volte a esta página")
                return None

            if roles and not _role_satisfies(roles, user.role):
                _ui.error(f"🔒 Acesso restrito. Papel necessário: {_format_roles(roles)}")
                current_role = getattr(user.role, "display_name", None) or getattr(user.role, "value", None) or str(user.role)
                _ui.info(f"💼 **Seu papel atual:** {current_role}")
                with st.expander("🤝 Solicitar acesso"):
                    st.markdown("1) Contate o administrador • 2) Peça a permissão • 3) Retorne após atualização")
                return None

            return func(*args, **kwargs)
        return wrapper
    return decorator


def require_admin(func: Callable[..., Any]) -> Callable[..., Any]:
    """Atalho para exigir papel ADMIN (com hierarquia)."""
    return require_auth([UserRole.ADMIN])(func)


# =============================================================================
# Fluxos utilitários
# =============================================================================

def logout_user() -> None:
    """Logout local + backend, com rerun."""
    session_id = _get_session_id()
    if session_id:
        try:
            get_auth_manager().logout(session_id)
        except Exception as e:
            if _AUTH_DEBUG:
                _ui.warning(f"Logout backend failed: {e}")
    _clear_session()
    _ui.rerun()


def show_user_info() -> None:
    """Exibe informações do usuário autenticado na sidebar (quando houver)."""
    user = get_current_user()
    if not user:
        return

    with st.sidebar:
        st.markdown("---")
        st.markdown("### 👤 User Info")
        username = getattr(user, "username", None) or getattr(user, "email", None) or "user"
        role_label = getattr(user.role, "display_name", None) or getattr(user.role, "value", None) or str(user.role)
        st.markdown(f"**Username:** {username}")
        st.markdown(f"**Role:** {role_label}")
        if st.button("🚪 Logout", use_container_width=True):
            logout_user()


def init_protected_page(page_title: str, required_roles: Optional[Sequence[UserRole]] = None) -> Optional[User]:
    """
    Inicializa página protegida:
    - Verifica autenticação e papéis (hierarquia)
    - Exibe informações do usuário
    - Redireciona para login se necessário
    - Retorna o usuário autenticado ou None
    """
    user = auth_middleware()
    if not user:
        # Tenta redirecionar via page_manager, senão fallback
        try:
            from ..components.page_manager import redirect_to_login
            redirect_to_login()
            return None
        except Exception:
            _ui.error("🔒 Acesso negado. Faça login.")
            _ui.info("Autentique para acessar esta página.")
            return None

    st.title(page_title)

    if required_roles and not _role_satisfies(required_roles, user.role):
        _ui.error(f"🔒 Acesso negado. Papel necessário: {_format_roles(required_roles)}")
        current_role = getattr(user.role, "display_name", None) or getattr(user.role, "value", None) or str(user.role)
        _ui.info(f"Seu papel: {current_role}")
        return None

    show_user_info()
    return user


# =============================================================================
# API pública
# =============================================================================

__all__ = [
    "get_auth_manager",
    "auth_middleware",
    "get_current_user",
    "is_authenticated",
    "logout_user",
    "require_auth",
    "require_admin",
    "init_protected_page",
    "show_user_info",
]
