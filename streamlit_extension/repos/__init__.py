"""
Repository layer for data access operations.

Clean architecture implementation with consistent error handling,
performance optimization and production-ready patterns.
"""

from .tasks_repo import TasksRepo, RepoError
from .deps_repo import DepsRepo

__all__ = [
    'TasksRepo',
    'DepsRepo', 
    'RepoError'
]