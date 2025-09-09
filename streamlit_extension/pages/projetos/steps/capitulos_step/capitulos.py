"""Interface principal da etapa Capítulos - Formulário vertical.

Implementa a interface de usuário para criar e gerenciar capítulos
(épicos) no framework genérico de projetos. Segue o padrão estabelecido
na Phase 4.7 com campos verticais (text_area 120px).
"""

from typing import Dict, Any, Optional
import streamlit as st
import logging

from ..cap_state import init_cap_state, get_cap_state, add_capitulo, remove_capitulo
from ..cap_state import validate_capitulo_data, is_capitulos_complete
from ..cap_state.init_nav import init_cap_navigation, update_navigation_state

logger = logging.getLogger(__name__)


def _cap_key(name: str) -> str:
    """Gera chave única para elementos dos capítulos."""
    session_id = st.session_state.get("session_id", "anon")
    return f"cap::{session_id}::2::{name}"


def render_capitulos_step() -> None:
    """Renderiza a etapa completa de Capítulos.
    
    Interface principal que combina formulário de criação com
    listagem e gerência dos capítulos já criados.
    """
    # Inicialização
    init_cap_state(st.session_state)
    init_cap_navigation(st.session_state)
    
    # Título da etapa
    st.markdown("### 📋 Capítulos - Grandes Divisões do Projeto")
    st.markdown(
        "*Capítulos são as grandes divisões que organizam seu projeto. "
        "Pense neles como os pilares principais que estruturam todo o trabalho.*"
    )
    
    # Exibe dados do Roteiro se disponíveis
    _show_roteiro_context()
    
    # Layout principal: formulário + lista
    col1, col2 = st.columns([1.2, 0.8])
    
    with col1:
        _render_capitulo_form()
    
    with col2:
        _render_capitulos_summary()
    
    # Navegação
    _render_navigation_buttons()
    
    # Atualiza estado de navegação
    update_navigation_state(st.session_state)


def _show_roteiro_context() -> None:
    """Mostra contexto do Roteiro (etapa anterior) se disponível."""
    if hasattr(st.session_state, 'pv'):
        pv = st.session_state.pv
        vision = pv.get('vision_statement', '')
        if vision:
            with st.expander("🎯 Roteiro do Projeto", expanded=False):
                st.markdown(f"**Visão:** {vision}")
                if pv.get('problem_statement'):
                    st.markdown(f"**Problema:** {pv['problem_statement']}")
                if pv.get('target_audience'):
                    st.markdown(f"**Público:** {pv['target_audience']}")


def _render_capitulo_form() -> None:
    """Renderiza o formulário para criar/editar capítulos."""
    cap_state = get_cap_state(st.session_state)
    
    st.markdown("#### ➕ Adicionar Novo Capítulo")
    
    with st.form(key=_cap_key("new_capitulo_form")):
        # Campo Nome (obrigatório)
        nome = st.text_area(
            "Como você chamaria esta grande divisão?",
            value=cap_state['current']['nome'],
            height=120,
            key=_cap_key("nome_input"),
            help="Ex: Fundação e Estrutura, Backend e APIs, Roteiro e Planejamento"
        )
        
        # Campo Descrição
        descricao = st.text_area(
            "Descreva o que será feito neste capítulo",
            value=cap_state['current']['descricao'],
            height=120,
            key=_cap_key("descricao_input"),
            help="Detalhe o escopo e principais atividades desta divisão"
        )
        
        # Campos numéricos em colunas
        col1, col2 = st.columns(2)
        
        with col1:
            prioridade = st.slider(
                "Qual a prioridade deste capítulo?",
                min_value=1,
                max_value=5,
                value=cap_state['current']['prioridade'],
                key=_cap_key("prioridade_slider"),
                help="1=Baixa, 3=Média, 5=Alta"
            )
        
        with col2:
            duracao_dias = st.number_input(
                "Quantos dias para completar?",
                min_value=1,
                max_value=365,
                value=cap_state['current']['duracao_dias'],
                key=_cap_key("duracao_input"),
                help="Estimativa em dias úteis"
            )
        
        # Botão de envio
        submitted = st.form_submit_button(
            "📋 Adicionar Capítulo",
            type="primary",
            use_container_width=True
        )
        
        if submitted:
            _handle_add_capitulo(nome, descricao, prioridade, duracao_dias)


def _handle_add_capitulo(nome: str, descricao: str, prioridade: int, duracao_dias: int) -> None:
    """Processa adição de um novo capítulo."""
    capitulo_data = {
        'nome': nome,
        'descricao': descricao,
        'prioridade': prioridade,
        'duracao_dias': duracao_dias
    }
    
    # Validação
    is_valid, error_msg = validate_capitulo_data(capitulo_data)
    if not is_valid:
        st.error(f"⚠️ {error_msg}")
        return
    
    # Adiciona o capítulo
    success = add_capitulo(st.session_state, capitulo_data)
    if success:
        st.success(f"✅ Capítulo '{nome}' adicionado com sucesso!")
        st.rerun()
    else:
        st.error("❌ Erro ao adicionar capítulo. Verifique os dados.")


def _render_capitulos_summary() -> None:
    """Renderiza o resumo dos capítulos já criados."""
    cap_state = get_cap_state(st.session_state)
    capitulos = cap_state['lista']
    
    st.markdown("#### 📊 Resumo dos Capítulos")
    
    if not capitulos:
        st.info("Nenhum capítulo criado ainda.")
        st.markdown(
            "*Adicione pelo menos um capítulo para prosseguir "
            "para a próxima etapa.*"
        )
        return
    
    st.markdown(f"**Total:** {len(capitulos)} capítulo(s)")
    
    # Lista dos capítulos
    for i, cap in enumerate(capitulos):
        with st.expander(f"**{cap['nome']}** ({cap['epic_key']})", expanded=False):
            if cap['descricao']:
                st.markdown(f"**Descrição:** {cap['descricao']}")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Prioridade", f"{cap['prioridade']}/5")
            with col2:
                st.metric("Duração", f"{cap['duracao_dias']} dias")
            with col3:
                st.metric("Status", cap['status'].title())
            
            # Botão de remoção
            if st.button(
                f"🗑️ Remover",
                key=_cap_key(f"remove_{i}"),
                type="secondary"
            ):
                if remove_capitulo(st.session_state, i):
                    st.success(f"Capítulo '{cap['nome']}' removido!")
                    st.rerun()
    
    # Estatísticas gerais
    if len(capitulos) > 1:
        st.markdown("---")
        total_dias = sum(cap['duracao_dias'] for cap in capitulos)
        prioridade_media = sum(cap['prioridade'] for cap in capitulos) / len(capitulos)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Duração Total", f"{total_dias} dias")
        with col2:
            st.metric("Prioridade Média", f"{prioridade_media:.1f}/5")


def _render_navigation_buttons() -> None:
    """Renderiza botões de navegação entre etapas."""
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.button("⬅️ Voltar para Roteiro", key=_cap_key("nav_back")):
            # Voltar para a etapa 1 (Roteiro)
            st.session_state.wizard_current_step = 1
            st.rerun()
    
    with col3:
        can_proceed = is_capitulos_complete(st.session_state)
        
        if can_proceed:
            if st.button(
                "Próximo: Histórias ➡️",
                key=_cap_key("nav_next"),
                type="primary"
            ):
                # Avançar para etapa 3 (Histórias)
                st.session_state.wizard_current_step = 3
                st.rerun()
        else:
            st.button(
                "Próximo: Histórias ➡️",
                key=_cap_key("nav_next_disabled"),
                disabled=True,
                help="Adicione pelo menos um capítulo para prosseguir"
            )
    
    with col2:
        if is_capitulos_complete(st.session_state):
            st.success("✅ Capítulos definidos! Pronto para prosseguir.")
        else:
            st.info("📝 Adicione capítulos para organizar seu projeto.")


def _render_debug_info() -> None:
    """Renderiza informações de debug (apenas em desenvolvimento)."""
    if st.sidebar.checkbox("Debug: Mostrar Estado", key=_cap_key("debug_toggle")):
        with st.sidebar.expander("Estado dos Capítulos"):
            st.json(get_cap_state(st.session_state))
        
        if st.sidebar.button("Reset Estado", key=_cap_key("debug_reset")):
            from ..cap_state.init_nav import reset_cap_state
            reset_cap_state(st.session_state)
            st.rerun()


# Função principal para exportação
def render_capitulos_step_main() -> None:
    """Ponto de entrada principal para a etapa Capítulos."""
    render_capitulos_step()
    
    # Debug em desenvolvimento
    if st.secrets.get("environment", "development") == "development":
        _render_debug_info()
