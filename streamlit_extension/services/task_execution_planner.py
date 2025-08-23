#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎯 SERVICES - Task Execution Planner (otimizado)

Sistema de ordenação topológica e priorização de tarefas baseado em DAG.
Implementação refatorada para componentes limpos, determinismo nos empates e
reuso consistente do grafo invertido.

Usage:
    from streamlit_extension.services.task_execution_planner import TaskExecutionPlanner

    planner = TaskExecutionPlanner(db_connection)
    result = planner.plan_execution(epic_id=1, scoring_preset="balanced")

Features:
- ✅ Ordenação topológica (Kahn) com priorização via heap (tie-breaks estáveis)
- ✅ Sistema de scoring configurável (presets + override de pesos)
- ✅ Validação de DAG e detecção de ciclos (GraphAlgorithms)
- ✅ Repository pattern (TasksRepo / DepsRepo)
- ✅ Error handling com ServiceResult
- ✅ Métricas consolidadas do plano
"""

from __future__ import annotations

import heapq
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from collections import defaultdict

from ..repos.tasks_repo import TasksRepo, RepoError
from ..repos.deps_repo import DepsRepo
from ..models.task_models import Task, TaskDependency
from ..models.scoring import ScoringSystem, ScoringPreset
from ..utils.graph_algorithms import GraphAlgorithms
from ..services.base import BaseService, ServiceResult

logger = logging.getLogger(__name__)


# ============================================================================ #
# DTOs
# ============================================================================ #

@dataclass
class ExecutionPlan:
    """Resultado do planejamento de execução."""
    epic_id: int
    execution_order: List[str]
    task_scores: Dict[str, float]
    critical_path: List[str]
    execution_metrics: Dict[str, Any]
    dag_validation: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class PlanningContext:
    """Contexto interno para planejamento."""
    tasks: List[Task]
    dependencies: List[TaskDependency]
    # adjacency_graph: task_key -> {prerequisite_task_key, ...}
    adjacency_graph: Dict[str, Set[str]]
    # inverted_graph: prerequisite_task_key -> {dependent_task_key, ...}
    inverted_graph: Dict[str, Set[str]]
    task_weights: Dict[str, int]
    task_metadata: Dict[str, Dict[str, Any]]


# ============================================================================ #
# Serviço
# ============================================================================ #

class TaskExecutionPlanner(BaseService):
    """
    Planejador de execução de tarefas com ordenação topológica e priorização.

    Integra:
    - TasksRepo / DepsRepo (acesso a dados)
    - ScoringSystem (priorização configurável)
    - GraphAlgorithms (validação DAG / caminho crítico)
    """

    def __init__(self, connection):
        """
        Args:
            connection: Objeto de conexão de banco.
        """
        super().__init__()
        self.connection = connection
        self.tasks_repo = TasksRepo(connection)
        self.deps_repo = DepsRepo(connection)
        self.scoring_system = ScoringSystem()

    # --------------------------------------------------------------------- #
    # Orquestração
    # --------------------------------------------------------------------- #

    def plan_execution(
        self,
        epic_id: int,
        scoring_preset: str = "balanced",
        custom_weights: Optional[Dict[str, float]] = None,
    ) -> ServiceResult[ExecutionPlan]:
        """
        Planeja execução de tarefas com ordenação topológica e priorização.

        Args:
            epic_id: ID do épico
            scoring_preset: "balanced" | "critical_path" | "tdd_workflow" | "business_value"
            custom_weights: pesos customizados para sobrescrever preset

        Returns:
            ServiceResult contendo ExecutionPlan ou erros.
        """
        try:
            self._log_operation_start(
                "plan_execution",
                {"epic_id": epic_id, "preset": scoring_preset},
            )

            # 1) Validação de inputs
            validation_result = self._validate_planning_inputs(epic_id, scoring_preset)
            if not validation_result.success:
                return validation_result

            # 2) Carregar contexto (tarefas, deps, grafos, pesos, metadados)
            ctx_result = self._load_planning_context(epic_id)
            if not ctx_result.success:
                return ctx_result
            context = ctx_result.data

            # 3) Validar DAG
            dag_validation = self._validate_dag_structure(context)
            if not dag_validation["is_valid"]:
                return ServiceResult.validation_error(
                    f"DAG inválido para épico {epic_id}: {dag_validation['error']}"
                )

            # 4) Configurar Scoring
            scoring_cfg_res = self._configure_scoring_system(scoring_preset, custom_weights)
            if not scoring_cfg_res.success:
                return scoring_cfg_res
            scoring_cfg = scoring_cfg_res.data

            # 5) Pontuar tarefas
            task_scores = self._calculate_task_scores(context, scoring_cfg)

            # 6) Ordenação topológica com prioridade (usa inverted_graph do contexto)
            execution_order = self._topological_sort_with_priority(context, task_scores)

            # 7) Caminho crítico (usa mesmo grafo invertido + pesos)
            critical_path = self._calculate_critical_path(context)

            # 8) Métricas
            execution_metrics = self._calculate_execution_metrics(context, task_scores, execution_order)

            # 9) Montar plano
            plan = ExecutionPlan(
                epic_id=epic_id,
                execution_order=execution_order,
                task_scores=task_scores,
                critical_path=critical_path,
                execution_metrics=execution_metrics,
                dag_validation=dag_validation,
            )

            logger.info(
                "Plano de execução criado (epic_id=%s): %s tarefas.",
                epic_id,
                len(execution_order),
            )
            return ServiceResult.ok(plan)

        except Exception as e:
            logger.exception("Falha no planejamento de execução (epic_id=%s): %s", epic_id, e)
            return ServiceResult.validation_error(f"Falha no planejamento: {str(e)}")

    # --------------------------------------------------------------------- #
    # Carregamento e validações
    # --------------------------------------------------------------------- #

    def _validate_planning_inputs(self, epic_id: int, scoring_preset: str) -> ServiceResult[bool]:
        errors: List[str] = []

        if not isinstance(epic_id, int) or epic_id <= 0:
            errors.append(f"epic_id deve ser inteiro positivo, recebido: {epic_id}")

        valid_presets = {"balanced", "critical_path", "tdd_workflow", "business_value"}
        if scoring_preset not in valid_presets:
            errors.append(f"scoring_preset inválido: {scoring_preset}. Válidos: {valid_presets}")

        if errors:
            return ServiceResult.validation_error("; ".join(errors))
        return ServiceResult.ok(True)

    def _load_planning_context(self, epic_id: int) -> ServiceResult[PlanningContext]:
        """Carrega tarefas/dependências e constrói grafos + metadados."""
        try:
            tasks = self.tasks_repo.list_by_epic(epic_id)
            if not tasks:
                return ServiceResult.not_found("tasks", f"epic_id={epic_id}")

            dependencies = self.deps_repo.list_by_epic(epic_id)

            adjacency = self._build_adjacency_graph(tasks, dependencies)
            inverted = self._build_inverted_graph(adjacency)

            task_weights = {
                t.task_key: max(t.estimate_minutes or 60, 1)  # mínimo 1 min
                for t in tasks
            }
            task_metadata = {
                t.task_key: {
                    "id": t.id,
                    "title": t.title,
                    "tdd_phase": t.tdd_phase,
                    "tdd_order": t.tdd_order,
                    "priority": t.priority,
                    "story_points": t.story_points,
                    "task_type": t.task_type,
                    "status": t.status,
                    "task_group": t.task_group,
                    "task_sequence": t.task_sequence,
                }
                for t in tasks
            }

            ctx = PlanningContext(
                tasks=tasks,
                dependencies=dependencies,
                adjacency_graph=adjacency,
                inverted_graph=inverted,
                task_weights=task_weights,
                task_metadata=task_metadata,
            )
            return ServiceResult.ok(ctx)

        except RepoError as e:
            return ServiceResult.validation_error(f"Erro no repository: {e}")
        except Exception as e:
            return ServiceResult.validation_error(f"Erro ao carregar contexto: {e}")

    @staticmethod
    def _build_adjacency_graph(
        tasks: List[Task],
        dependencies: List[TaskDependency],
    ) -> Dict[str, Set[str]]:
        """
        Constrói grafo de adjacência (task -> prerequisites).
        """
        adjacency: Dict[str, Set[str]] = {t.task_key: set() for t in tasks}

        for dep in dependencies:
            # Esperado: dep.dependent_task_key depende de dep.depends_on_task_key
            if getattr(dep, "dependent_task_key", None) and getattr(dep, "depends_on_task_key", None):
                dependent = dep.dependent_task_key
                prerequisite = dep.depends_on_task_key
                if dependent in adjacency and prerequisite in adjacency:
                    adjacency[dependent].add(prerequisite)
                else:
                    logger.warning("Dependência órfã: %s -> %s", dependent, prerequisite)

        return adjacency

    @staticmethod
    def _build_inverted_graph(
        adjacency_graph: Dict[str, Set[str]],
    ) -> Dict[str, Set[str]]:
        """
        Inverte o grafo para arestas prerequisite -> dependent.
        Garante presença de todos os nós sem arestas de saída.
        """
        inverted: Dict[str, Set[str]] = defaultdict(set)
        for dependent, prerequisites in adjacency_graph.items():
            for prerequisite in prerequisites:
                inverted[prerequisite].add(dependent)

        # garantir nós isolados
        for node in adjacency_graph.keys():
            _ = inverted[node]  # força key existir
        return dict(inverted)

    def _validate_dag_structure(self, context: PlanningContext) -> Dict[str, Any]:
        """Valida DAG a partir do grafo invertido centralizado no contexto."""
        try:
            is_valid, error_message = GraphAlgorithms.validate_dag(context.inverted_graph)
            if is_valid:
                metrics = GraphAlgorithms.calculate_graph_metrics(context.inverted_graph)
                return {
                    "is_valid": True,
                    "error": None,
                    "graph_metrics": metrics,
                }
            return {
                "is_valid": False,
                "error": error_message,
                "graph_metrics": None,
            }
        except Exception as e:
            logger.exception("Erro na validação do DAG: %s", e)
            return {
                "is_valid": False,
                "error": f"Erro interno na validação: {e}",
                "graph_metrics": None,
            }

    # --------------------------------------------------------------------- #
    # Scoring
    # --------------------------------------------------------------------- #

    def _configure_scoring_system(
        self,
        scoring_preset: str,
        custom_weights: Optional[Dict[str, float]],
    ) -> ServiceResult[ScoringPreset]:
        try:
            preset = self.scoring_system.get_preset(scoring_preset)
            if custom_weights:
                for key, weight in custom_weights.items():
                    if hasattr(preset, key):
                        setattr(preset, key, weight)
                    else:
                        logger.warning("Peso customizado ignorado (campo inexistente): %s", key)
            return ServiceResult.ok(preset)
        except Exception as e:
            return ServiceResult.validation_error(f"Erro na configuração do scoring: {e}")

    def _calculate_task_scores(
        self,
        context: PlanningContext,
        scoring_preset: ScoringPreset,
    ) -> Dict[str, float]:
        scores: Dict[str, float] = {}
        for task in context.tasks:
            try:
                scores[task.task_key] = self.scoring_system.calculate_score(task, scoring_preset)
            except Exception as e:
                logger.warning("Erro ao calcular score para %s: %s", task.task_key, e)
                scores[task.task_key] = 1.0  # fallback
        return scores

    # --------------------------------------------------------------------- #
    # Ordenação Topológica com Prioridade
    # --------------------------------------------------------------------- #

    def _topological_sort_with_priority(
        self,
        context: PlanningContext,
        task_scores: Dict[str, float],
    ) -> List[str]:
        """
        Ordenação topológica (Kahn) usando heap de max-prioridade.
        Critérios de prioridade (empate estável):
          1) maior score
          2) menor tdd_order (se existir)
          3) maior prioridade (se existir)
          4) task_key alfabética
        """
        inverted = context.inverted_graph

        # in_degree com base no grafo "task -> prerequisites"
        in_degree: Dict[str, int] = {t: 0 for t in context.adjacency_graph}
        for _, dependents in inverted.items():
            for dep in dependents:
                if dep in in_degree:
                    in_degree[dep] += 1

        def priority_tuple(task_key: str) -> tuple:
            meta = context.task_metadata.get(task_key, {})
            score = task_scores.get(task_key, 1.0)
            tdd_order = meta.get("tdd_order", 1_000_000)  # menor é melhor
            priority = meta.get("priority", 0)            # maior é melhor
            # Heapq é min-heap; usamos negativos onde maior é melhor.
            return (-score, tdd_order, -priority, task_key)

        heap: List[tuple] = []
        for tk, deg in in_degree.items():
            if deg == 0:
                heapq.heappush(heap, priority_tuple(tk))

        ordered: List[str] = []
        while heap:
            _, _, _, current = heapq.heappop(heap)
            ordered.append(current)

            for dependent in inverted.get(current, set()):
                if dependent in in_degree:
                    in_degree[dependent] -= 1
                    if in_degree[dependent] == 0:
                        heapq.heappush(heap, priority_tuple(dependent))

        if len(ordered) != len(context.tasks):
            missing = set(t.task_key for t in context.tasks) - set(ordered)
            logger.error("Ordenação topológica incompleta. Faltando nós: %s", sorted(missing))

        return ordered

    # --------------------------------------------------------------------- #
    # Caminho Crítico / Métricas
    # --------------------------------------------------------------------- #

    def _calculate_critical_path(self, context: PlanningContext) -> List[str]:
        try:
            return GraphAlgorithms.find_critical_path_nodes(
                context.inverted_graph, context.task_weights
            )
        except Exception as e:
            logger.exception("Erro ao calcular caminho crítico: %s", e)
            return []

    def _calculate_execution_metrics(
        self,
        context: PlanningContext,
        task_scores: Dict[str, float],
        execution_order: List[str],
    ) -> Dict[str, Any]:
        try:
            total_tasks = len(context.tasks)
            total_estimated_minutes = sum(context.task_weights.values())

            scores = list(task_scores.values())
            avg_score = sum(scores) / len(scores) if scores else 0.0

            total_deps = sum(len(prs) for prs in context.adjacency_graph.values())
            avg_deps = (total_deps / total_tasks) if total_tasks else 0.0

            priorities = [t.priority for t in context.tasks if getattr(t, "priority", None) is not None]
            avg_priority = (sum(priorities) / len(priorities)) if priorities else 0.0

            tdd_phases = [t.tdd_phase for t in context.tasks if getattr(t, "tdd_phase", None)]
            tdd_distribution = {p: tdd_phases.count(p) for p in set(tdd_phases)} if tdd_phases else {}

            return {
                "total_tasks": total_tasks,
                "total_estimated_minutes": total_estimated_minutes,
                "total_estimated_hours": round(total_estimated_minutes / 60, 1),
                "total_dependencies": total_deps,
                "avg_dependencies_per_task": round(avg_deps, 2),
                "scoring_metrics": {
                    "avg_score": round(avg_score, 2),
                    "max_score": round(max(scores), 2) if scores else 0.0,
                    "min_score": round(min(scores), 2) if scores else 0.0,
                    "score_range": round((max(scores) - min(scores)), 2) if scores else 0.0,
                },
                "tdd_distribution": tdd_distribution,
                "priority_metrics": {
                    "avg_priority": round(avg_priority, 1),
                    "priority_count": len(priorities),
                },
                "execution_order_length": len(execution_order),
                "planning_success": len(execution_order) == total_tasks,
            }
        except Exception as e:
            logger.exception("Erro ao calcular métricas: %s", e)
            return {"error": str(e)}

    # --------------------------------------------------------------------- #
    # Sumário executivo
    # --------------------------------------------------------------------- #

    def get_execution_summary(self, plan: ExecutionPlan) -> Dict[str, Any]:
        try:
            m = plan.execution_metrics
            return {
                "epic_id": plan.epic_id,
                "total_tasks": m.get("total_tasks", 0),
                "estimated_duration": {
                    "hours": m.get("total_estimated_hours", 0),
                    "minutes": m.get("total_estimated_minutes", 0),
                },
                "critical_path": {
                    "tasks": plan.critical_path,
                    "length": len(plan.critical_path),
                },
                "complexity_indicators": {
                    "dependencies": m.get("total_dependencies", 0),
                    "avg_score": m.get("scoring_metrics", {}).get("avg_score", 0),
                    "tdd_phases": len(m.get("tdd_distribution", {})),
                },
                "dag_validation": plan.dag_validation.get("is_valid", False),
                "execution_ready": m.get("planning_success", False),
                "created_at": plan.created_at.isoformat(),
            }
        except Exception as e:
            logger.exception("Erro ao gerar sumário: %s", e)
            return {"error": str(e)}
