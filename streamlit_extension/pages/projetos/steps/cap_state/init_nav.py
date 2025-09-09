"""
🧭 Navigation Integration - História 4.1 FASE 2.4

Funções de navegação para integração com wizard:
- Step visibility gating 
- Available steps calculation
- Navigation flow control

Implementação TDD seguindo metodologia Green-phase.
"""

from typing import List, Dict, Any, Optional


def should_show_epic_review_step(session_state) -> bool:
    """
    Determina se step de epic review deve ser mostrado.
    
    Critérios:
    - Deve haver capítulos criados
    - Capítulos não devem estar finalizados
    - Lista não deve estar vazia
    """
    # Verificar se há capítulos
    if not hasattr(session_state, 'cap') or not session_state.cap.get('lista'):
        return False
    
    # Se lista está vazia, não mostrar
    if len(session_state.cap['lista']) == 0:
        return False
    
    # Se capítulos já foram finalizados, não mostrar
    if session_state.cap.get('finalized', False):
        return False
    
    return True


def get_available_steps(session_state) -> List[str]:
    """
    Retorna lista de steps disponíveis baseado no estado atual.
    
    Steps possíveis:
    - roteiro (sempre disponível)
    - capitulos (sempre disponível)
    - epic_review (condicional)
    - historias (se review completa)
    - tarefas (se histórias completas)
    """
    available_steps = ["roteiro", "capitulos"]
    
    # Epic review disponível se há capítulos
    if should_show_epic_review_step(session_state):
        available_steps.append("epic_review")
    
    # Histórias disponível se epic review está completo
    if _is_epic_review_complete(session_state):
        available_steps.append("historias")
    
    # Tarefas disponível se histórias estão completas
    if _are_historias_complete(session_state):
        available_steps.append("tarefas")
    
    return available_steps


def _is_epic_review_complete(session_state) -> bool:
    """Verifica se epic review foi completado"""
    # Se não deve mostrar epic review, considera completo
    if not should_show_epic_review_step(session_state):
        return False
    
    # Verificar se há estado de review
    if not hasattr(session_state, 'epic_review_state') or not session_state.epic_review_state:
        return False
    
    # Verificar se não há mudanças pendentes
    from streamlit_extension.pages.projetos.steps.capitulos_step.epic_review import EpicReviewPage
    try:
        review_page = EpicReviewPage(session_state)
        return not review_page.has_unsaved_changes()
    except Exception:
        # Se falhar ao criar página, considerar não completo
        return False


def _are_historias_complete(session_state) -> bool:
    """Verifica se histórias foram completadas"""
    # Placeholder - implementação futura
    return hasattr(session_state, 'historias_complete') and session_state.historias_complete


def get_current_step_info(session_state) -> Dict[str, Any]:
    """
    Retorna informações sobre o step atual.
    
    Returns:
        Dict com informações do step: name, title, progress, etc.
    """
    current_step = getattr(session_state, 'wizard_current_step', 1)
    
    step_info = {
        1: {
            "name": "roteiro", 
            "title": "Roteiro do Projeto",
            "description": "Definir visão e objetivos",
            "progress": 100 if hasattr(session_state, 'roteiro_complete') else 0
        },
        2: {
            "name": "capitulos",
            "title": "Capítulos",
            "description": "Estruturar grandes marcos",
            "progress": 100 if should_show_epic_review_step(session_state) else 0
        },
        2.5: {
            "name": "epic_review",
            "title": "Revisão de Capítulos", 
            "description": "Revisar e reordenar épicos",
            "progress": 100 if _is_epic_review_complete(session_state) else 50
        },
        3: {
            "name": "historias",
            "title": "Histórias",
            "description": "Detalhar narrativas específicas", 
            "progress": 100 if _are_historias_complete(session_state) else 0
        },
        4: {
            "name": "tarefas",
            "title": "Tarefas",
            "description": "Executar ações específicas",
            "progress": 0
        }
    }
    
    return step_info.get(current_step, {
        "name": "unknown",
        "title": "Unknown Step",
        "description": "",
        "progress": 0
    })


def can_navigate_to_step(session_state, target_step: float) -> bool:
    """
    Verifica se é possível navegar para um step específico.
    
    Args:
        session_state: Estado da sessão
        target_step: Step alvo (1, 2, 2.5, 3, 4)
    
    Returns:
        True se navegação é permitida
    """
    available_steps = get_available_steps(session_state)
    
    step_mapping = {
        1: "roteiro",
        2: "capitulos", 
        2.5: "epic_review",
        3: "historias",
        4: "tarefas"
    }
    
    target_name = step_mapping.get(target_step)
    if not target_name:
        return False
    
    return target_name in available_steps


def get_next_available_step(session_state) -> Optional[float]:
    """
    Retorna o próximo step disponível para navegação.
    
    Returns:
        Número do próximo step ou None se já está no último
    """
    current_step = getattr(session_state, 'wizard_current_step', 1)
    available_steps = get_available_steps(session_state)
    
    step_sequence = [1, 2, 2.5, 3, 4]
    step_mapping = {
        1: "roteiro",
        2: "capitulos",
        2.5: "epic_review", 
        3: "historias",
        4: "tarefas"
    }
    
    # Encontrar próximo step na sequência que está disponível
    current_index = step_sequence.index(current_step) if current_step in step_sequence else 0
    
    for step in step_sequence[current_index + 1:]:
        step_name = step_mapping[step]
        if step_name in available_steps:
            return step
    
    return None


def get_previous_available_step(session_state) -> Optional[float]:
    """
    Retorna o step anterior disponível para navegação.
    
    Returns:
        Número do step anterior ou None se já está no primeiro
    """
    current_step = getattr(session_state, 'wizard_current_step', 1)
    
    step_sequence = [1, 2, 2.5, 3, 4]
    
    # Encontrar step anterior na sequência
    current_index = step_sequence.index(current_step) if current_step in step_sequence else 0
    
    if current_index > 0:
        return step_sequence[current_index - 1]
    
    return None


# Legacy functions for backward compatibility
def init_cap_navigation(session_state) -> None:
    """Inicializa navegação de capítulos (compatibilidade)"""
    # Placeholder para compatibilidade com sistema existente
    if not hasattr(session_state, 'cap_nav'):
        session_state.cap_nav = {
            'initialized': True,
            'can_proceed': False,
            'came_from_roteiro': True,
            'show_success_message': False
        }


def update_navigation_state(session_state) -> None:
    """Atualiza estado de navegação (compatibilidade)"""
    # Placeholder para compatibilidade com sistema existente
    if hasattr(session_state, 'cap_nav'):
        session_state.cap_nav['can_proceed'] = should_show_epic_review_step(session_state)