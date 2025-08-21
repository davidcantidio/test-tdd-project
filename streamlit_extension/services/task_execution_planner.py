#!/usr/bin/env python3
"""
🎯 SERVICES - Task Execution Planner

Sistema de ordenação topológica e priorização de tarefas baseado em DAG.
Implementação refatorada usando componentes limpos e testáveis.

Usage:
    from streamlit_extension.services.task_execution_planner import TaskExecutionPlanner
    
    planner = TaskExecutionPlanner(db_connection)
    result = planner.plan_execution(epic_id=1, scoring_preset="balanced")

Features:
- ✅ Ordenação topológica com priorização por heap
- ✅ Sistema de scoring configurável
- ✅ Detecção de ciclos e validação de DAG
- ✅ Repository pattern para acesso a dados
- ✅ Error handling robusto com ServiceResult
- ✅ Métricas e analytics do plano de execução
"""

import logging
import heapq
from typing import Dict, List, Set, Optional, Any, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, deque
from datetime import datetime

from ..repos.tasks_repo import TasksRepo, RepoError
from ..repos.deps_repo import DepsRepo
from ..models.task_models import Task, TaskDependency
from ..models.scoring import ScoringSystem, ScoringPreset
from ..utils.graph_algorithms import GraphAlgorithms
from ..services.base import BaseService, ServiceResult

logger = logging.getLogger(__name__)

@dataclass
class ExecutionPlan:
    """Resultado do planejamento de execução"""
    epic_id: int
    execution_order: List[str]
    task_scores: Dict[str, float]
    critical_path: List[str]
    execution_metrics: Dict[str, Any]
    dag_validation: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.now)

@dataclass 
class PlanningContext:
    """Contexto interno para planejamento"""
    tasks: List[Task]
    dependencies: List[TaskDependency]
    adjacency_graph: Dict[str, Set[str]]
    task_weights: Dict[str, int]
    task_metadata: Dict[str, Dict[str, Any]]

class TaskExecutionPlannerError(Exception):
    """Exception específica do TaskExecutionPlanner"""
    pass

class TaskExecutionPlanner(BaseService):
    # Delegation to TaskExecutionPlannerValidation
    def __init__(self):
        self._taskexecutionplannervalidation = TaskExecutionPlannerValidation()
    # Delegation to TaskExecutionPlannerLogging
    def __init__(self):
        self._taskexecutionplannerlogging = TaskExecutionPlannerLogging()
    # Delegation to TaskExecutionPlannerErrorhandling
    def __init__(self):
        self._taskexecutionplannererrorhandling = TaskExecutionPlannerErrorhandling()
    # Delegation to TaskExecutionPlannerConfiguration
    def __init__(self):
        self._taskexecutionplannerconfiguration = TaskExecutionPlannerConfiguration()
    # Delegation to TaskExecutionPlannerCalculation
    def __init__(self):
        self._taskexecutionplannercalculation = TaskExecutionPlannerCalculation()
    # Delegation to TaskExecutionPlannerFormatting
    def __init__(self):
        self._taskexecutionplannerformatting = TaskExecutionPlannerFormatting()
    # Delegation to TaskExecutionPlannerNetworking
    def __init__(self):
        self._taskexecutionplannernetworking = TaskExecutionPlannerNetworking()
    """
    Planejador de execução de tarefas com ordenação topológica e priorização.
    
    Integra todos os componentes refatorados:
    - TasksRepo e DepsRepo para acesso a dados
    - ScoringSystem para priorização configurável  
    - GraphAlgorithms para ordenação topológica
    - Validação de DAG e detecção de ciclos
    """
    
    def __init__(self, connection):
        """
        Args:
            connection: Database connection object
        """
        super().__init__()
        self.connection = connection
        self.tasks_repo = TasksRepo(connection)
        self.deps_repo = DepsRepo(connection)
        self.scoring_system = ScoringSystem()
    
    def plan_execution(
        self, 
        epic_id: int, 
        scoring_preset: str = "balanced",
        custom_weights: Optional[Dict[str, float]] = None
    ) -> ServiceResult[ExecutionPlan]:
        """
        Planeja execução de tarefas com ordenação topológica e priorização.
        
        Args:
            epic_id: ID do épico
            scoring_preset: Preset de scoring ("balanced", "critical_path", "tdd_workflow", "business_value")
            custom_weights: Pesos customizados para override do preset
            
        Returns:
            ServiceResult contendo ExecutionPlan ou erros
        """
        try:
            self._log_operation_start("plan_execution", {"epic_id": epic_id, "preset": scoring_preset})
            
            # 1. Validação de inputs
            validation_result = self._validate_planning_inputs(epic_id, scoring_preset)
            if not validation_result.success:
                return validation_result
            
            # 2. Carregar dados usando repositories
            context_result = self._load_planning_context(epic_id)
            if not context_result.success:
                return context_result
            
            context = context_result.data
            
            # 3. Validar DAG e detectar ciclos
            dag_validation = self._validate_dag_structure(context)
            if not dag_validation["is_valid"]:
                return ServiceResult.validation_error(
                    f"DAG inválido para épico {epic_id}: {dag_validation['error']}"
                )
            
            # 4. Configurar sistema de scoring
            scoring_config_result = self._configure_scoring_system(scoring_preset, custom_weights)
            if not scoring_config_result.success:
                return scoring_config_result
            
            # 5. Calcular scores das tarefas
            task_scores = self._calculate_task_scores(context, scoring_config_result.data)
            
            # 6. Executar ordenação topológica com priorização
            execution_order = self._topological_sort_with_priority(context, task_scores)
            
            # 7. Calcular caminho crítico
            critical_path = self._calculate_critical_path(context)
            
            # 8. Calcular métricas do plano
            execution_metrics = self._calculate_execution_metrics(context, task_scores, execution_order)
            
            # 9. Criar plano de execução
            plan = ExecutionPlan(
                epic_id=epic_id,
                execution_order=execution_order,
                task_scores=task_scores,
                critical_path=critical_path,
                execution_metrics=execution_metrics,
                dag_validation=dag_validation
            )
            
            logger.info(f"Plano de execução criado para épico {epic_id}: {len(execution_order)} tarefas ordenadas")
            return ServiceResult.ok(plan)
            
        except Exception as e:
            logger.error(f"Erro no planejamento de execução do épico {epic_id}: {e}")
            return ServiceResult.validation_error(f"Falha no planejamento: {str(e)}")
    
    def _validate_planning_inputs(self, epic_id: int, scoring_preset: str) -> ServiceResult[bool]:
        """Valida inputs do planejamento"""
        errors = []
        
        if not isinstance(epic_id, int) or epic_id <= 0:
            errors.append(f"epic_id deve ser inteiro positivo, recebido: {epic_id}")
        
        valid_presets = {"balanced", "critical_path", "tdd_workflow", "business_value"}
        if scoring_preset not in valid_presets:
            errors.append(f"scoring_preset inválido: {scoring_preset}. Válidos: {valid_presets}")
        
        if errors:
            return ServiceResult.validation_error("; ".join(errors))
        
        return ServiceResult.ok(True)
    
    def _load_planning_context(self, epic_id: int) -> ServiceResult[PlanningContext]:
        """Carrega contexto necessário para planejamento usando repositories"""
        try:
            # Carregar tarefas
            tasks = self.tasks_repo.list_by_epic(epic_id)
            if not tasks:
                return ServiceResult.not_found("tasks", f"epic_id={epic_id}")
            
            # Carregar dependências  
            dependencies = self.deps_repo.list_by_epic(epic_id)
            
            # Construir grafo de adjacência
            adjacency_graph = self._build_adjacency_graph(tasks, dependencies)
            
            # Extrair pesos das tarefas (estimate_minutes)
            task_weights = {
                task.task_key: max(task.estimate_minutes or 60, 1)  # Mínimo 1 minuto
                for task in tasks
            }
            
            # Construir metadados das tarefas
            task_metadata = {
                task.task_key: {
                    "id": task.id,
                    "title": task.title,
                    "tdd_phase": task.tdd_phase,
                    "tdd_order": task.tdd_order,
                    "priority": task.priority,
                    "story_points": task.story_points,
                    "task_type": task.task_type,
                    "status": task.status,
                    "task_group": task.task_group,
                    "task_sequence": task.task_sequence
                }
                for task in tasks
            }
            
            context = PlanningContext(
                tasks=tasks,
                dependencies=dependencies,
                adjacency_graph=adjacency_graph,
                task_weights=task_weights,
                task_metadata=task_metadata
            )
            
            return ServiceResult.ok(context)
            
        except RepoError as e:
            return ServiceResult.validation_error(f"Erro no repository: {e}")
        except Exception as e:
            return ServiceResult.validation_error(f"Erro ao carregar contexto: {e}")
    
    def _build_adjacency_graph(self, tasks: List[Task], dependencies: List[TaskDependency]) -> Dict[str, Set[str]]:
        """Constrói grafo de adjacência a partir de tarefas e dependências"""
        # Inicializar com todas as tarefas
        adjacency = {task.task_key: set() for task in tasks}
        
        # Adicionar dependências
        for dep in dependencies:
            if hasattr(dep, 'dependent_task_key') and dep.dependent_task_key:
                # dependent_task_key -> depends_on_task_key
                dependent = dep.dependent_task_key
                prerequisite = dep.depends_on_task_key
                
                if dependent in adjacency and prerequisite in adjacency:
                    adjacency[dependent].add(prerequisite)
                else:
                    logger.warning(f"Dependência órfã: {dependent} -> {prerequisite}")
        
        return adjacency
    
    def _validate_dag_structure(self, context: PlanningContext) -> Dict[str, Any]:
        """Valida estrutura DAG usando GraphAlgorithms"""
        try:
            # Inverter grafo para ordenação correta (prerequisite -> dependent)
            inverted_graph = defaultdict(set)
            for dependent, prerequisites in context.adjacency_graph.items():
                for prerequisite in prerequisites:
                    inverted_graph[prerequisite].add(dependent)
            
            # Garantir que todos os nós estão no grafo invertido
            for task_key in context.adjacency_graph.keys():
                if task_key not in inverted_graph:
                    inverted_graph[task_key] = set()
            
            inverted_graph_dict = dict(inverted_graph)
            
            # Validar DAG
            is_valid, error_message = GraphAlgorithms.validate_dag(inverted_graph_dict)
            
            if is_valid:
                # Calcular métricas do grafo
                graph_metrics = GraphAlgorithms.calculate_graph_metrics(inverted_graph_dict)
                
                return {
                    "is_valid": True,
                    "error": None,
                    "graph_metrics": graph_metrics,
                    "inverted_graph": inverted_graph_dict
                }
            else:
                return {
                    "is_valid": False,
                    "error": error_message,
                    "graph_metrics": None,
                    "inverted_graph": None
                }
        
        except Exception as e:
            logger.error(f"Erro na validação DAG: {e}")
            return {
                "is_valid": False,
                "error": f"Erro interno na validação: {e}",
                "graph_metrics": None,
                "inverted_graph": None
            }
    
    def _configure_scoring_system(
        self, 
        scoring_preset: str, 
        custom_weights: Optional[Dict[str, float]]
    ) -> ServiceResult[ScoringPreset]:
        """Configura sistema de scoring"""
        try:
            preset = self.scoring_system.get_preset(scoring_preset)
            
            # Aplicar weights customizados se fornecidos
            if custom_weights:
                for key, weight in custom_weights.items():
                    if hasattr(preset, key):
                        setattr(preset, key, weight)
                    else:
                        logger.warning(f"Weight customizado ignorado (inexistente): {key}")
            
            return ServiceResult.ok(preset)
            
        except Exception as e:
            return ServiceResult.validation_error(f"Erro na configuração do scoring: {e}")
    
    def _calculate_task_scores(
        self, 
        context: PlanningContext, 
        scoring_preset: ScoringPreset
    ) -> Dict[str, float]:
        """Calcula scores das tarefas usando sistema configurável"""
        task_scores = {}
        
        for task in context.tasks:
            try:
                score = self.scoring_system.calculate_score(task, scoring_preset)
                task_scores[task.task_key] = score
            except Exception as e:
                logger.warning(f"Erro ao calcular score para {task.task_key}: {e}")
                task_scores[task.task_key] = 1.0  # Score padrão
        
        return task_scores
    
    def _topological_sort_with_priority(
        self, 
        context: PlanningContext, 
        task_scores: Dict[str, float]
    ) -> List[str]:
        """
        Ordenação topológica com priorização por heap.
        Implementação baseada no algoritmo de Kahn com heap para priorização.
        """
        # Usar grafo invertido da validação DAG
        inverted_graph = defaultdict(set)
        for dependent, prerequisites in context.adjacency_graph.items():
            for prerequisite in prerequisites:
                inverted_graph[prerequisite].add(dependent)
        
        # Garantir todos os nós
        for task_key in context.adjacency_graph.keys():
            if task_key not in inverted_graph:
                inverted_graph[task_key] = set()
        
        # Calcular in-degree
        in_degree = {task_key: 0 for task_key in context.adjacency_graph.keys()}
        for node in inverted_graph:
            for neighbor in inverted_graph[node]:
                if neighbor in in_degree:
                    in_degree[neighbor] += 1
        
        # Heap com nós de in-degree 0 (prioridade negativa para max-heap)
        heap = []
        for task_key, degree in in_degree.items():
            if degree == 0:
                score = task_scores.get(task_key, 1.0)
                # Usar -score para max-heap e task_key como tiebreaker
                heapq.heappush(heap, (-score, task_key))
        
        result = []
        
        while heap:
            # Pegar tarefa com maior prioridade
            neg_score, current_task = heapq.heappop(heap)
            result.append(current_task)
            
            # Atualizar in-degree dos dependentes
            for dependent in inverted_graph.get(current_task, set()):
                if dependent in in_degree:
                    in_degree[dependent] -= 1
                    if in_degree[dependent] == 0:
                        score = task_scores.get(dependent, 1.0)
                        heapq.heappush(heap, (-score, dependent))
        
        # Verificar se processou todas as tarefas
        if len(result) != len(context.tasks):
            missing = set(task.task_key for task in context.tasks) - set(result)
            logger.error(f"Nem todas as tarefas foram processadas. Faltam: {missing}")
        
        return result
    
    def _calculate_critical_path(self, context: PlanningContext) -> List[str]:
        """Calcula caminho crítico usando GraphAlgorithms"""
        try:
            # Usar grafo invertido
            inverted_graph = defaultdict(set)
            for dependent, prerequisites in context.adjacency_graph.items():
                for prerequisite in prerequisites:
                    inverted_graph[prerequisite].add(dependent)
            
            for task_key in context.adjacency_graph.keys():
                if task_key not in inverted_graph:
                    inverted_graph[task_key] = set()
            
            inverted_graph_dict = dict(inverted_graph)
            
            return GraphAlgorithms.find_critical_path_nodes(inverted_graph_dict, context.task_weights)
            
        except Exception as e:
            logger.error(f"Erro ao calcular caminho crítico: {e}")
            return []
    
    def _calculate_execution_metrics(
        self, 
        context: PlanningContext, 
        task_scores: Dict[str, float],
        execution_order: List[str]
    ) -> Dict[str, Any]:
        """Calcula métricas do plano de execução"""
        try:
            total_tasks = len(context.tasks)
            total_estimated_minutes = sum(context.task_weights.values())
            
            # Métricas de scoring
            scores = list(task_scores.values())
            avg_score = sum(scores) / len(scores) if scores else 0
            max_score = max(scores) if scores else 0
            min_score = min(scores) if scores else 0
            
            # Métricas de TDD
            tdd_phases = [task.tdd_phase for task in context.tasks if task.tdd_phase]
            tdd_distribution = {phase: tdd_phases.count(phase) for phase in set(tdd_phases)} if tdd_phases else {}
            
            # Métricas de dependências
            total_dependencies = len(context.dependencies)
            avg_dependencies_per_task = total_dependencies / total_tasks if total_tasks > 0 else 0
            
            # Métricas de prioridade
            priorities = [task.priority for task in context.tasks if task.priority]
            avg_priority = sum(priorities) / len(priorities) if priorities else 0
            
            return {
                "total_tasks": total_tasks,
                "total_estimated_minutes": total_estimated_minutes,
                "total_estimated_hours": round(total_estimated_minutes / 60, 1),
                "total_dependencies": total_dependencies,
                "avg_dependencies_per_task": round(avg_dependencies_per_task, 2),
                "scoring_metrics": {
                    "avg_score": round(avg_score, 2),
                    "max_score": round(max_score, 2),
                    "min_score": round(min_score, 2),
                    "score_range": round(max_score - min_score, 2)
                },
                "tdd_distribution": tdd_distribution,
                "priority_metrics": {
                    "avg_priority": round(avg_priority, 1),
                    "priority_count": len(priorities)
                },
                "execution_order_length": len(execution_order),
                "planning_success": len(execution_order) == total_tasks
            }
            
        except Exception as e:
            logger.error(f"Erro ao calcular métricas: {e}")
            return {"error": str(e)}
    
    def get_execution_summary(self, plan: ExecutionPlan) -> Dict[str, Any]:
        """
        Gera sumário executivo do plano de execução.
        
        Args:
            plan: Plano de execução
            
        Returns:
            Dicionário com sumário executivo
        """
        try:
            metrics = plan.execution_metrics
            
            return {
                "epic_id": plan.epic_id,
                "total_tasks": metrics.get("total_tasks", 0),
                "estimated_duration": {
                    "hours": metrics.get("total_estimated_hours", 0),
                    "minutes": metrics.get("total_estimated_minutes", 0)
                },
                "critical_path": {
                    "tasks": plan.critical_path,
                    "length": len(plan.critical_path)
                },
                "complexity_indicators": {
                    "dependencies": metrics.get("total_dependencies", 0),
                    "avg_score": metrics.get("scoring_metrics", {}).get("avg_score", 0),
                    "tdd_phases": len(metrics.get("tdd_distribution", {}))
                },
                "dag_validation": plan.dag_validation.get("is_valid", False),
                "execution_ready": metrics.get("planning_success", False),
                "created_at": plan.created_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erro ao gerar sumário: {e}")
            return {"error": str(e)}