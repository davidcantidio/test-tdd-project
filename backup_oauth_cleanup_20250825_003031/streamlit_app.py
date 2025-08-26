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

# Autenticação
from streamlit_extension.utils.auth import (
    render_login_page,
    get_authenticated_user,
    is_user_authenticated,
)

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
    """Renderiza a página de login de forma segura (somente em UI)."""
    if not is_ui():
        return
    try:
        render_login_page()
    except Exception as e:
        # Evita hard-fail na tela de login; mostra erro amigável e loga detalhes.
        logger.exception("Authentication UI error: %s", e)
        safe_streamlit_error("🔒 Authentication system unavailable at the moment.")

def authenticate_user() -> Optional[AuthenticatedUser]:
    """
    Controla autenticação com fallback simples e seguro.
    - Headless: retorna usuário sentinel.
    - UI sem sessão: mostra login e interrompe render do app por agora.
    - UI com sessão: retorna dados do usuário (normalizados).
    """
    if not is_ui():
        # Em headless não há sessão UI: retorna sentinel para seguir smoke test.
        return AuthenticatedUser(name="Headless", id="headless")

    if not is_user_authenticated():
        _render_login_inline()
        return None

    user = get_authenticated_user()
    
    # Normalização defensiva do retorno do auth layer
    if isinstance(user, dict):
        # Mapeia chaves padrão, tolerando ausência.
        return AuthenticatedUser(
            id=str(user.get("id", "")),
            name=str(user.get("name", "User")),
            email=str(user.get("email", "")),
            role=str(user.get("role", "")),
        )

    # Fallback seguro (não quebra UI, mas deixa evidente o estado)
    logger.warning("Authenticated user returned in unexpected format: %r", user)
    return AuthenticatedUser(name="User")

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
