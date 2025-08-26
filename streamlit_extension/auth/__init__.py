#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔐 Authentication Module — Google OAuth Integration

Este módulo centraliza a autenticação via **Google OAuth 2.0** com
retrocompatibilidade para trechos legados que ainda esperam funções
locais de autenticação.

- ✅ Método primário: Google OAuth (via `..utils.auth`)
- ♻️ Legado: `auth_middleware`, `is_authenticated`, `get_current_user`
- 🧪 Seguro para import: falhas em dependências geram *fallback* controlado
- 🧭 Uso recomendado:
        GoogleOAuthManager,
        get_authenticated_user,
        is_user_authenticated,
        render_login_page,
        require_authentication,
        auth_middleware,         # alias legado
        is_authenticated,        # alias legado
        get_current_user,        # alias legado
    )

Comportamento em fallback (dependências ausentes):
- Fornece *stubs* previsíveis
- `require_authentication` bloqueia de forma amigável (Streamlit) ou
  lança `RuntimeError` em ambientes sem UI.

Observações:
- Este módulo não configura variáveis de ambiente. Garanta que as
  credenciais do Google (client id/secret, redirect URI etc.) estejam
  corretamente definidas no ambiente esperado por `..utils.auth`.

"""

from __future__ import annotations

from typing import Optional, Any, Callable, TypeVar, Dict
from functools import wraps
import logging

logger = logging.getLogger(__name__)

# Streamlit é opcional: usado apenas para UX melhor no fallback/decorators
try:
    import streamlit as st  # type: ignore
    _STREAMLIT_AVAILABLE = True
except Exception:  # pragma: no cover
    st = None  # type: ignore
    _STREAMLIT_AVAILABLE = False

# Tipos auxiliares
F = TypeVar("F", bound=Callable[..., Any])

# Flag de disponibilidade do backend OAuth real
_OAUTH_AVAILABLE = False

# Espaço de nomes default (sobrescrito no try/except abaixo quando disponível)
class _GoogleOAuthManagerStub:  # pragma: no cover
    """Stub usado apenas quando dependências de OAuth não estão disponíveis."""
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        raise RuntimeError(
            "Google OAuth não está disponível. "
            "Verifique se as dependências e configurações foram instaladas."
        )

def _fallback_get_authenticated_user() -> Optional[Dict[str, Any]]:  # pragma: no cover
    logger.warning("get_authenticated_user(): OAuth indisponível — retornando None.")
    return None

def _fallback_is_user_authenticated() -> bool:  # pragma: no cover
    logger.warning("is_user_authenticated(): OAuth indisponível — retornando False.")
    return False

def _fallback_render_login_page() -> None:  # pragma: no cover
    msg = "Google OAuth não configurado. Contate o administrador."
    if _STREAMLIT_AVAILABLE:
        st.error(msg)  # type: ignore
        st.stop()      # type: ignore
    else:
        raise RuntimeError(msg)

def _fallback_require_authentication(func: F) -> F:  # pragma: no cover
    @wraps(func)
    def _wrapper(*args: Any, **kwargs: Any):
        if _STREAMLIT_AVAILABLE and st is not None:
            st.warning("Autenticação obrigatória. Faça login para continuar.")  # type: ignore
            _fallback_render_login_page()
            st.stop()  # type: ignore
        raise RuntimeError("Autenticação exigida, mas Google OAuth não está disponível.")
    return _wrapper  # type: ignore


# Tentativa de importar a implementação real de OAuth
try:
    from ..utils.auth_streamlit_native import (  # type: ignore
        get_authenticated_user as _get_authenticated_user_real,
        is_user_authenticated as _is_user_authenticated_real,
        render_login_page as _render_login_page_real,
    )
    # Create a mock GoogleOAuthManager since we're using native Streamlit OAuth
    class _GoogleOAuthManagerReal:
        def __init__(self, *args, **kwargs):
            logger.info("Using Streamlit native OAuth - GoogleOAuthManager is a compatibility wrapper")
    
    # Create a mock require_authentication decorator
    def _require_authentication_real(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not _is_user_authenticated_real():
                _render_login_page_real()
                if _STREAMLIT_AVAILABLE and st:
                    st.stop()
                return None
            return func(*args, **kwargs)
        return wrapper
    # Marcar como disponível e expor símbolos reais
    _OAUTH_AVAILABLE = True

    GoogleOAuthManager = _GoogleOAuthManagerReal
    get_authenticated_user = _get_authenticated_user_real
    is_user_authenticated = _is_user_authenticated_real
    render_login_page = _render_login_page_real
    require_authentication = _require_authentication_real

except Exception as e:  # pragma: no cover
    # Dependências/ambiente não disponíveis — configurar fallback seguro
    GoogleOAuthManager = _GoogleOAuthManagerStub         # type: ignore
    get_authenticated_user = _fallback_get_authenticated_user
    is_user_authenticated = _fallback_is_user_authenticated
    render_login_page = _fallback_render_login_page
    require_authentication = _fallback_require_authentication
    logger.warning("Google OAuth não disponível: %s", e)


# ============
# Retrocompat
# ============

def auth_middleware() -> Optional[Dict[str, Any]]:
    """
    Alias de compatibilidade. Retorna o usuário autenticado (ou None).
    Preferir `get_authenticated_user()`.
    """
    return get_authenticated_user()

def is_authenticated() -> bool:
    """
    Alias de compatibilidade. Retorna True/False se o usuário está autenticado.
    Preferir `is_user_authenticated()`.
    """
    return is_user_authenticated()

def get_current_user() -> Optional[Dict[str, Any]]:
    """
    Alias de compatibilidade. Retorna o usuário corrente (ou None).
    Preferir `get_authenticated_user()`.
    """
    return get_authenticated_user()


# ==================
# Utilidades extras
# ==================

def ensure_oauth_available(raise_error: bool = False) -> bool:
    """
    Indica se o backend de OAuth real está disponível.
    - Se `raise_error=True` e indisponível, lança `RuntimeError`.
    """
    if not _OAUTH_AVAILABLE and raise_error:
        raise RuntimeError(
            "Google OAuth não está disponível. "
            "Instale e configure as dependências necessárias."
        )
    return _OAUTH_AVAILABLE


# Exportação de símbolos públicos
__all__ = [
    # API primária
    "GoogleOAuthManager",
    "get_authenticated_user",
    "is_user_authenticated",
    "render_login_page",
    "require_authentication",
    "ensure_oauth_available",
    # Aliases legados
    "auth_middleware",
    "is_authenticated",
    "get_current_user",
]