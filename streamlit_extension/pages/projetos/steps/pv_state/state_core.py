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
    "constraints": "",  # string field
}

#: Mapeamento das perguntas por etapa macro
QUESTIONS_BY_STEP = {
    1: [  # Etapa "O Quê"
        ("vision_statement", "O que você quer criar?"),
        ("problem_statement", "Qual problema isso resolve?"),
        ("target_audience", "Quem vai usar?"),
    ],
    2: [  # Etapa "Como" 
        ("value_proposition", "Como isso ajuda essa pessoa?"),
    ],
    3: [  # Etapa "Restrições"
        ("constraints", "O quê não pode ter, ou não pode faltar?"),
    ]
}

#: Ordem dos campos do fluxo step-by-step (tuplas: (chave, rótulo para UI))
PV_FIELDS = [
    ("vision_statement", "O que você quer criar?"),
    ("problem_statement", "Qual problema isso resolve?"),
    ("target_audience", "Quem vai usar?"),
    ("value_proposition", "Como isso ajuda essa pessoa?"),
    ("constraints", "O quê não pode ter, ou não pode faltar?"),
]
