"""
POAgent — Agente Product Owner (Agno)

Regras:
- NUNCA faz perguntas ao usuário.
- NÃO inventa fatos; se faltar dado, mantém o conteúdo original e sinaliza avisos (externos ao texto).
- Refina textos em PT‑BR com clareza/concisão, sem alterar significado.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple


RefineWarnings = List[str]


@dataclass
class POAgent:
    model_id: str = "gpt-5-nano"

    def refine_field(self, field_key: str, value: str, context: Dict[str, Any]) -> Tuple[str, RefineWarnings]:
        """Refina um campo textual sem perguntar nada ao usuário.
        Retorna (novo_texto, warnings). Se faltarem dados, mantém texto e adiciona warning.
        """
        warnings: RefineWarnings = []
        text = (value or "").strip()
        if not text:
            warnings.append(f"Campo '{field_key}' vazio; mantendo conteúdo em branco.")
            return value, warnings

        # Aqui integraria o agente Agno real; placeholder não altera sem instrução clara
        refined = text  # No-op placeholder para manter política “sem perguntas”
        return refined, warnings

    def refine_all(self, pv: Dict[str, str]) -> Tuple[Dict[str, str], RefineWarnings]:
        """Refina todos os campos do Roteiro. Sem perguntas, sem fatos novos.
        Retorna (dados_refinados, warnings).
        """
        warnings: RefineWarnings = []
        refined = dict(pv)
        missing = [k for k, v in pv.items() if not isinstance(v, str) or not v.strip()]
        if missing:
            warnings.append(f"Campos obrigatórios ausentes: {', '.join(missing)}")
            # Política: manter original sem inventar.
        return refined, warnings

    def generate_epics(self, vision: Dict[str, str]) -> Tuple[List[Dict[str, Any]], RefineWarnings]:
        """Gera épicos mínimos (temp_key, name, description, dependencies, complexity_score, effort_estimate).
        Não faz perguntas; se a visão for insuficiente, retorna lista vazia e warning.
        """
        warnings: RefineWarnings = []
        required = ["vision_statement", "problem_statement", "target_audience", "value_proposition"]
        if any(not vision.get(k) for k in required):
            warnings.append("Visão insuficiente para gerar épicos. Preencha Roteiro.")
            return [], warnings

        # Placeholder determinístico mínimo: devolve estrutura vazia para orquestrador decidir
        return [], warnings

