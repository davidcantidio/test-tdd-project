"""Estado central para Capítulos - Core state definitions.

Define a estrutura de dados e utilidades para gerenciar
o estado dos capítulos (épicos) no wizard genérico.
"""

from typing import Dict, Any, List, Optional
import streamlit as st


# Definições dos campos de Capítulos
CAP_FIELDS = [
    ("nome", "Como você chamaria esta grande divisão?"),
    ("descricao", "Descreva o que será feito neste capítulo"),
    ("prioridade", "Qual a prioridade deste capítulo?"),
    ("duracao_dias", "Quantos dias para completar?")
]


def init_cap_state(session_state) -> None:
    """Inicializa o estado dos capítulos no session_state.
    
    Args:
        session_state: Streamlit session state object
    """
    if not hasattr(session_state, 'capitulos'):
        session_state.capitulos = {
            'lista': [],  # Lista de capítulos criados
            'current': {  # Capítulo sendo editado
                'nome': '',
                'descricao': '',
                'prioridade': 3,
                'duracao_dias': 7
            },
            'editing_index': None,  # Índice do capítulo sendo editado (-1 = novo)
            'show_form': True  # Se mostra formulário ou apenas lista
        }


def get_cap_state(session_state) -> Dict[str, Any]:
    """Retorna o estado atual dos capítulos.
    
    Args:
        session_state: Streamlit session state object
        
    Returns:
        Dict com estado dos capítulos
    """
    if not hasattr(session_state, 'capitulos'):
        init_cap_state(session_state)
    return session_state.capitulos


def add_capitulo(session_state, capitulo_data: Dict[str, Any]) -> bool:
    """Adiciona um novo capítulo à lista.
    
    Args:
        session_state: Streamlit session state object
        capitulo_data: Dados do capítulo
        
    Returns:
        True se adicionado com sucesso
    """
    cap_state = get_cap_state(session_state)
    
    # Validação básica
    if not capitulo_data.get('nome', '').strip():
        return False
        
    # Gera epic_key único
    projeto_nome = getattr(session_state, 'pv', {}).get('vision_statement', 'PROJ')
    epic_key = _generate_epic_key(projeto_nome, len(cap_state['lista']) + 1)
    
    capitulo_completo = {
        'epic_key': epic_key,
        'nome': capitulo_data['nome'].strip(),
        'descricao': capitulo_data.get('descricao', '').strip(),
        'prioridade': int(capitulo_data.get('prioridade', 3)),
        'duracao_dias': int(capitulo_data.get('duracao_dias', 7)),
        'status': 'planejado'
    }
    
    cap_state['lista'].append(capitulo_completo)
    
    # Limpa o formulário atual
    cap_state['current'] = {
        'nome': '',
        'descricao': '',
        'prioridade': 3,
        'duracao_dias': 7
    }
    
    return True


def remove_capitulo(session_state, index: int) -> bool:
    """Remove um capítulo da lista.
    
    Args:
        session_state: Streamlit session state object
        index: Índice do capítulo a remover
        
    Returns:
        True se removido com sucesso
    """
    cap_state = get_cap_state(session_state)
    
    if 0 <= index < len(cap_state['lista']):
        cap_state['lista'].pop(index)
        return True
    return False


def get_capitulos_count(session_state) -> int:
    """Retorna o número de capítulos criados.
    
    Args:
        session_state: Streamlit session state object
        
    Returns:
        Número de capítulos
    """
    cap_state = get_cap_state(session_state)
    return len(cap_state['lista'])


def is_capitulos_complete(session_state) -> bool:
    """Verifica se a etapa capítulos está completa.
    
    Args:
        session_state: Streamlit session state object
        
    Returns:
        True se pelo menos um capítulo foi criado
    """
    return get_capitulos_count(session_state) > 0


def _generate_epic_key(projeto_nome: str, numero: int) -> str:
    """Gera uma chave épica única.
    
    Args:
        projeto_nome: Nome/visão do projeto
        numero: Número sequencial do capítulo
        
    Returns:
        Epic key no formato CAP-X
    """
    # Extrai primeiras letras do projeto para o prefixo
    if projeto_nome and len(projeto_nome.strip()) > 0:
        palavras = projeto_nome.strip().upper().split()[:2]
        prefixo = ''.join(p[0] for p in palavras if p and p[0].isalpha())
        if not prefixo:
            prefixo = "CAP"
    else:
        prefixo = "CAP"
        
    return f"{prefixo}-{numero}"


def validate_capitulo_data(data: Dict[str, Any]) -> tuple[bool, str]:
    """Valida os dados de um capítulo.
    
    Args:
        data: Dados do capítulo a validar
        
    Returns:
        Tupla (is_valid, error_message)
    """
    if not data.get('nome', '').strip():
        return False, "Nome do capítulo é obrigatório"
        
    if len(data['nome'].strip()) < 3:
        return False, "Nome deve ter pelo menos 3 caracteres"
        
    try:
        prioridade = int(data.get('prioridade', 3))
        if not (1 <= prioridade <= 5):
            return False, "Prioridade deve estar entre 1 e 5"
    except (ValueError, TypeError):
        return False, "Prioridade deve ser um número"
        
    try:
        duracao = int(data.get('duracao_dias', 7))
        if duracao < 1:
            return False, "Duração deve ser pelo menos 1 dia"
        if duracao > 365:
            return False, "Duração não pode exceder 365 dias"
    except (ValueError, TypeError):
        return False, "Duração deve ser um número de dias"
        
    return True, ""