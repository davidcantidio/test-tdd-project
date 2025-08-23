#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🖼️ WIZARD FRAME - Projeto Wizard (otimizado)
Baseado em streamlit-wizard-form, adaptado ao state_manager otimizado.

API mantida:
- set_wizard_view(view: str)
- set_wizard_step(action: str, step: Optional[int] = None)
- render_projeto_wizard(auto_load_draft: bool = True)
"""

from __future__ import annotations

import logging
from functools import partial
from typing import Optional

import streamlit as st

from .state_manager import (
    # estado & navegação
    Step, WizardView,
    get_wizard_state,
    initialize_wizard_state,
    update_wizard_state,
    is_step_valid,
    validate_all_wizard_data,
    has_validation_errors,
    add_validation_error,
    clear_validation_errors,
    # rascunho
    auto_save_wizard, save_wizard_draft, load_wizard_draft,
    # novos utilitários de nav
    set_current_step, set_current_view, sync_nav_from_session,
)

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Navegação (API compatível)
# --------------------------------------------------------------------------- #

def set_wizard_view(view: str) -> None:
    """
    Define a view principal do wizard.
    Compatível com a API anterior, mas delega ao state_manager.
    """
    try:
        set_current_view(view)
        # auto-save quando sai do wizard
        if str(view) != WizardView.WIZARD:
            auto_save_wizard()
    except Exception as e:
        logger.error("set_wizard_view error: %s", e, exc_info=True)


def set_wizard_step(action: str, step: Optional[int] = None) -> None:
    """
    Controla navegação entre steps do wizard.
    Actions: 'Next' | 'Back' | 'Jump'
    """
    try:
        sync_nav_from_session()
        state = get_wizard_state()
        current = int(state.current_step)

        if action == "Next":
            if not is_step_valid(current):
                st.error(f"❌ Complete os campos obrigatórios do Step {current}")
                return
            if current < int(Step.PREVIEW):
                set_current_step(current + 1)
                auto_save_wizard()

        elif action == "Back":
            if current > int(Step.VISION):
                set_current_step(current - 1)
                auto_save_wizard()

        elif action == "Jump":
            if step is None:
                return
            step_int = int(step)
            if int(Step.VISION) <= step_int <= int(Step.PREVIEW):
                set_current_step(step_int)
                auto_save_wizard()
    except Exception as e:
        logger.error("set_wizard_step error: %s", e, exc_info=True)


# --------------------------------------------------------------------------- #
# Estrutura do Wizard
# --------------------------------------------------------------------------- #

def projeto_wizard_header() -> None:
    """Cabeçalho do wizard com navegação por botões."""
    sync_nav_from_session()
    state = get_wizard_state()
    current = int(state.current_step)

    h1, h2, h3 = st.columns([1, 4, 1])
    with h2:
        st.subheader("🚀 Criar Novo Projeto")

    def _btn(label: str, target: int, help_text: str):
        st.button(
            label,
            type=("primary" if current == target else "secondary"),
            on_click=partial(set_wizard_step, "Jump", target),
            help=help_text,
            use_container_width=True,
        )

    c = st.columns([0.5, 1, 1, 1, 1, 1, 0.5])
    with c[1]: _btn("📝 Visão",   int(Step.VISION),  "Definir visão e objetivos do projeto")
    with c[2]: _btn("🎯 Épicos",  int(Step.EPICS),   "Criar épicos principais do projeto")
    with c[3]: _btn("📖 Stories", int(Step.STORIES), "Detalhar user stories com story points")
    with c[4]: _btn("✅ Tasks",   int(Step.TASKS),   "Criar tasks e marcar milestones")
    with c[5]: _btn("👁️ Preview",int(Step.PREVIEW), "Visualizar backlog e cronograma")


def projeto_wizard_body() -> None:
    """Corpo principal do wizard - renderiza conteúdo por step."""
    sync_nav_from_session()
    clear_validation_errors()

    state = get_wizard_state()
    step = int(state.current_step)

    if step == int(Step.VISION):
        render_step_1_vision()
    elif step == int(Step.EPICS):
        render_step_2_epics()
    elif step == int(Step.STORIES):
        render_step_3_stories()
    elif step == int(Step.TASKS):
        render_step_4_tasks()
    elif step == int(Step.PREVIEW):
        render_step_5_preview()
    else:
        st.error(f"❌ Step inválido: {step}")


def projeto_wizard_footer() -> None:
    """Rodapé com botões de navegação."""
    sync_nav_from_session()
    state = get_wizard_state()
    current = int(state.current_step)

    disable_back = current == int(Step.VISION)
    disable_next = current == int(Step.PREVIEW)

    col_cancel, col_back, col_next, col_spacer, col_primary = st.columns([3, 1, 1, 1, 2])

    col_cancel.button(
        "❌ Cancelar",
        on_click=partial(set_wizard_view, WizardView.PROJECT_LIST),
        help="Cancelar criação do projeto (rascunho será salvo)",
        use_container_width=True,
    )

    col_back.button(
        "⬅️ Voltar",
        on_click=partial(set_wizard_step, "Back"),
        disabled=disable_back,
        help="Voltar ao step anterior",
        use_container_width=True,
    )

    if current < int(Step.PREVIEW):
        # desabilita Próximo se step atual inválido
        col_next.button(
            "➡️ Próximo",
            on_click=partial(set_wizard_step, "Next"),
            disabled=disable_next or not is_step_valid(current),
            help="Avançar para próximo step",
            use_container_width=True,
        )

    if current == int(Step.PREVIEW):
        projeto_ready = validate_all_wizard_data()
        if col_primary.button(
            "🎉 Criar Projeto",
            disabled=not projeto_ready or has_validation_errors(),
            type="primary",
            help="Criar projeto com todos os dados preenchidos",
            use_container_width=True,
        ):
            create_project_from_wizard()


# --------------------------------------------------------------------------- #
# Step Renderers (placeholders)
# --------------------------------------------------------------------------- #

def render_step_1_vision() -> None:
    st.info("📝 **Step 1: Visão do Produto**")
    st.write("Defina a visão, objetivos e escopo do projeto")

    state = get_wizard_state()
    with st.form("vision_form", clear_on_submit=False):
        title = st.text_input(
            "Título do Projeto",
            value=state.vision_title,
            placeholder="Ex: Sistema de E-commerce Moderno",
        )
        description = st.text_area(
            "Descrição da Visão",
            value=state.vision_description,
            placeholder="Descreva o que o projeto pretende alcançar...",
            height=120,
        )
        submitted = st.form_submit_button("Salvar alterações", use_container_width=False)
        if submitted:
            update_wizard_state(vision_title=title, vision_description=description)
            auto_save_wizard()
            st.success("✅ Visão atualizada")

    if st.button("🤖 Sugerir com IA", help="(Sprint 3)"):
        st.info("TODO: Implementar integração com IA (Sprint 3)")


def render_step_2_epics() -> None:
    st.info("🎯 **Step 2: Épicos**")
    st.write("Crie os épicos principais que compõem o projeto")
    st.write("TODO: Implementar CRUD de épicos + integração IA")


def render_step_3_stories() -> None:
    st.info("📖 **Step 3: User Stories**")
    st.write("Detalhe as user stories com story points e priorização")
    st.write("TODO: Implementar CRUD de stories + story points + IA")


def render_step_4_tasks() -> None:
    st.info("✅ **Step 4: Tasks**")
    st.write("Crie tasks executáveis e marque milestones")
    st.write("TODO: Implementar CRUD de tasks + milestone marking + IA")


def render_step_5_preview() -> None:
    st.info("👁️ **Step 5: Preview**")
    st.write("Visualize o backlog completo e cronograma do projeto")
    st.write("TODO: Implementar Backlog tree + Gantt chart")


def create_project_from_wizard() -> None:
    if validate_all_wizard_data() and not has_validation_errors():
        st.success("✅ Projeto criado com sucesso!")
        st.info("TODO: Implementar persistência via services")
        set_wizard_view(WizardView.PROJECT_LIST)
    else:
        st.error("❌ Complete todos os steps obrigatórios antes de criar o projeto")


# --------------------------------------------------------------------------- #
# Rascunho & Debug
# --------------------------------------------------------------------------- #

def _initialize_wizard_with_draft() -> None:
    """Inicializa estado e tenta carregar rascunho do usuário, se houver."""
    initialize_wizard_state()
    try:
        current_user = st.session_state.get("authenticated_user")
        user_id = current_user.get("id") if isinstance(current_user, dict) else None
        loaded = load_wizard_draft(user_id=user_id)
        if loaded:
            st.sidebar.success("✅ Rascunho carregado automaticamente")
        else:
            st.sidebar.info("🆕 Iniciando novo projeto")
    except Exception as e:
        logger.error("Error loading wizard draft: %s", e, exc_info=True)


def _render_draft_controls() -> None:
    with st.sidebar.expander("💾 Gerenciar Rascunhos", expanded=False):
        col1, col2 = st.columns(2)
        if col1.button("💾 Salvar", help="Salvar rascunho manualmente"):
            st.success("✅ Rascunho salvo!" if save_wizard_draft() else "❌ Erro ao salvar")
        if col2.button("🆕 Novo", help="Começar novo projeto (limpar dados)"):
            for k in ("projeto_wizard_state", "current_step", "current_view", "wizard_draft_loaded"):
                st.session_state.pop(k, None)
            st.rerun()

        state = get_wizard_state()
        if state.last_saved:
            st.caption(f"💾 Última salvagem: {state.last_saved.strftime('%H:%M:%S')}")
        st.caption("⚠️ Alterações não salvas" if any(state.dirty_flags.values()) else "✅ Tudo salvo")


def render_debug_state() -> None:
    st.sidebar.markdown("### 🔧 Debug State")
    state = get_wizard_state()
    st.sidebar.write(f"**Current Step:** {int(state.current_step)}")
    st.sidebar.write(f"**Current View:** {state.current_view}")
    st.sidebar.write(f"**Epics Count:** {len(state.epics)}")
    st.sidebar.write(f"**Stories Count:** {len(state.stories)}")
    st.sidebar.write(f"**Tasks Count:** {len(state.tasks)}")
    st.sidebar.write(f"**Last Saved:** {state.last_saved}")

    st.sidebar.markdown("**Step Validation:**")
    for s in (Step.VISION, Step.EPICS, Step.STORIES, Step.TASKS, Step.PREVIEW):
        st.sidebar.write(f"Step {int(s)}: {'✅' if is_step_valid(int(s)) else '❌'}")

    if any(state.dirty_flags.values()):
        st.sidebar.warning("🔸 Unsaved changes")
    if has_validation_errors():
        st.sidebar.error("❌ Validation errors")


# --------------------------------------------------------------------------- #
# Função principal
# --------------------------------------------------------------------------- #

def render_projeto_wizard(auto_load_draft: bool = True) -> None:
    """
    Renderiza o wizard completo.
    """
    if auto_load_draft and not st.session_state.get("wizard_draft_loaded", False):
        _initialize_wizard_with_draft()
        st.session_state["wizard_draft_loaded"] = True
    else:
        initialize_wizard_state()

    _render_draft_controls()

    # container sem label vazio
    container = st.container()
    with container:
        projeto_wizard_header()
        st.divider()
        projeto_wizard_body()
        st.divider()
        projeto_wizard_footer()

    if st.sidebar.checkbox("🔧 Debug State", value=False):
        render_debug_state()
