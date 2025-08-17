#!/usr/bin/env python3
"""
🔧 MODELS - Task Execution Models

Modelos de dados para sistema de ordenação topológica e priorização de tarefas.
Dataclass alinhada com schema do banco de dados.

Usage:
    from streamlit_extension.models.task_models import Task, TaskExecutionResult
    
Features:
- Task dataclass com todos os campos necessários
- Validação de dados de entrada
- Métodos utilitários para TDD workflow
- Compatibilidade com sqlite3.Row
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Set
from enum import Enum
from datetime import datetime, date

class TaskStatus(Enum):
    """Status da tarefa"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"

class TDDPhase(Enum):
    """Fases do ciclo TDD"""
    RED = "red"
    GREEN = "green"
    REFACTOR = "refactor"

class TaskType(Enum):
    """Tipos de tarefa"""
    IMPLEMENTATION = "implementation"
    ANALYSIS = "analysis"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    REFACTORING = "refactoring"

class DependencyType(Enum):
    """Tipos de dependência"""
    BLOCKING = "blocking"
    TDD_SEQUENCE = "tdd_sequence"
    RELATED = "related"
    OPTIONAL = "optional"

@dataclass
class Task:
    """
    Modelo completo de tarefa com todos os campos necessários
    Alinhado com schema framework_tasks
    """
    # Campos obrigatórios
    id: int
    task_key: str
    epic_id: int
    title: str
    
    # Campos de descrição
    description: Optional[str] = None
    
    # Campos TDD e workflow
    tdd_phase: Optional[str] = None
    tdd_order: Optional[int] = None
    task_type: str = "implementation"
    status: str = "pending"
    
    # Campos de estimativa e tracking
    estimate_minutes: Optional[int] = None
    actual_minutes: Optional[int] = None
    story_points: Optional[int] = None
    position: Optional[int] = None
    
    # Campos de priorização
    priority: int = 3  # 1=crítico, 5=backlog
    
    # Campos de agrupamento
    task_group: Optional[str] = None
    task_sequence: Optional[int] = None
    parent_task_key: Optional[str] = None
    
    # Campos de gamificação
    points_earned: int = 0
    difficulty_modifier: float = 1.0
    streak_bonus: int = 0
    perfectionist_bonus: int = 0
    points_value: int = 5
    
    # Campos GitHub
    github_issue_number: Optional[int] = None
    github_branch: Optional[str] = None
    github_pr_number: Optional[int] = None
    
    # Campos de atribuição
    assigned_to: Optional[int] = None
    reviewer_id: Optional[int] = None
    
    # Campos de auditoria
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    deleted_at: Optional[str] = None
    due_date: Optional[str] = None
    
    # Campos JSON
    test_plan: Optional[str] = None
    test_specs: Optional[str] = None
    acceptance_criteria: Optional[str] = None
    deliverables: Optional[str] = None
    files_touched: Optional[str] = None
    priority_tags: Optional[str] = None
    task_labels: Optional[str] = None
    
    # Campos de risco
    risk: Optional[str] = None
    mitigation: Optional[str] = None
    tdd_skip_reason: Optional[str] = None
    
    def __post_init__(self):
        """Validação e normalização após inicialização"""
        # Normalizar prioridade
        if self.priority < 1:
            self.priority = 1
        elif self.priority > 5:
            self.priority = 5
            
        # Extrair task_group se não definido
        if not self.task_group and self.task_key:
            self._extract_task_group()
    
    def _extract_task_group(self):
        """Extrai task_group do task_key (ex: '1.1b.1' → '1.1b')"""
        parts = self.task_key.split('.')
        if len(parts) >= 2:
            # Se último elemento é número, remover (sequência)
            if parts[-1].isdigit():
                self.task_group = '.'.join(parts[:-1])
                if not self.task_sequence:
                    self.task_sequence = int(parts[-1])
            else:
                self.task_group = self.task_key
                if not self.task_sequence:
                    self.task_sequence = 1
    
    @property
    def is_tdd_task(self) -> bool:
        """Verifica se é tarefa TDD"""
        return self.tdd_order is not None and self.tdd_phase is not None
    
    @property
    def is_analysis_task(self) -> bool:
        """Verifica se é tarefa de análise"""
        return self.task_type == "analysis" or self.tdd_skip_reason is not None
    
    @property
    def is_blocked(self) -> bool:
        """Verifica se tarefa está bloqueada"""
        return self.status == TaskStatus.BLOCKED.value
    
    @property
    def is_completed(self) -> bool:
        """Verifica se tarefa está completa"""
        return self.status == TaskStatus.COMPLETED.value
    
    @property
    def effort_estimate(self) -> int:
        """Retorna estimativa de esforço (minutos ou story points convertidos)"""
        if self.estimate_minutes:
            return self.estimate_minutes
        elif self.story_points:
            # Conversão aproximada: 1 story point = 30 minutos
            return self.story_points * 30
        else:
            return 60  # Default 1 hora
    
    @property
    def value_density(self) -> float:
        """Calcula densidade de valor (valor/esforço)"""
        effort = max(self.effort_estimate, 1)
        value_score = (6 - self.priority)  # 1=5 pontos, 5=1 ponto
        return value_score / effort
    
    @property
    def tdd_phase_enum(self) -> Optional[TDDPhase]:
        """Retorna TDD phase como enum"""
        if self.tdd_phase:
            try:
                return TDDPhase(self.tdd_phase)
            except ValueError:
                return None
        return None
    
    @property
    def status_enum(self) -> TaskStatus:
        """Retorna status como enum"""
        try:
            return TaskStatus(self.status)
        except ValueError:
            return TaskStatus.PENDING
    
    @property
    def task_type_enum(self) -> TaskType:
        """Retorna task type como enum"""
        try:
            return TaskType(self.task_type)
        except ValueError:
            return TaskType.IMPLEMENTATION
    
    def get_tdd_next_phase(self) -> Optional[str]:
        """Retorna próxima fase TDD"""
        if not self.is_tdd_task:
            return None
            
        phase_progression = {
            TDDPhase.RED.value: TDDPhase.GREEN.value,
            TDDPhase.GREEN.value: TDDPhase.REFACTOR.value,
            TDDPhase.REFACTOR.value: None  # Ciclo completo
        }
        
        return phase_progression.get(self.tdd_phase)
    
    def is_ready_for_execution(self, completed_tasks: Set[str]) -> bool:
        """
        Verifica se tarefa está pronta para execução
        (sem dependências pendentes)
        """
        # Tarefa já completa não precisa execução
        if self.is_completed:
            return False
            
        # Tarefa bloqueada não pode executar
        if self.is_blocked:
            return False
            
        # Para este método funcionar completamente, precisaria das dependências
        # Mas como é uma tarefa individual, assumimos que sim por padrão
        return True
    
    def calculate_complexity_score(self) -> float:
        """Calcula score de complexidade baseado em múltiplos fatores"""
        base_complexity = max(self.story_points or 1, 1)
        
        # TDD tasks são mais estruturadas, menos complexas
        tdd_factor = 0.8 if self.is_tdd_task else 1.0
        
        # Analysis tasks podem ser mais incertas
        analysis_factor = 1.2 if self.is_analysis_task else 1.0
        
        # Difficulty modifier do banco
        difficulty_factor = self.difficulty_modifier
        
        return base_complexity * tdd_factor * analysis_factor * difficulty_factor
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        result = {}
        for field in self.__dataclass_fields__:
            value = getattr(self, field)
            result[field] = value
        return result
    
    @classmethod
    def from_db_row(cls, row) -> 'Task':
        """Cria Task a partir de sqlite3.Row"""
        # Converter row para dict
        if hasattr(row, 'keys'):
            data = dict(row)
        else:
            # Fallback para tuple/list
            data = row
            
        # Filtrar apenas campos existentes na dataclass
        valid_fields = cls.__dataclass_fields__.keys()
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        
        return cls(**filtered_data)

@dataclass
class TaskDependency:
    """Modelo de dependência entre tarefas"""
    id: int
    task_id: int
    depends_on_task_key: str
    depends_on_task_id: Optional[int] = None
    dependency_type: str = "blocking"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    @property
    def dependency_type_enum(self) -> DependencyType:
        """Retorna tipo de dependência como enum"""
        try:
            return DependencyType(self.dependency_type)
        except ValueError:
            return DependencyType.BLOCKING
    
    @classmethod
    def from_db_row(cls, row) -> 'TaskDependency':
        """Cria TaskDependency a partir de sqlite3.Row"""
        if hasattr(row, 'keys'):
            data = dict(row)
        else:
            data = row
            
        valid_fields = cls.__dataclass_fields__.keys()
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        
        return cls(**filtered_data)

@dataclass
class TaskExecutionResult:
    """Resultado da ordenação de execução de tarefas"""
    epic_id: int
    execution_order: List[str]
    parallel_batches: List[List[str]]
    total_tasks: int
    tasks_with_dependencies: int
    total_dependencies: int
    estimated_total_minutes: int
    critical_path_length: int
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    
    @property
    def has_errors(self) -> bool:
        """Verifica se há erros"""
        return len(self.errors) > 0
    
    @property
    def has_warnings(self) -> bool:
        """Verifica se há warnings"""
        return len(self.warnings) > 0
    
    @property
    def dependency_percentage(self) -> float:
        """Percentual de tarefas com dependências"""
        if self.total_tasks == 0:
            return 0.0
        return (self.tasks_with_dependencies / self.total_tasks) * 100
    
    @property
    def avg_dependencies_per_task(self) -> float:
        """Média de dependências por tarefa"""
        if self.tasks_with_dependencies == 0:
            return 0.0
        return self.total_dependencies / self.tasks_with_dependencies
    
    @property
    def estimated_hours(self) -> float:
        """Estimativa total em horas"""
        return self.estimated_total_minutes / 60
    
    @property
    def max_parallel_tasks(self) -> int:
        """Máximo de tarefas que podem executar em paralelo"""
        if not self.parallel_batches:
            return 0
        return max(len(batch) for batch in self.parallel_batches)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return {
            'epic_id': self.epic_id,
            'execution_order': self.execution_order,
            'parallel_batches': self.parallel_batches,
            'total_tasks': self.total_tasks,
            'tasks_with_dependencies': self.tasks_with_dependencies,
            'total_dependencies': self.total_dependencies,
            'estimated_total_minutes': self.estimated_total_minutes,
            'estimated_hours': self.estimated_hours,
            'critical_path_length': self.critical_path_length,
            'dependency_percentage': self.dependency_percentage,
            'avg_dependencies_per_task': self.avg_dependencies_per_task,
            'max_parallel_tasks': self.max_parallel_tasks,
            'warnings': self.warnings,
            'errors': self.errors,
            'has_errors': self.has_errors,
            'has_warnings': self.has_warnings
        }

@dataclass
class TaskPriorityScore:
    """Score detalhado de priorização de tarefa"""
    task_key: str
    total_score: float
    priority_score: float
    value_density_score: float
    unblock_score: float
    critical_path_score: float
    tdd_bonus_score: float
    aging_score: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário"""
        return {
            'task_key': self.task_key,
            'total_score': self.total_score,
            'priority_score': self.priority_score,
            'value_density_score': self.value_density_score,
            'unblock_score': self.unblock_score,
            'critical_path_score': self.critical_path_score,
            'tdd_bonus_score': self.tdd_bonus_score,
            'aging_score': self.aging_score
        }

# Exceptions customizadas
class TaskModelError(Exception):
    """Erro base para modelos de tarefa"""
    pass

class InvalidTaskDataError(TaskModelError):
    """Erro para dados de tarefa inválidos"""
    pass

class CyclicDependencyError(TaskModelError):
    """Erro para dependências cíclicas"""
    pass

class TaskNotFoundError(TaskModelError):
    """Erro para tarefa não encontrada"""
    pass