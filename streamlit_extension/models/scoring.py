#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔧 MODELS - Task Scoring System

Sistema de pontuação configurável para priorização de tarefas.

Principais pontos:
- Pesos configuráveis e imutáveis por padrão
- TDD scoring corrigido (RED > GREEN > REFACTOR)
- Cálculo de value density e de desbloqueio (fan-out)
- Suporte a caminho crítico (tempo crítico + nós críticos)
- Tie-breakers determinísticos para heap (estável)
- API compatível com a versão anterior

Uso:
    from streamlit_extension.models.scoring import (
        calc_task_scores,
        priority_tuple,
        ScoringSystem,
        SCORING_PRESET_BALANCED,
    )
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Dict, Set, Optional, List, Tuple

from .task_models import Task, TaskPriorityScore

# 🎛️ PESOS PADRÃO (tunable via config/env)
W_PRIORITY = 10.0       # Prioridade explícita da tarefa (1=crítico, 5=backlog)
W_VALUE_DENSITY = 6.0   # Valor/esforço ratio
W_UNBLOCK = 3.0         # Quantas tarefas esta tarefa desbloqueia (fan-out)
W_CRITICAL_PATH = 2.0   # Posição no caminho crítico
W_TDD_BONUS = 1.0       # Bônus para tarefas TDD (pondera o tdd_order)
W_AGING = 0.2           # Bônus por “antiguidade” (aging)

# 🔄 TDD SCORING CORRIGIDO - RED primeiro!
TDD_BONUS_RED_FIRST: Dict[int, float] = {
    1: 3.0,  # RED = maior prioridade
    2: 2.0,  # GREEN = média
    3: 1.0,  # REFACTOR = menor
}


# =============================================================================
# Utilidades de cálculo
# =============================================================================

@dataclass(frozen=True)
class ScoringWeights:
    """Configuração de pesos para scoring (imutável por padrão)."""
    priority: float = W_PRIORITY
    value_density: float = W_VALUE_DENSITY
    unblock: float = W_UNBLOCK
    critical_path: float = W_CRITICAL_PATH
    tdd_bonus: float = W_TDD_BONUS
    aging: float = W_AGING


def task_effort_safe(task: Task) -> int:
    """
    Retorna esforço da tarefa com fallback consistente.
    - Garante mínimo 1 para evitar divisão por zero.
    """
    effort = (
        getattr(task, "effort_estimate", None)
        or getattr(task, "estimate_minutes", None)
        or getattr(task, "story_points", None)
        or 1
    )
    return max(int(effort), 1)


def tdd_bonus_score(task: Task) -> float:
    """
    Calcula bônus TDD corrigido (RED > GREEN > REFACTOR).
    """
    if getattr(task, "tdd_order", None) in TDD_BONUS_RED_FIRST:
        return TDD_BONUS_RED_FIRST[int(task.tdd_order)]
    return 0.0


def value_density_score(task: Task) -> float:
    """
    Densidade de valor: prioridade_invertida / esforço.
    - prioridade 1 → valor 5
    - prioridade 5 → valor 1
    """
    prio = max(1, min(5, getattr(task, "priority", 3) or 3))  # clamp 1..5
    prio_value = 6 - prio  # 1→5, 2→4, 3→3, 4→2, 5→1
    return prio_value / float(task_effort_safe(task))


def unblock_score(task_key: str, adjacency: Dict[str, Set[str]]) -> float:
    """
    Quantas tarefas esta tarefa desbloqueia (fan-out no grafo invertido).
    """
    return float(len(adjacency.get(task_key, set())))


def critical_path_score(
    task_key: str,
    critical_time: Dict[str, int],
    critical_nodes: Set[str],
) -> float:
    """
    Score de caminho crítico.
    - Se a tarefa está no caminho crítico, usa tempo crítico normalizado [0..10].
    - Caso contrário, 0.
    """
    if not critical_time:
        return 0.0

    max_ct = max(critical_time.values()) or 0
    if max_ct <= 0:
        return 0.0

    if task_key in critical_nodes:
        task_ct = critical_time.get(task_key, 0)
        return (task_ct / max_ct) * 10.0

    return 0.0


def aging_score(task: Task) -> float:
    """
    Score de aging (antiguidade).
    OBS: manter simples; cálculo real pode considerar dias desde created_at.
    """
    return 1.0 if getattr(task, "created_at", None) else 0.0


# =============================================================================
# Cálculo principal
# =============================================================================

def calc_task_scores(
    tasks: List[Task],
    adjacency: Dict[str, Set[str]],
    critical_time: Dict[str, int],
    critical_nodes: Set[str],
    weights: Optional[ScoringWeights] = None,
) -> Dict[str, TaskPriorityScore]:
    """
    Calcula scores de prioridade para todas as tarefas.

    Args:
        tasks: Lista de tarefas
        adjacency: Grafo de dependências invertido {task_key: {dependentes}}
        critical_time: Tempo crítico (distância) por tarefa
        critical_nodes: Conjunto de tarefas que compõem o caminho crítico
        weights: Pesos customizados (opcional)

    Returns:
        Dict mapeando task_key → TaskPriorityScore
    """
    w = weights or ScoringWeights()
    scores: Dict[str, TaskPriorityScore] = {}

    for task in tasks:
        tkey = task.task_key

        # Componentes individuais
        prio_score = 6 - (getattr(task, "priority", 3) or 3)  # 1=5pts, 5=1pt
        v_density = value_density_score(task)
        unblock = unblock_score(tkey, adjacency)
        cpath = critical_path_score(tkey, critical_time, critical_nodes)
        tdd = tdd_bonus_score(task)
        aging = aging_score(task)

        # Score ponderado
        total = (
            w.priority * prio_score
            + w.value_density * v_density
            + w.unblock * unblock
            + w.critical_path * cpath
            + w.tdd_bonus * tdd
            + w.aging * aging
        )

        scores[tkey] = TaskPriorityScore(
            task_key=tkey,
            total_score=float(total),
            priority_score=float(prio_score),
            value_density_score=float(v_density),
            unblock_score=float(unblock),
            critical_path_score=float(cpath),
            tdd_bonus_score=float(tdd),
            aging_score=float(aging),
        )

    return scores


def priority_tuple(task: Task, score: TaskPriorityScore) -> Tuple[float, float, int, str]:
    """
    Tupla de prioridade para uso em heap (min-heap do heapq).
    Inverte-se o sinal do total_score e da prioridade para simular max-heap.

    Ordem:
      1) -score.total_score        (maior score primeiro)
      2) -(6 - priority)           (prioridade 1 antes de 5)
      3) effort                    (menor esforço primeiro)
      4) task_key                  (ordem determinística alfabética)
    """
    prio = max(1, min(5, getattr(task, "priority", 3) or 3))
    return (
        -float(score.total_score),
        -(6 - prio),
        task_effort_safe(task),
        task.task_key,
    )


def validate_scoring_monotonicity(tasks: List[Task]) -> Dict[str, bool]:
    """
    Valida monotonicidade do sistema de scoring para testes simples.
    - Verifica se densidade de valor é maior para prioridade mais alta.
    - Verifica TDD RED > REFACTOR.
    """
    results: Dict[str, bool] = {}

    high = next((t for t in tasks if getattr(t, "priority", None) == 1), None)
    low = next((t for t in tasks if getattr(t, "priority", None) == 5), None)
    if high and low:
        results["value_density_monotonic"] = value_density_score(high) > value_density_score(low)

    red = next((t for t in tasks if getattr(t, "tdd_order", None) == 1), None)
    refactor = next((t for t in tasks if getattr(t, "tdd_order", None) == 3), None)
    if red and refactor:
        results["tdd_bonus_red_first"] = tdd_bonus_score(red) > tdd_bonus_score(refactor)

    return results


# =============================================================================
# Presets
# =============================================================================

SCORING_PRESET_BALANCED = ScoringWeights(
    priority=10.0,
    value_density=6.0,
    unblock=3.0,
    critical_path=2.0,
    tdd_bonus=1.0,
    aging=0.2,
)

SCORING_PRESET_CRITICAL_PATH_FOCUS = ScoringWeights(
    priority=8.0,
    value_density=4.0,
    unblock=2.0,
    critical_path=10.0,  # foco no caminho crítico
    tdd_bonus=1.0,
    aging=0.1,
)

SCORING_PRESET_TDD_WORKFLOW = ScoringWeights(
    priority=6.0,
    value_density=3.0,
    unblock=2.0,
    critical_path=1.0,
    tdd_bonus=8.0,  # foco TDD
    aging=0.1,
)

SCORING_PRESET_BUSINESS_VALUE = ScoringWeights(
    priority=15.0,      # foco na prioridade de negócio
    value_density=10.0, # valor/esforço
    unblock=1.0,
    critical_path=1.0,
    tdd_bonus=0.5,
    aging=0.1,
)


# =============================================================================
# Sistema de Scoring (interface para serviços)
# =============================================================================

@dataclass(frozen=True)
class ScoringPreset:
    """Preset de configuração de scoring (imutável)."""
    name: str
    weights: ScoringWeights
    description: str = ""


class ScoringSystem:
    """
    Sistema de scoring com presets configuráveis.
    - `get_preset` retorna cópias imutáveis (defensive copy).
    - `calculate_score` calcula o score de **uma** tarefa.
    """

    def __init__(self) -> None:
        self._presets: Dict[str, ScoringPreset] = {
            "balanced": ScoringPreset(
                name="balanced",
                weights=SCORING_PRESET_BALANCED,
                description="Configuração balanceada para uso geral",
            ),
            "critical_path": ScoringPreset(
                name="critical_path",
                weights=SCORING_PRESET_CRITICAL_PATH_FOCUS,
                description="Foco no caminho crítico",
            ),
            "tdd_workflow": ScoringPreset(
                name="tdd_workflow",
                weights=SCORING_PRESET_TDD_WORKFLOW,
                description="Foco no workflow TDD (Red-Green-Refactor)",
            ),
            "business_value": ScoringPreset(
                name="business_value",
                weights=SCORING_PRESET_BUSINESS_VALUE,
                description="Foco no valor de negócio",
            ),
        }

    def get_preset(self, preset_name: str) -> ScoringPreset:
        """
        Obtém preset por nome (cópia defensiva).
        Levanta ValueError se não existir.
        """
        if preset_name not in self._presets:
            available = ", ".join(self._presets.keys())
            raise ValueError(f"Preset '{preset_name}' não existe. Disponíveis: {available}")

        p = self._presets[preset_name]
        # defensive copy (mantém imutabilidade das instâncias originais)
        return ScoringPreset(
            name=p.name,
            weights=replace(p.weights),
            description=p.description,
        )

    def list_presets(self) -> Dict[str, str]:
        """Lista os presets disponíveis com descrição."""
        return {name: p.description for name, p in self._presets.items()}

    def calculate_score(self, task: Task, preset: ScoringPreset) -> float:
        """
        Calcula o score de uma tarefa usando um preset específico.
        - Usa contexto mínimo (sem adjacências / caminho crítico).
        - Mantém compatibilidade com `calc_task_scores`.
        """
        empty_adjacency: Dict[str, Set[str]] = {}
        empty_critical_time: Dict[str, int] = {}
        empty_critical_nodes: Set[str] = set()

        result = calc_task_scores(
            tasks=[task],
            adjacency=empty_adjacency,
            critical_time=empty_critical_time,
            critical_nodes=empty_critical_nodes,
            weights=preset.weights,
        )
        tkey = task.task_key
        if tkey in result:
            return float(result[tkey].total_score)
        # fallback seguro e explícito
        return 1.0


# 📊 EXPORTAÇÕES
__all__ = [
    "calc_task_scores",
    "priority_tuple",
    "task_effort_safe",
    "tdd_bonus_score",
    "value_density_score",
    "ScoringWeights",
    "ScoringSystem",
    "ScoringPreset",
    "TDD_BONUS_RED_FIRST",
    "validate_scoring_monotonicity",
    "SCORING_PRESET_BALANCED",
    "SCORING_PRESET_CRITICAL_PATH_FOCUS",
    "SCORING_PRESET_TDD_WORKFLOW",
    "SCORING_PRESET_BUSINESS_VALUE",
]
