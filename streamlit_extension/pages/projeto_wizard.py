#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 PAGES - Projeto Wizard

Página principal do wizard de criação de projetos.
Implementa autenticação, proteção básica de sessão (CSRF token em nível de página),
rate limiting por usuário e integração com o componente principal do wizard.

Padrões aplicados:
- Autenticação obrigatória
- CSRF token armazenado em session_state
- Rate limiting com chave por usuário
- Tratamento de exceções com fallback seguro
- set_page_config protegido contra chamadas duplicadas
"""

from __future__ import annotations

import logging
import secrets
from typing import Any, Dict, Optional
from contextlib import suppress

import streamlit as st

# Importações do projeto (seguindo padrões do repositório)
from ..auth.middleware import init_protected_page
from ..utils.exception_handler import handle_streamlit_exceptions
from ..utils.security import check_rate_limit
from ..components.projeto_wizard import render_projeto_wizard

logger = logging.getLogger(__name__)


# ============================================================================ #
# Page Configuration (tolerante a múltiplas chamadas em apps multipágina)
# ============================================================================ #

with suppress(Exception):
    st.set_page_config(
        page_title="Novo Projeto - TDD Framework",
        page_icon="🚀",
        layout="wide",
        initial_sidebar_state="collapsed",
    )


# ============================================================================ #
# Helpers (SRP: separar UI auxiliares)
# ============================================================================ #

def _ensure_csrf_token() -> str:
    """Garante a existência de um token de CSRF em nível de sessão."""
    token = st.session_state.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        st.session_state["csrf_token"] = token
    return token


def _render_sidebar(current_user: Dict[str, Any]) -> None:
    """Renderiza informações do usuário e dicas do wizard na sidebar."""
    with st.sidebar:
        st.markdown("### 👤 Usuário Logado")
        st.write(f"**Nome:** {current_user.get('name', 'Usuário')}")
        st.write(f"**Email:** {current_user.get('email', 'email@exemplo.com')}")

        st.markdown("---")
        st.markdown("### 💡 Dicas do Wizard")
        st.info(
            """
            **🎯 Como usar:**
            1. **Visão**: Defina objetivos claros
            2. **Épicos**: Agrupe funcionalidades grandes  
            3. **Stories**: Detalhe requisitos específicos
            4. **Tasks**: Crie items executáveis
            5. **Preview**: Visualize o backlog final

            **🤖 IA Integrada:** Use os botões de IA em cada step para sugestões inteligentes!

            **💾 Auto-Save:** Seus dados são salvos automaticamente.
            """
        )


def _render_footer() -> None:
    """Renderiza rodapé da página com informações úteis e ações de suporte."""
    st.markdown("---")
    col_recursos, col_status, col_suporte = st.columns([2, 1, 1])

    with col_recursos:
        st.markdown("### 📚 Recursos Adicionais")
        st.markdown(
            """
            - [📖 Guia TDD](/) - Como usar metodologia TDD
            - [🎯 Templates de Projeto](/templates) - Modelos prontos  
            - [🤖 Integração IA](/ai-docs) - Como usar sugestões de IA
            """
        )

    with col_status:
        st.markdown("### 🚀 Status do Sistema")
        st.success("✅ Wizard Operacional")
        st.info("🤖 IA Integrada")
        st.info("💾 Auto-save Ativo")

    with col_suporte:
        st.markdown("### 🆘 Suporte")
        if st.button("💬 Relatar Problema"):
            st.info("TODO: Implementar sistema de feedback")
        if st.button("❓ Ajuda"):
            st.info("TODO: Implementar sistema de ajuda contextual")


# ============================================================================ #
# Main Page Function
# ============================================================================ #

@handle_streamlit_exceptions(show_error=True, attempt_recovery=True)
def render_projeto_wizard_page() -> None:
    """
    Renderiza a página do wizard de projetos com padrões de segurança e UX.
    """
    # 1) Autenticação obrigatória
    current_user: Optional[Dict[str, Any]] = init_protected_page("🚀 Criar Novo Projeto")
    if not current_user:
        st.info("🔒 Faça login para acessar o sistema de criação de projetos")
        return

    # 2) Proteções de sessão (CSRF em nível de página)
    csrf_token = _ensure_csrf_token()  # Disponível para componentes lerem se necessário

    # 3) Rate limiting por usuário (evita bloqueio cruzado entre contas/sessões)
    user_id = str(current_user.get("id") or current_user.get("email") or "anon")
    rl_key = f"projeto_wizard_page:{user_id}"
    rate_limit_ok, rate_limit_msg = check_rate_limit(rl_key)
    if not rate_limit_ok:
        st.error(f"🚦 {rate_limit_msg}")
        st.info("Aguarde alguns instantes antes de tentar novamente.")
        return

    # 4) Header da página
    st.title("🚀 Criar Novo Projeto")
    st.markdown("Crie um projeto completo com IA: Visão → Épicos → Stories → Tasks → Planejamento")

    # 5) Sidebar
    _render_sidebar(current_user)

    # 6) Componente principal do wizard
    try:
        # Se o componente do wizard suportar, ele pode ler st.session_state['csrf_token']
        # para validar envios de formulário.
        render_projeto_wizard()
    except Exception as e:  # noqa: BLE001 - queremos logar e mostrar mensagem amigável
        logger.exception("Erro ao renderizar wizard de projeto: %s", e)
        st.error("❌ Erro interno no wizard. Tente recarregar a página.")
        # Evita vazar detalhes em produção; habilite via secrets DEBUG=true se quiser ver.
        if bool(st.secrets.get("DEBUG", False)) and st.checkbox("🔧 Mostrar detalhes técnicos"):
            st.exception(e)

    # 7) Footer
    _render_footer()


# ============================================================================ #
# Page Entry Point
# ============================================================================ #

# Em apps multipágina do Streamlit, o arquivo é executado como script.
# Chamamos explicitamente a função principal para manter padrão consistente.
render_projeto_wizard_page()
