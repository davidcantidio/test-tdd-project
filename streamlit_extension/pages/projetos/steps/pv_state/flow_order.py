"""
flow_order
==========

Funções relacionadas à **ordem e navegação** dos passos do fluxo step-by-step.

Conceito-chave
--------------
Existe um **passo adicional ao final** (índice `len(PV_FIELDS)`) que representa
a **revisão final** – o formulário completo com ações globais.
"""

from __future__ import annotations
from typing import Any

from .state_core import PV_FIELDS
from .init_nav import clamp_pv_step_idx  # import explícito para evitar ciclo


def next_step(ss: Any) -> None:
    """
    Avança `pv_step_idx` em +1, com *clamp*.

    Útil para o botão “Próximo ➡” no passo-a-passo.
    """
    ss["pv_step_idx"] += 1
    clamp_pv_step_idx(ss)


def prev_step(ss: Any) -> None:
    """
    Retrocede `pv_step_idx` em -1, com *clamp*.

    Útil para o botão “⬅ Anterior” no passo-a-passo.
    """
    ss["pv_step_idx"] -= 1
    clamp_pv_step_idx(ss)


def total_steps() -> int:
    """
    Retorna o total de passos **incluindo** o passo de revisão final.

    Exemplo: se há 5 campos, `total_steps()` retorna 6.
    """
    return len(PV_FIELDS) + 1


def is_review_step(ss: Any) -> bool:
    """
    Retorna `True` se `pv_step_idx` estiver no **passo de revisão final**.

    Isto sinaliza para a UI renderizar o **formulário completo** nesse passo.
    """
    return ss["pv_step_idx"] == len(PV_FIELDS)
