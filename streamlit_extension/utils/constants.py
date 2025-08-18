from __future__ import annotations

from enum import Enum, IntEnum
from typing import Final, List

class TableNames:
    """Database table names."""
    CLIENTS: Final[str] = "framework_clients"
    PROJECTS: Final[str] = "framework_projects"
    EPICS: Final[str] = "framework_epics"
    TASKS: Final[str] = "framework_tasks"
    USERS: Final[str] = "framework_users"
    WORK_SESSIONS: Final[str] = "work_sessions"
    ACHIEVEMENTS: Final[str] = "user_achievements"
    STREAKS: Final[str] = "user_streaks"


class FieldNames:
    """Common database field names."""
    ID: Final[str] = "id"
    NAME: Final[str] = "name"
    EMAIL: Final[str] = "email"
    STATUS: Final[str] = "status"
    CREATED_AT: Final[str] = "created_at"
    UPDATED_AT: Final[str] = "updated_at"
    CLIENT_ID: Final[str] = "client_id"
    PROJECT_ID: Final[str] = "project_id"
    EPIC_ID: Final[str] = "epic_id"


class ClientStatus(Enum):
    """Client status values."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PROSPECT = "prospect"
    ARCHIVED = "archived"


class ProjectStatus(Enum):
    """Project status values."""
    PLANNING = "planning"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskStatus(Enum):
    """Task status values."""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    TESTING = "testing"
    DONE = "done"
    BLOCKED = "blocked"


class EpicStatus(Enum):
    """Epic status values."""
    DRAFT = "draft"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    DONE = "done"


class TDDPhase(Enum):
    """TDD development phases."""
    RED = "red"
    GREEN = "green"
    REFACTOR = "refactor"
    COMPLETE = "complete"


class Priority(IntEnum):
    """Priority levels for tasks and epics."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5


class Complexity(IntEnum):
    """Complexity levels for estimation."""
    TRIVIAL = 1
    SIMPLE = 2
    MODERATE = 3
    COMPLEX = 4
    EXPERT = 5


class UIConstants:
    """UI-related constants."""
    DEFAULT_PAGE_SIZE: Final[int] = 10
    MAX_PAGE_SIZE: Final[int] = 100
    DEFAULT_SEARCH_PLACEHOLDER: Final[str] = "Digite para buscar..."
    EMPTY_STATE_MESSAGE: Final[str] = "Nenhum registro encontrado"
    LOADING_MESSAGE: Final[str] = "Carregando..."
    SUCCESS_MESSAGE: Final[str] = "Operação realizada com sucesso!"
    ERROR_MESSAGE: Final[str] = "Erro ao executar operação"


class ValidationRules:
    """Validation constants."""
    MIN_PASSWORD_LENGTH: Final[int] = 8
    MAX_NAME_LENGTH: Final[int] = 100
    MAX_EMAIL_LENGTH: Final[int] = 255
    MAX_DESCRIPTION_LENGTH: Final[int] = 1000
    MIN_SEARCH_LENGTH: Final[int] = 2


class TimeConstants:
    """Time-related constants."""
    SESSION_TIMEOUT_MINUTES: Final[int] = 30
    CACHE_TTL_SECONDS: Final[int] = 300
    DB_CONNECTION_TIMEOUT: Final[int] = 30
    POMODORO_MINUTES: Final[int] = 25
    SHORT_BREAK_MINUTES: Final[int] = 5
    LONG_BREAK_MINUTES: Final[int] = 15

# Explicit re-exports para linting/type checkers
__all__: List[str] = [
    "TableNames", "FieldNames", "ClientStatus", "ProjectStatus", "TaskStatus",
    "EpicStatus", "TDDPhase", "Priority", "Complexity", "UIConstants",
    "ValidationRules", "TimeConstants",
]

