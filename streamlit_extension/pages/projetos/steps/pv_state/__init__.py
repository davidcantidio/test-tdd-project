"""
pv_state
========

Pacote que concentra o **estado e a navegação** do passo *Product Vision* no wizard.

Motivação da divisão
--------------------
Separar responsabilidades em módulos pequenos e testáveis:
- `state_core.py`         → metadados e estrutura de dados (DEFAULT_PV, PV_FIELDS)
- `init_nav.py`           → inicialização de estado e clamp do índice de passos
- `flow_order.py`         → ordem e navegação (next/prev, total_steps, is_review_step)
- `constraints_utils.py`  → utilidades de serialização de constraints

API pública
-----------
Este `__init__` reexporta a API usada pela UI, preservando compatibilidade
e facilitando os imports no resto do projeto.
"""

from .state_core import DEFAULT_PV, PV_FIELDS
from .init_nav import init_pv_state, clamp_pv_step_idx, set_pv_mode
from .flow_order import next_step, prev_step, total_steps, is_review_step

__all__ = [
    "DEFAULT_PV",
    "PV_FIELDS",
    "init_pv_state",
    "clamp_pv_step_idx",
    "set_pv_mode",
    "next_step",
    "prev_step",
    "total_steps",
    "is_review_step",
]
