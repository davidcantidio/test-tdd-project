"""Inicialização e navegação para Capítulos.

Fornece utilidades para inicializar o estado de navegação
e gerenciar transições na etapa Capítulos.
"""

import streamlit as st
from .state_core import init_cap_state


def init_cap_navigation(session_state) -> None:
    """Inicializa a navegação para capítulos.
    
    Args:
        session_state: Streamlit session state object
    """
    # Inicializa estado dos capítulos se necessário
    init_cap_state(session_state)
    
    # Configura flags de navegação
    if not hasattr(session_state, 'cap_nav'):
        session_state.cap_nav = {
            'initialized': True,
            'can_proceed': False,  # Pode prosseguir para próxima etapa
            'came_from_roteiro': True,  # Veio da etapa anterior
            'show_success_message': False
        }


def can_proceed_to_next(session_state) -> bool:
    """Verifica se pode prosseguir para a próxima etapa.
    
    Args:
        session_state: Streamlit session state object
        
    Returns:
        True se pode prosseguir
    """
    # Precisa ter pelo menos um capítulo criado
    if not hasattr(session_state, 'capitulos'):
        return False
        
    capitulos = getattr(session_state, 'capitulos', {})
    return len(capitulos.get('lista', [])) > 0


def update_navigation_state(session_state) -> None:
    """Atualiza o estado de navegação baseado no progresso atual.
    
    Args:
        session_state: Streamlit session state object
    """
    if not hasattr(session_state, 'cap_nav'):
        init_cap_navigation(session_state)
        
    session_state.cap_nav['can_proceed'] = can_proceed_to_next(session_state)


def reset_cap_state(session_state) -> None:
    """Reseta o estado dos capítulos (para desenvolvimento/teste).
    
    Args:
        session_state: Streamlit session state object
    """
    if hasattr(session_state, 'capitulos'):
        delattr(session_state, 'capitulos')
    if hasattr(session_state, 'cap_nav'):
        delattr(session_state, 'cap_nav')
        
    # Reinicializa
    init_cap_navigation(session_state)