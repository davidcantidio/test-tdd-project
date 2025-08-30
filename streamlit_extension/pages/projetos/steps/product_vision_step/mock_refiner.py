# streamlit_extension/pages/projetos/steps/_mock_refiners.py
"""
Mock Vision Refine Service for development and testing.

This module provides optimized mock implementations of a VisionRefineService
until the real AI integration is completed in Phase 5.1.

Classes
-------
- MockVisionRefineService: full-payload refinement with deterministic output
- SingleFieldMockRefiner: refine a single field with context awareness
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import time
import random


# ----------------------------- Helpers --------------------------------- #

REQUIRED_FIELDS: List[str] = [
    "vision_statement",
    "problem_statement",
    "target_audience",
    "value_proposition",
    "constraints",
]


def _norm_str(val: Any) -> str:
    return val.strip() if isinstance(val, str) else ""


def _norm_constraints(val: Any) -> List[str]:
    if not isinstance(val, list):
        return []
    out: List[str] = []
    for item in val:
        if isinstance(item, str):
            s = item.strip()
            if s:
                out.append(s)
    return out


def _ensure_period(s: str) -> str:
    return s if not s or s[-1] in ".!?;" else s + "."


def _capitalize(s: str) -> str:
    return s if not s else s[0].upper() + s[1:]


def _seed_random(seed: Optional[int]) -> None:
    if seed is not None:
        random.seed(seed)


# ----------------------- Mock Service (Optimized) ----------------------- #

@dataclass
class MockVisionRefineConfig:
    """Configurações para controlar o comportamento do mock refiner."""
    simulate_latency: bool = True
    latency_seconds: float = 0.35
    deterministic_seed: Optional[int] = 42  # defina None para comportamento não determinístico
    auto_suggest_constraints: bool = True
    max_auto_constraints: int = 1  # quantas sugestões extras injetar no máximo


class MockVisionRefineService:
    """
    Mock implementation of VisionRefineService for development.

    - Determinístico por padrão (seed fixo), evitando flakiness em testes.
    - Latência simulada configurável para aproximar experiência real de IA.
    - Normalização de payload, garantindo tipos consistentes.
    - Lógica de “refino” simples e previsível.
    """

    def __init__(self, agent: Any = None, config: Optional[MockVisionRefineConfig] = None):
        self.agent = agent  # mantido para compatibilidade de construtor
        self.config = config or MockVisionRefineConfig()

    # -------------------------- API principal --------------------------- #

    def refine(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simula o refino de IA com normalização e melhorias simples.

        Args:
            payload: dicionário com os campos de visão de produto.

        Returns:
            dict parcialmente/totalmente refinado (mantém chaves requeridas).
        """
        _seed_random(self.config.deterministic_seed)
        if self.config.simulate_latency and self.config.latency_seconds > 0:
            # Pequeno “jitter” determinístico para parecer mais real
            base = self.config.latency_seconds
            time.sleep(base + (0.0 if self.config.deterministic_seed is not None else random.uniform(0, 0.15)))

        pv = self._normalize_payload(payload)
        result: Dict[str, Any] = {}

        # --- Vision Statement ---
        vs = pv["vision_statement"]
        if vs:
            refined = _ensure_period(vs)
            if len(refined) < 100 and not refined.lower().startswith("nossa visão é"):
                refined = f"Nossa visão é {refined.lower()}"
            result["vision_statement"] = refined

        # --- Problem Statement ---
        ps = pv["problem_statement"]
        if ps:
            refined = ps
            if "problema" not in refined.lower():
                refined = f"O problema principal é: {refined}"
            refined = _ensure_period(refined)
            result["problem_statement"] = refined

        # --- Target Audience ---
        ta = pv["target_audience"]
        if ta:
            refined = ta
            if len(refined.split()) < 5 and "soluções" not in refined.lower():
                refined = f"{refined} que buscam soluções inovadoras"
            result["target_audience"] = refined

        # --- Value Proposition ---
        vp = pv["value_proposition"]
        if vp:
            refined = vp
            if "oferecemos" not in refined.lower() and "oferecer" not in refined.lower():
                refined = f"Oferecemos {refined.lower()}"
            refined = _ensure_period(refined)
            result["value_proposition"] = refined

        # --- Constraints ---
        cons = pv["constraints"]
        refined_constraints: List[str] = []
        for c in cons:
            c_ref = _capitalize(c)
            c_ref = _ensure_period(c_ref)
            refined_constraints.append(c_ref)

        if self.config.auto_suggest_constraints and len(refined_constraints) < 3:
            suggestions = [
                "Prazo de entrega deve ser cumprido rigorosamente.",
                "Orçamento limitado requer otimização de recursos.",
                "Conformidade com regulamentações do setor.",
            ]
            # Inserir no máximo N sugestões, sem duplicar
            to_add = max(0, min(self.config.max_auto_constraints, 3 - len(refined_constraints)))
            for s in suggestions:
                if to_add <= 0:
                    break
                if s not in refined_constraints:
                    refined_constraints.append(s)
                    to_add -= 1

        result["constraints"] = refined_constraints

        # Garantir presença de todos os campos requeridos (pass-through se necessário)
        for field in REQUIRED_FIELDS:
            if field not in result:
                result[field] = pv[field]

        return result

    # -------------------------- Internals ------------------------------- #

    def _normalize_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Garante tipos e chaves esperadas para o processamento."""
        pv: Dict[str, Any] = {}
        pv["vision_statement"] = _norm_str(payload.get("vision_statement"))
        pv["problem_statement"] = _norm_str(payload.get("problem_statement"))
        pv["target_audience"] = _norm_str(payload.get("target_audience"))
        pv["value_proposition"] = _norm_str(payload.get("value_proposition"))
        pv["constraints"] = _norm_constraints(payload.get("constraints"))
        return pv


# --------------------- Single-field Context Refiner --------------------- #

class SingleFieldMockRefiner:
    """
    Mock refiner otimizado para refino de um único campo com contexto.

    Uso típico no modo “steps”: ao focar em um campo, o refino considera
    o restante do payload para manter coerência, mas retorna apenas o valor
    do campo alvo.
    """

    def __init__(self, service: Optional[MockVisionRefineService] = None):
        self.service = service or MockVisionRefineService()

    def refine_field(self, field_key: str, field_value: Any, context: Dict[str, Any]) -> Any:
        """
        Refina um campo específico usando o contexto completo.

        Args:
            field_key: chave do campo a refinar (ex.: "vision_statement")
            field_value: valor atual do campo
            context: payload completo com demais campos

        Returns:
            Valor refinado do campo (ou o original, se não houver melhoria).
        """
        payload = dict(context or {})
        payload[field_key] = field_value
        refined = self.service.refine(payload)
        return refined.get(field_key, field_value)
