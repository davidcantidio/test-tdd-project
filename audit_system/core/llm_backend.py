# -*- coding: utf-8 -*-
"""
LLM Backend Interface (real ou nulo)
------------------------------------
Fornece um ponto único de integração para provedores LLM reais.
Se não houver backend configurado, usamos NullLLMBackend (modo dry-run)
sem métricas falsas e sem modificar arquivos.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple


@dataclass
class LLMOverview:
    overall_purpose: str
    architectural_role: str
    risks: List[str]
    notes: List[str]
    # Sem score fixo; se um provedor real devolver, use-o explicitamente
    confidence_score: Optional[float] = None


class LLMBackend:
    """Interface mínima para acoplamento fraco com provedores reais."""
    def file_overview(self, *, content: str, file_path: str, ast_tree: Any | None) -> LLMOverview:
        raise NotImplementedError

    def line_batch_analysis(
        self, *, content: str, file_path: str, ast_tree: Any | None, line_batch: Iterable[Tuple[int, str]]
    ) -> List[Dict[str, Any]]:
        raise NotImplementedError


class NullLLMBackend(LLMBackend):
    """Backend nulo: não inventa números, apenas devolve texto honesto e não destrutivo."""
    def file_overview(self, *, content: str, file_path: str, ast_tree: Any | None) -> LLMOverview:
        return LLMOverview(
            overall_purpose="Dry-run: visão de arquivo baseada em heurísticas locais (sem LLM).",
            architectural_role="desconhecido",
            risks=[],
            notes=["LLM não configurado: nenhuma inferência externa executada.", "Sem métricas/‘scores’ artificiais."],
            confidence_score=None,
        )

    def line_batch_analysis(
        self, *, content: str, file_path: str, ast_tree: Any | None, line_batch: Iterable[Tuple[int, str]]
    ) -> List[Dict[str, Any]]:
        # Retorna estrutura mínima sem “scores” mágicos.
        return [
            {
                "line": ln,
                "purpose": "Dry-run: heurística local",
                "semantic_type": "unknown",
                "notes": ["LLM não configurado"],
                "confidence": None,
            }
            for ln, _ in line_batch
        ]
