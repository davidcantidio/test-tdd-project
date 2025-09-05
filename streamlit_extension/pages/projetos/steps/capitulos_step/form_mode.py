"""Modo formulário para Capítulos.

Implementa o modo formulário alternativo para criar capítulos,
seguindo padrões similares ao product_vision_step.
"""

from typing import Dict, Any
import streamlit as st

from ..cap_state import get_cap_state, add_capitulo, validate_capitulo_data


def render_capitulos_form_mode() -> None:
    """Renderiza o modo formulário para capítulos.
    
    Alternativa mais compacta ao modo principal, permitindo
    edição rápida de múltiplos capítulos.
    """
    st.markdown("#### 📋 Modo Formulário - Capítulos")
    
    cap_state = get_cap_state(st.session_state)
    
    # Formulário simplificado
    with st.form("capitulos_batch_form"):
        st.markdown("**Criar múltiplos capítulos rapidamente:**")
        
        # Área de texto para múltiplos capítulos
        capitulos_text = st.text_area(
            "Digite um capítulo por linha:",
            height=200,
            help="Exemplo:\nFundação e Estrutura\nSistemas Elétricos\nAcabamentos"
        )
        
        # Configurações padrão
        col1, col2 = st.columns(2)
        with col1:
            default_priority = st.slider("Prioridade padrão", 1, 5, 3)
        with col2:
            default_duration = st.number_input("Duração padrão (dias)", 1, 365, 7)
        
        submitted = st.form_submit_button(
            "📥 Criar Todos os Capítulos",
            type="primary"
        )
        
        if submitted and capitulos_text.strip():
            _process_batch_capitulos(
                capitulos_text, 
                default_priority, 
                default_duration
            )


def _process_batch_capitulos(text: str, priority: int, duration: int) -> None:
    """Processa criação em lote de capítulos."""
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    if not lines:
        st.warning("⚠️ Nenhum capítulo encontrado no texto.")
        return
    
    success_count = 0
    errors = []
    
    for i, line in enumerate(lines, 1):
        capitulo_data = {
            'nome': line,
            'descricao': f'Capítulo {i} - {line}',
            'prioridade': priority,
            'duracao_dias': duration
        }
        
        # Validação
        is_valid, error_msg = validate_capitulo_data(capitulo_data)
        if not is_valid:
            errors.append(f"Linha {i}: {error_msg}")
            continue
        
        # Adiciona
        if add_capitulo(st.session_state, capitulo_data):
            success_count += 1
        else:
            errors.append(f"Linha {i}: Erro ao adicionar '{line}'")
    
    # Feedback
    if success_count > 0:
        st.success(f"✅ {success_count} capítulo(s) criado(s) com sucesso!")
        
    if errors:
        st.error("❌ Alguns capítulos não puderam ser criados:")
        for error in errors[:5]:  # Mostra apenas primeiros 5 erros
            st.error(f"- {error}")
        if len(errors) > 5:
            st.error(f"... e mais {len(errors) - 5} erro(s)")
    
    if success_count > 0:
        st.rerun()