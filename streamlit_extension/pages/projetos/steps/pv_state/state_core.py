"""
state_core
==========

Metadados e estrutura de dados do *Product Vision*.

O que fica aqui:
- `DEFAULT_PV`: dicionário com o estado inicial válido.
- `PV_FIELDS`: ordem canônica dos campos para o fluxo step-by-step.
"""

from __future__ import annotations
from typing import Any, Dict

#: Estado padrão do Product Vision (imutável no sentido de contrato — use cópias)
DEFAULT_PV: Dict[str, Any] = {
    "vision_statement": "",
    "problem_statement": "",
    "target_audience": "",
    "value_proposition": "",
    "constraints": [],  # list[str]
}

#: Ordem dos campos do fluxo step-by-step (tuplas: (chave, rótulo para UI))
PV_FIELDS = [
    ("vision_statement", "Declaração de Visão"),
    ("problem_statement", "Problema a Resolver"),
    ("target_audience", "Público-alvo"),
    ("value_proposition", "Proposta de Valor"),
    ("constraints", "Restrições (uma por linha)"),
]
