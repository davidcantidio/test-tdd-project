"""Estado dos Capítulos - Gerenciamento de estado para macro etapa 2.

Este módulo fornece utilidades de gerenciamento de estado para
a etapa Capítulos do wizard genérico de projetos.

Components:
    - state_core.py: Definições centrais de estado
    - init_nav.py: Inicialização e navegação
"""

from .state_core import (
    CAP_FIELDS, init_cap_state, get_cap_state, add_capitulo, 
    remove_capitulo, validate_capitulo_data, is_capitulos_complete
)
from .init_nav import init_cap_navigation

__all__ = [
    'CAP_FIELDS', 'init_cap_state', 'get_cap_state', 'add_capitulo', 
    'remove_capitulo', 'validate_capitulo_data', 'is_capitulos_complete',
    'init_cap_navigation'
]