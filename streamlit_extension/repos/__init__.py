"""
Repository layer for data access operations.

Clean architecture implementation with consistent error handling,
performance optimization and production-ready patterns.
"""

from .tasks_repo import TasksRepo, RepoError
from .deps_repo import DepsRepo
# Auth imports
from streamlit_extension.auth.middleware import require_auth, require_admin
from streamlit_extension.auth.user_model import UserRole


__all__ = ["TasksRepo", "DepsRepo", "RepoError"]
