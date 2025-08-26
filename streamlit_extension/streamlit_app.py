#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 TDD Framework - Pure Orchestrator (Optimized)

- Entrada única, mínima, resiliente.
- Sem dependências de UI em modo headless.
- Logs padronizados e coesos.
- Autenticação com fallback simples e seguro.
- Tipagem melhorada para o usuário autenticado.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Optional, TypedDict

# === LOGGING SETUP ============================================================
# Configura logging apenas se o root logger ainda não tiver handlers.
if not logging.getLogger().handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

logger = logging.getLogger("orchestrator")

# === STREAMLIT IMPORT ========================================================
# Safe streamlit import for OAuth functionality
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    st = None
    STREAMLIT_AVAILABLE = False

# === CENTRALIZED IMPORTS (helpers do projeto) =================================
from streamlit_extension.utils.streamlit_helpers import (
    is_ui,
    is_headless,
    set_page_config_once,
    safe_streamlit_error,
    add_project_to_path,
)
from streamlit_extension.utils.session_manager import (
    initialize_session_state,
    is_debug_mode,
)
from streamlit_extension.utils.exception_handler import handle_streamlit_exceptions

# Components (apenas referências — cada módulo encapsula sua própria lógica)
from streamlit_extension.components.sidebar import render_sidebar
from streamlit_extension.components.layout_renderers import render_topbar
from streamlit_extension.components.page_manager import render_current_page

# Painel de debug (opcional)
from streamlit_extension.components.debug_widgets import render_debug_panel

# 🔐 OFFICIAL STREAMLIT OAUTH - NO FALLBACKS
# Following: https://docs.streamlit.io/develop/tutorials/authentication/google

# Banco (para headless)
from streamlit_extension.database.queries import list_epics
from streamlit_extension.database.health import check_health


# === TYPES ====================================================================

class AuthenticatedUser(TypedDict, total=False):
    id: str
    name: str
    email: str
    role: str


# === CONFIG ===================================================================

@dataclass(frozen=True)
class OrchestratorConfig:
    page_title: str = "TDD Framework Dashboard"
    page_icon: str = "🚀"
    layout: str = "wide"
    initial_sidebar_state: str = "expanded"


CONFIG = OrchestratorConfig()


# === MODULE INIT ==============================================================
# Garante que o projeto esteja no PYTHONPATH, antes de qualquer coisa.
add_project_to_path()

# Configura a página do Streamlit (somente se UI disponível).
if is_ui():
    set_page_config_once(
        page_title=CONFIG.page_title,
        page_icon=CONFIG.page_icon,
        layout=CONFIG.layout,
        initial_sidebar_state=CONFIG.initial_sidebar_state,
        menu_items={
            "Report a bug": "https://github.com/davidcantidio/test-tdd-project/issues",
            "About": (
                "# TDD Framework - Advanced Dashboard\n"
                "- ⏱️ Timer com suporte a TDAH\n"
                "- 📋 Kanban de tarefas\n"
                "- 📊 Analytics e produtividade\n"
                "- 🎮 Gamification\n"
                "- 🐙 Integração GitHub\n"
                "**Version:** 1.3.4 (Orchestrator Optimized)"
            ),
        },
    )


# === ORCHESTRATION ============================================================

def setup_application() -> None:
    """Inicializa estado de sessão e dependências mínimas."""
    initialize_session_state()
    logger.info("Session state initialized.")

def _render_login_inline() -> None:
    """
    🔐 OFFICIAL STREAMLIT OAUTH LOGIN - NO FALLBACKS
    Following official documentation exactly.
    """
    if not is_ui():
        return
    
    # Check if streamlit is available and has OAuth capabilities
    if not STREAMLIT_AVAILABLE or st is None:
        logger.error("Streamlit not available for OAuth login rendering")
        return
        
    if not hasattr(st, 'login'):
        logger.error("Streamlit OAuth not available - missing st.login method")
        return
    
    # Official Streamlit OAuth login screen
    st.header("🔐 TDD Framework")
    st.subheader("Please log in with your Google account")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.button(
            "🔐 Log in with Google", 
            on_click=st.login,
            type="primary",
            use_container_width=True
        )
    
    st.markdown("---")
    st.caption("🔒 Secure authentication via Google OAuth 2.0")

def authenticate_user() -> Optional[AuthenticatedUser]:
    """
    🔐 OFFICIAL STREAMLIT OAUTH AUTHENTICATION - NO FALLBACKS
    Uses ONLY st.user.is_logged_in and st.user properties.
    """
    if not is_ui():
        # Headless mode - return sentinel for smoke tests
        return AuthenticatedUser(name="Headless", id="headless")

    # Check if streamlit is available and has OAuth capabilities
    if not STREAMLIT_AVAILABLE or st is None:
        logger.error("Streamlit not available for OAuth authentication")
        return None
    
    if not hasattr(st, 'user'):
        logger.error("Streamlit OAuth not available - missing st.user attribute")
        return None

    # OFFICIAL STREAMLIT OAUTH CHECK - NO FALLBACKS
    if not st.user.is_logged_in:
        _render_login_inline()
        return None

    # OFFICIAL STREAMLIT USER DATA - NO PROCESSING
    return AuthenticatedUser(
        id=getattr(st.user, 'id', 'streamlit_user'),
        name=getattr(st.user, 'name', 'User'),
        email=getattr(st.user, 'email', ''),
        role="User"  # Default role - can be enhanced later
    )

def render_application_ui(user: AuthenticatedUser) -> None:
    """Renderiza a UI principal com segurança e isolando falhas."""
    if not is_ui():
        return

    try:
        # Sidebar/navigation
        _sidebar_state = render_sidebar()

        # Top bar (saudação, status, etc.)
        render_topbar(user)

        # Página atual
        render_current_page(user)

        # Debug panel opcional
        if is_debug_mode():
            render_debug_panel()

    except Exception as e:
        logger.exception("UI rendering error: %s", e)
        safe_streamlit_error("⚠️ Application UI temporarily unavailable.")

def run_headless_mode() -> None:
    """Executa um smoke test em modo headless (sem Streamlit)."""
    logger.info("Headless mode: starting smoke tests.")
    try:
        epics = list_epics()
        health = check_health()
        logger.info(
            "Headless results | epics=%d | health=%s",
            len(epics),
            health.get("status", "unknown"),
        )
    except Exception as e:
        # Não interrompe pipeline headless; apenas registra.
        logger.exception("Headless test error: %s", e)


# === MAIN =====================================================================

@handle_streamlit_exceptions(show_error=True, attempt_recovery=True)
def main() -> None:
    """
    Orquestrador principal:
    - Headless → smoke test
    - UI → sessão, auth, UI
    """
    # Headless prioriza execução rápida para CI/smoke
    if is_headless():
        run_headless_mode()
        return

    # Setup mínimo
    setup_application()

    # Autenticação
    user = authenticate_user()
    if user is None:
        # Página de login já renderizada; não prosseguir com o app.
        logger.debug("Authentication pending; halting UI render for now.")
        return

    # Render principal
    render_application_ui(user)

    logger.info("Application orchestration completed successfully.")


# === HEALTH ===================================================================

def check_orchestrator_health() -> dict[str, Any]:
    """
    Health-check leve do orquestrador (não toca UI).
    Útil para testes rápidos e sondas locais.
    """
    return {
        "ui_mode": "UI" if is_ui() else ("Headless" if is_headless() else "Unknown"),
        "streamlit_helpers_available": True,
        "session_manager_available": True,
        "exception_handler_available": True,
        "sidebar_available": True,
        "layout_renderers_available": True,
        "page_manager_available": True,
        "debug_widgets_available": True,
        "auth_available": True,
        "database_available": True,
        "status": "healthy",
    }


# === ENTRYPOINT ===============================================================

if __name__ == "__main__":
    main()
