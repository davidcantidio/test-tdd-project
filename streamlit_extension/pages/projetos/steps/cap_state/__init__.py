"""Estado dos Capítulos - Gerenciamento de estado para macro etapa 2.

Este módulo fornece utilidades de gerenciamento de estado para
a etapa Capítulos do wizard genérico de projetos.

Components:
    - state_core.py: Definições centrais de estado
    - init_nav.py: Inicialização e navegação
"""

from .state_core import CAP_FIELDS, init_cap_state
from .init_nav import init_cap_navigation

__all__ = ['CAP_FIELDS', 'init_cap_state', 'init_cap_navigation']