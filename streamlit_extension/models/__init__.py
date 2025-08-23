"""
Models module for enterprise task execution system with SQLAlchemy ORM integration
"""

# Legacy dataclass models (backward compatibility)
from .task_models import (
    Task,
    TaskDependency,
    TaskExecutionResult,
    TaskPriorityScore,
    TaskStatus,
    TDDPhase,
    TaskType,
    DependencyType,
    TaskModelError,
    InvalidTaskDataError,
    CyclicDependencyError,
    TaskNotFoundError
)

# SQLAlchemy base infrastructure
from .base import Base, get_session, create_tables
from .database import SQLAlchemyDatabase
from .mixins import AuditMixin, JSONFieldMixin, TDDWorkflowMixin, TDAHOptimizationMixin

# Core ORM models
from .task_enhanced import TaskORM
from .product_vision import ProductVisionORM
from .user_story import UserStoryORM
from .sprint import SprintORM, SprintStatus, SprintHealthStatus, SprintSyncStatus
from .sprint_milestone import SprintMilestoneORM, MilestoneType, MilestoneStatus, QualityStatus
from .task_dependency import TaskDependencyORM, DependencyType as ORMDependencyType, DependencyStrength, RiskLevel
from .task_labels import TaskLabelORM, TaskLabelAssignmentORM, LabelVisibility, AssignmentContext
from .ai_generation import AiGenerationORM, ChangeLogORM, GenerationType, ContextType, ReviewStatus

# Enums and data classes
from .sprint import SprintMetrics, SprintBurndownPoint
from .sprint_milestone import MilestoneProgress, UpdateFrequency
from .task_dependency import DependencyValidationResult
from .task_labels import LabelUsageStats, AutoAssignmentRule
from .ai_generation import GenerationMetrics, ChangeContext

__all__ = [
    # Legacy models (backward compatibility)
    'Task',
    'TaskDependency', 
    'TaskExecutionResult',
    'TaskPriorityScore',
    'TaskStatus',
    'TDDPhase',
    'TaskType',
    'DependencyType',
    'TaskModelError',
    'InvalidTaskDataError',
    'CyclicDependencyError',
    'TaskNotFoundError',
    
    # Base infrastructure
    'Base',
    'get_session',
    'create_tables',
    'SQLAlchemyDatabase',
    'AuditMixin',
    'JSONFieldMixin', 
    'TDDWorkflowMixin',
    'TDAHOptimizationMixin',
    
    # ORM models
    'TaskORM',
    'ProductVisionORM',
    'UserStoryORM',
    'SprintORM',
    'SprintMilestoneORM',
    'TaskDependencyORM',
    'TaskLabelORM',
    'TaskLabelAssignmentORM',
    'AiGenerationORM',
    'ChangeLogORM',
    
    # Enums
    'SprintStatus',
    'SprintHealthStatus', 
    'SprintSyncStatus',
    'MilestoneType',
    'MilestoneStatus',
    'QualityStatus',
    'UpdateFrequency',
    'ORMDependencyType',
    'DependencyStrength',
    'RiskLevel',
    'LabelVisibility',
    'AssignmentContext',
    'GenerationType',
    'ContextType',
    'ReviewStatus',
    
    # Data classes and result objects
    'SprintMetrics',
    'SprintBurndownPoint',
    'MilestoneProgress',
    'DependencyValidationResult',
    'LabelUsageStats',
    'AutoAssignmentRule',
    'GenerationMetrics',
    'ChangeContext'
]