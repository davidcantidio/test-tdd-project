"""
DevTeamAgent — Agente do Time de Desenvolvimento (Agno)

Regras:
- NUNCA pergunta ao usuário.
- Converte entradas do PO em artefatos técnicos testáveis (INVEST) sem inventar escopo.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple


RefineWarnings = List[str]


@dataclass
class DevTeamAgent:
    model_id: str = "gpt-5-nano"

    def generate_user_stories(self, epics: List[Dict[str, Any]], po_inputs: Dict[str, Any] | None = None) -> Tuple[List[Dict[str, Any]], RefineWarnings]:
        warnings: RefineWarnings = []
        if not epics:
            warnings.append("Sem épicos aprovados para gerar histórias.")
            return [], warnings
        # Placeholder: retorno vazio controlado, sem perguntas
        return [], warnings

    def generate_tasks(self, user_story: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], RefineWarnings]:
        warnings: RefineWarnings = []
        if not user_story:
            warnings.append("História vazia para detalhar tarefas.")
            return [], warnings
        # Placeholder: retorno vazio controlado, sem perguntas
        return [], warnings

