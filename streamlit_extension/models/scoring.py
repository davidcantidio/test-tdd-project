#!/usr/bin/env python3
"""
🔧 MODELS - Task Scoring System

Sistema de pontuação configurável para priorização de tarefas.
Implementação baseada nas correções da crítica técnica.

Usage:
    from streamlit_extension.models.scoring import (
        calc_task_scores, 
        priority_tuple,
        TDD_BONUS_RED_FIRST
    )
    
Features:
- Pesos configuráveis externamente
- TDD scoring corrigido (RED > GREEN > REFACTOR)
- Value density calculation
- Tie-breakers determinísticos para heap
- Modular e testável
"""

from __future__ import annotations
from typing import Dict, Set, Optional
from dataclasses import dataclass

from .task_models import Task, TaskPriorityScore

# 🎛️ PESOS CONFIGURÁVEIS (tunable via environment/config)
W_PRIORITY = 10.0      # Prioridade explícita da tarefa (1=crítico, 5=backlog)
W_VALUE_DENSITY = 6.0  # Valor/esforço ratio
W_UNBLOCK = 3.0        # Quantas tarefas esta tarefa desbloqueia
W_CRITICAL_PATH = 2.0  # Posição no caminho crítico
W_TDD_BONUS = 1.0      # Bonus para tarefas TDD
W_AGING = 0.2          # Bonus por antiguidade (aging)

# 🔄 TDD SCORING CORRIGIDO - RED primeiro!
TDD_BONUS_RED_FIRST = {
    1: 3.0,  # RED = maior prioridade
    2: 2.0,  # GREEN = média prioridade  
    3: 1.0   # REFACTOR = menor prioridade
}

@dataclass
class ScoringWeights:
    """Configuração de pesos para scoring"""
    priority: float = W_PRIORITY
    value_density: float = W_VALUE_DENSITY
    unblock: float = W_UNBLOCK
    critical_path: float = W_CRITICAL_PATH
    tdd_bonus: float = W_TDD_BONUS
    aging: float = W_AGING

def task_effort_safe(task: Task) -> int:
    """
    Retorna esforço da tarefa com fallback consistente.
    Implementa correção da crítica para effort_estimate None.
    """
    return max(
        (getattr(task, "effort_estimate", None) or
         getattr(task, "estimate_minutes", None) or
         getattr(task, "story_points", None) or 1), 
        1  # Mínimo 1 para evitar divisão por zero
    )

def tdd_bonus_score(task: Task) -> float:
    """
    Calcula bonus TDD corrigido: RED > GREEN > REFACTOR.
    Correção da crítica - RED deve ter maior prioridade.
    """
    if task.tdd_order and task.tdd_order in TDD_BONUS_RED_FIRST:
        return TDD_BONUS_RED_FIRST[task.tdd_order]
    return 0.0

def value_density_score(task: Task) -> float:
    """
    Calcula densidade de valor: prioridade_invertida / esforço.
    Maior prioridade (1) = maior valor, menor esforço = maior densidade.
    """
    priority = max(1, min(5, task.priority or 3))  # Clamp 1-5
    priority_value = 6 - priority  # 1→5, 2→4, 3→3, 4→2, 5→1
    effort = task_effort_safe(task)
    
    return priority_value / effort

def unblock_score(task_key: str, adjacency: Dict[str, Set[str]]) -> float:
    """
    Calcula quantas tarefas esta tarefa desbloqueia.
    Tarefas que desbloqueiam muitas outras têm prioridade maior.
    """
    return float(len(adjacency.get(task_key, set())))

def critical_path_score(
    task_key: str, 
    critical_time: Dict[str, int], 
    critical_nodes: Set[str]
) -> float:
    """
    Calcula score do caminho crítico.
    Tarefas no caminho crítico têm prioridade máxima.
    """
    if not critical_time:
        return 0.0
        
    max_critical_time = max(critical_time.values())
    
    # Se está no caminho crítico, usar tempo crítico normalizado
    if task_key in critical_nodes:
        task_critical_time = critical_time.get(task_key, 0)
        return (task_critical_time / max_critical_time) * 10.0
    
    return 0.0

def aging_score(task: Task) -> float:
    """
    Calcula score de aging (antiguidade).
    TODO: Implementar cálculo real baseado em created_at.
    """
    # Placeholder - em implementação real, calcular dias desde criação
    if task.created_at:
        return 1.0
    return 0.0

def calc_task_scores(
    tasks: list[Task],
    adjacency: Dict[str, Set[str]],
    critical_time: Dict[str, int],
    critical_nodes: Set[str],
    weights: Optional[ScoringWeights] = None
) -> Dict[str, TaskPriorityScore]:
    """
    Calcula scores de prioridade para todas as tarefas.
    
    Args:
        tasks: Lista de tarefas para pontuar
        adjacency: Grafo de dependências {task_key: {dependent_tasks}}
        critical_time: Tempo crítico de cada tarefa
        critical_nodes: Set de tarefas no caminho crítico
        weights: Pesos customizados (opcional)
        
    Returns:
        Dict mapeando task_key para TaskPriorityScore
    """
    if weights is None:
        weights = ScoringWeights()
    
    scores = {}
    
    for task in tasks:
        task_key = task.task_key
        
        # Calcular scores individuais
        priority_score = 6 - (task.priority or 3)  # 1=5pts, 5=1pt
        value_density = value_density_score(task)
        unblock = unblock_score(task_key, adjacency)
        critical_path = critical_path_score(task_key, critical_time, critical_nodes)
        tdd_bonus = tdd_bonus_score(task)
        aging = aging_score(task)
        
        # Score total ponderado
        total_score = (
            weights.priority * priority_score +
            weights.value_density * value_density +
            weights.unblock * unblock +
            weights.critical_path * critical_path +
            weights.tdd_bonus * tdd_bonus +
            weights.aging * aging
        )
        
        scores[task_key] = TaskPriorityScore(
            task_key=task_key,
            total_score=total_score,
            priority_score=priority_score,
            value_density_score=value_density,
            unblock_score=unblock,
            critical_path_score=critical_path,
            tdd_bonus_score=tdd_bonus,
            aging_score=aging
        )
    
    return scores

def priority_tuple(task: Task, score: TaskPriorityScore) -> tuple:
    """
    Cria tupla de prioridade para heap com tie-breakers determinísticos.
    Implementa correção da crítica para heap instável.
    
    Returns:
        Tupla para heapq (min-heap): todos os valores invertidos para max-heap
        Ordem: score_total, priority, -effort, task_key
    """
    # heapq é min-heap, então invertemos sinais para comportamento max-heap
    return (
        -score.total_score,              # Maior score primeiro
        -(6 - (task.priority or 3)),     # Maior prioridade primeiro (1=crítico)
        task_effort_safe(task),          # Menor esforço primeiro (desempate)
        task.task_key                    # Ordem alfabética (determinística)
    )

def validate_scoring_monotonicity(tasks: list[Task]) -> Dict[str, bool]:
    """
    Valida monotonicidade do sistema de scoring.
    Para testes - garante que maior prioridade → maior score.
    """
    results = {}
    
    # Test value density monotonicity
    if len(tasks) >= 2:
        task_high_prio = next((t for t in tasks if t.priority == 1), None)
        task_low_prio = next((t for t in tasks if t.priority == 5), None)
        
        if task_high_prio and task_low_prio:
            high_density = value_density_score(task_high_prio)
            low_density = value_density_score(task_low_prio)
            results['value_density_monotonic'] = high_density > low_density
    
    # Test TDD bonus monotonicity  
    tdd_red = next((t for t in tasks if t.tdd_order == 1), None)
    tdd_refactor = next((t for t in tasks if t.tdd_order == 3), None)
    
    if tdd_red and tdd_refactor:
        red_bonus = tdd_bonus_score(tdd_red)
        refactor_bonus = tdd_bonus_score(tdd_refactor)
        results['tdd_bonus_red_first'] = red_bonus > refactor_bonus
    
    return results

# 🎯 PRESETS DE CONFIGURAÇÃO

SCORING_PRESET_BALANCED = ScoringWeights(
    priority=10.0,
    value_density=6.0,
    unblock=3.0,
    critical_path=2.0,
    tdd_bonus=1.0,
    aging=0.2
)

SCORING_PRESET_CRITICAL_PATH_FOCUS = ScoringWeights(
    priority=8.0,
    value_density=4.0,
    unblock=2.0,
    critical_path=10.0,  # Foco no caminho crítico
    tdd_bonus=1.0,
    aging=0.1
)

SCORING_PRESET_TDD_WORKFLOW = ScoringWeights(
    priority=6.0,
    value_density=3.0,
    unblock=2.0,
    critical_path=1.0,
    tdd_bonus=8.0,       # Foco no workflow TDD
    aging=0.1
)

SCORING_PRESET_BUSINESS_VALUE = ScoringWeights(
    priority=15.0,       # Foco na prioridade de negócio
    value_density=10.0,  # Foco no valor/esforço
    unblock=1.0,
    critical_path=1.0,
    tdd_bonus=0.5,
    aging=0.1
)

# 🎯 SISTEMA DE SCORING INTEGRADO

@dataclass
class ScoringPreset:
    """Preset de configuração de scoring"""
    name: str
    weights: ScoringWeights
    description: str = ""

class ScoringSystem:
    """
    Sistema de scoring integrado com presets configuráveis.
    Interface limpa para o TaskExecutionPlanner.
    """
    
    def __init__(self):
        self.presets = {
            "balanced": ScoringPreset(
                name="balanced",
                weights=SCORING_PRESET_BALANCED,
                description="Configuração balanceada para uso geral"
            ),
            "critical_path": ScoringPreset(
                name="critical_path", 
                weights=SCORING_PRESET_CRITICAL_PATH_FOCUS,
                description="Foco no caminho crítico"
            ),
            "tdd_workflow": ScoringPreset(
                name="tdd_workflow",
                weights=SCORING_PRESET_TDD_WORKFLOW, 
                description="Foco no workflow TDD (Red-Green-Refactor)"
            ),
            "business_value": ScoringPreset(
                name="business_value",
                weights=SCORING_PRESET_BUSINESS_VALUE,
                description="Foco no valor de negócio"
            )
        }
    
    def get_preset(self, preset_name: str) -> ScoringPreset:
        """
        Obtém preset de scoring por nome.
        
        Args:
            preset_name: Nome do preset
            
        Returns:
            ScoringPreset configurado
            
        Raises:
            ValueError: Se preset não existe
        """
        if preset_name not in self.presets:
            available = ", ".join(self.presets.keys())
            raise ValueError(f"Preset '{preset_name}' não existe. Disponíveis: {available}")
        
        return self.presets[preset_name]
    
    def calculate_score(self, task: Task, preset: ScoringPreset) -> float:
        """
        Calcula score de uma tarefa usando preset específico.
        
        Args:
            task: Tarefa para calcular score
            preset: Preset de configuração
            
        Returns:
            Score calculado
        """
        # Usar a função calc_task_scores existente mas com um único task
        adjacency = {}  # Não temos contexto de adjacência aqui
        scores = calc_task_scores([task], adjacency, preset.weights)
        
        # calc_task_scores retorna dict, pegar o score da nossa task
        return scores.get(task.task_key, 1.0)
    
    def list_presets(self) -> Dict[str, str]:
        """Lista presets disponíveis com descrições"""
        return {name: preset.description for name, preset in self.presets.items()}

# 📊 EXPORTAÇÕES
__all__ = [
    'calc_task_scores',
    'priority_tuple',
    'task_effort_safe',
    'tdd_bonus_score',
    'value_density_score',
    'ScoringWeights',
    'ScoringSystem',
    'ScoringPreset',
    'TDD_BONUS_RED_FIRST',
    'validate_scoring_monotonicity',
    'SCORING_PRESET_BALANCED',
    'SCORING_PRESET_CRITICAL_PATH_FOCUS', 
    'SCORING_PRESET_TDD_WORKFLOW',
    'SCORING_PRESET_BUSINESS_VALUE'
]