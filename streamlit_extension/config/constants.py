"""
📋 Application Constants and Enums

Centraliza strings e enums para reduzir *magic strings* no codebase.
Também cria **aliases compatíveis** com importações legadas do pacote.
"""

from enum import Enum
from typing import List, Dict, Any
# Auth imports
from streamlit_extension.auth.middleware import require_auth, require_admin
from streamlit_extension.auth.user_model import UserRole


class StatusValues(Enum):
    """Centralized status values for all entities"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    COMPLETED = "completed"
    PLANNING = "planning"
    IN_PROGRESS = "in_progress"
    ON_HOLD = "on_hold"
    CANCELLED = "cancelled"
    RED = "red"
    GREEN = "green"
    REFACTOR = "refactor"
    BLOCKED = "blocked"
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"

    @classmethod
    def get_all_values(cls) -> List[str]:
        """Get all status values as a list."""
        return [status.value for status in cls]


class TDDPhases(Enum):
    """TDD cycle phases"""
    RED = "red"
    GREEN = "green"
    REFACTOR = "refactor"
    BLOCKED = "blocked"

    @classmethod
    def get_all_values(cls) -> List[str]:
        """Get all phase values as a list."""
        return [phase.value for phase in cls]


class ClientTiers(Enum):
    """Client tier classifications"""
    FREE_TRIAL = "free_trial"
    STANDARD = "standard"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"

    @classmethod
    def get_all_values(cls) -> List[str]:
        """Get all tier values as a list."""
        return [tier.value for tier in cls]

    @classmethod
    def get_default(cls) -> str:
        """Get default client tier."""
        return cls.STANDARD.value


class CompanySizes(Enum):
    """Company size categories"""
    STARTUP = "startup"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    ENTERPRISE = "enterprise"
    SIZE_1_10 = "1-10"
    SIZE_11_50 = "11-50"
    SIZE_51_200 = "51-200"
    SIZE_201_1000 = "201-1000"
    SIZE_1000_PLUS = "1000+"

    @classmethod
    def get_all_values(cls) -> List[str]:
        """Get all company size values as a list."""
        return [size.value for size in cls]

    @classmethod
    def get_default(cls) -> str:
        """Get default company size."""
        return cls.STARTUP.value


class ErrorMessages:
    """Centralized error message templates"""
    # Client errors
    CLIENT_LOAD_ERROR = "❌ Error loading clients: {error}"
    CLIENT_CREATE_ERROR = "❌ Error creating client: {error}"
    CLIENT_UPDATE_ERROR = "❌ Error updating client: {error}"
    CLIENT_DELETE_ERROR = "❌ Error deleting client: {error}"
    CLIENT_NOT_FOUND = "❌ Client not found"
    CLIENT_CREATE_SUCCESS = "✅ Client created successfully!"
    CLIENT_UPDATE_SUCCESS = "✅ Client updated successfully!"
    CLIENT_DELETE_SUCCESS = "✅ Client deleted successfully!"

    # Project errors
    PROJECT_LOAD_ERROR = "❌ Error loading projects: {error}"
    PROJECT_CREATE_ERROR = "❌ Error creating project: {error}"
    PROJECT_UPDATE_ERROR = "❌ Error updating project: {error}"
    PROJECT_DELETE_ERROR = "❌ Error deleting project: {error}"

    # Generic errors
    NO_MATCHES_FILTER = "⚠️ No {entity} match your current filters."
    NO_ITEMS_FOUND = "🔍 No {entity} found"
    LOADING_ERROR = "❌ Error loading {entity}: {error}"


# ──────────────────────────────────────────────────────────────────────────────
# UI constants (ícones e textos comuns)
# (mantidos conforme trechos existentes neste arquivo)
# ──────────────────────────────────────────────────────────────────────────────


class TaskStatus(Enum):
    """Task status options."""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    PENDING = "pending"
    
    @classmethod
    def get_all_values(cls) -> List[str]:
        """Get all status values as a list."""
        return [status.value for status in cls]
    
    @classmethod
    def get_active_statuses(cls) -> List[str]:
        """Get statuses considered 'active' (not completed)."""
        return [cls.TODO.value, cls.IN_PROGRESS.value, cls.BLOCKED.value, cls.PENDING.value]


class EpicStatus(Enum):
    """Epic status options."""
    PLANNING = "planning"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"
    
    @classmethod
    def get_all_values(cls) -> List[str]:
        """Get all status values as a list."""
        return [status.value for status in cls]
    
    @classmethod
    def get_active_statuses(cls) -> List[str]:
        """Get statuses considered 'active' (not completed or archived)."""
        return [cls.PLANNING.value, cls.ACTIVE.value, cls.ON_HOLD.value]


class ProjectStatus(Enum):
    """Project status options."""
    PLANNING = "planning"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"
    
    @classmethod
    def get_all_values(cls) -> List[str]:
        """Get all status values as a list."""
        return [status.value for status in cls]


class ClientStatus(Enum):
    """Client status options."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PROSPECT = "prospect"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"
    
    @classmethod
    def get_all_values(cls) -> List[str]:
        """Get all status values as a list."""
        return [status.value for status in cls]
    
    @classmethod
    def get_display_name(cls, status_value: str) -> str:
        """Get display-friendly name for status value."""
        display_names = {
            cls.ACTIVE.value: "Ativo",
            cls.INACTIVE.value: "Inativo", 
            cls.PROSPECT.value: "Prospecto",
            cls.SUSPENDED.value: "Suspenso",
            cls.ARCHIVED.value: "Arquivado"
        }
        return display_names.get(status_value, status_value.title())
    
    @classmethod
    def get_default(cls) -> str:
        """Get default client status."""
        return cls.ACTIVE.value


class GeneralStatus(Enum):
    """General entity status options (clients, etc.)."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"
    
    @classmethod
    def get_all_values(cls) -> List[str]:
        """Get all status values as a list."""
        return [status.value for status in cls]


class TDDPhase(Enum):
    """TDD development phases."""
    RED = "red"
    GREEN = "green"
    REFACTOR = "refactor"
    
    @classmethod
    def get_all_values(cls) -> List[str]:
        """Get all phase values as a list."""
        return [phase.value for phase in cls]


class ClientTier(Enum):
    """Client tier options."""
    BASIC = "basic"
    STANDARD = "standard"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"
    
    @classmethod
    def get_all_values(cls) -> List[str]:
        """Get all tier values as a list."""
        return [tier.value for tier in cls]
    
    @classmethod
    def get_default(cls) -> str:
        """Get default client tier."""
        return cls.STANDARD.value


class CompanySize(Enum):
    """Company size options."""
    STARTUP = "startup"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    ENTERPRISE = "enterprise"
    
    @classmethod
    def get_all_values(cls) -> List[str]:
        """Get all size values as a list."""
        return [size.value for size in cls]
    
    @classmethod
    def get_default(cls) -> str:
        """Get default company size."""
        return cls.STARTUP.value


class Priority(Enum):
    """Task/Epic priority levels."""
    HIGH = 1
    MEDIUM = 2
    LOW = 3
    
    @classmethod
    def get_all_values(cls) -> List[int]:
        """Get all priority values as a list."""
        return [priority.value for priority in cls]
    
    @classmethod
    def get_default(cls) -> int:
        """Get default priority."""
        return cls.MEDIUM.value


# Database Table Names
class TableNames:
    """Database table names."""
    FRAMEWORK_EPICS = "framework_epics"
    FRAMEWORK_TASKS = "framework_tasks"
    FRAMEWORK_USERS = "framework_users"
    TIMER_SESSIONS = "timer_sessions"
    ACHIEVEMENT_TYPES = "achievement_types"
    USER_ACHIEVEMENTS = "user_achievements"
    USER_STREAKS = "user_streaks"
    GITHUB_SYNC_LOG = "github_sync_log"
    SYSTEM_SETTINGS = "system_settings"
    WORK_SESSIONS = "work_sessions"
    CLIENTS = "clients"
    PROJECTS = "projects"


# Database Field Names
class FieldNames:
    """Common database field names."""
    ID = "id"
    NAME = "name"
    DESCRIPTION = "description"
    STATUS = "status"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    DELETED_AT = "deleted_at"
    COMPLETED_AT = "completed_at"
    EPIC_ID = "epic_id"
    TASK_ID = "task_id"
    USER_ID = "user_id"
    PROJECT_ID = "project_id"
    CLIENT_ID = "client_id"
    EPIC_KEY = "epic_key"
    TASK_TITLE = "title"
    TDD_PHASE = "tdd_phase"
    PRIORITY = "priority"
    POINTS_EARNED = "points_earned"
    DIFFICULTY_LEVEL = "difficulty_level"


# UI Constants
class UIConstants:
    """User interface constants."""
    # Page titles
    CLIENTS_PAGE_TITLE = "👥 Client Management"
    PROJECTS_PAGE_TITLE = "📁 Project Management"
    ANALYTICS_PAGE_TITLE = "📊 Analytics Dashboard"
    KANBAN_PAGE_TITLE = "📋 Kanban Board"
    TIMER_PAGE_TITLE = "⏱️ Task Timer"

    # Button text
    EDIT_BUTTON = "✏️ Edit"
    DELETE_BUTTON = "🗑️ Delete"
    CREATE_BUTTON = "🚀 Create"
    SAVE_BUTTON = "💾 Save"
    CANCEL_BUTTON = "❌ Cancel"
    UPDATE_BUTTON = "💾 Update"
    
    # Messages
    SUCCESS_CREATE = "✅ Created successfully!"
    SUCCESS_UPDATE = "✅ Updated successfully!"
    SUCCESS_DELETE = "✅ Deleted successfully!"
    ERROR_GENERIC = "❌ An error occurred"
    ERROR_NOT_FOUND = "❌ Item not found"
    ERROR_INVALID_DATA = "❌ Invalid data provided"
    ERROR_DUPLICATE = "❌ Item already exists"

    # Status icons
    ICON_ACTIVE = "🟢"
    ICON_INACTIVE = "🔴"
    ICON_PENDING = "🟡"
    ICON_COMPLETED = "✅"
    ICON_PLANNING = "🟡"
    ICON_IN_PROGRESS = "🟢"
    ICON_ON_HOLD = "⏸️"
    ICON_CANCELLED = "🔴"
    ICON_UNKNOWN = "⚪"
    ICON_REFACTOR = "🔵"

    # Generic icons
    ICON_EPIC = "📋"
    ICON_TASK = "📝"
    ICON_SEARCH = "🔍"
    ICON_TOTAL = "📊"
    ICON_PAGE = "📄"
    ICON_EMPTY = "📭"

    # Common text
    TEXT_ALL = "Todos"
    TEXT_SELECT = "Selecionar..."
    TEXT_FILTER_BY = "Filtrar por"
    TEXT_SEARCH = "Buscar"
    TEXT_TOTAL = "📊 Total:"
    TEXT_PAGE = "📄 Página"
    TEXT_EMPTY = "📭 Nenhum"
    TEXT_NO_ITEMS = "{icon} Nenhum {entity} encontrado"

    # Modal widths
    MODAL_SMALL = "small"
    MODAL_MEDIUM = "medium"
    MODAL_LARGE = "large"


# Form Field Configurations
class FormFields:
    """Form field configurations."""
    
    CLIENT_FIELDS = {
        "client_key": {
            "label": "Client Key*",
            "placeholder": "e.g., client_xyz",
            "required": True
        },
        "name": {
            "label": "Client Name*",
            "placeholder": "e.g., Company ABC",
            "required": True
        },
        "description": {
            "label": "Description",
            "placeholder": "Brief description of the client...",
            "required": False
        },
        "industry": {
            "label": "Industry",
            "placeholder": "e.g., Technology",
            "required": False
        },
        "primary_contact_name": {
            "label": "Contact Name",
            "placeholder": "e.g., John Doe",
            "required": False
        },
        "primary_contact_email": {
            "label": "Contact Email*",
            "placeholder": "john@company.com",
            "required": True
        },
        "primary_contact_phone": {
            "label": "Contact Phone",
            "placeholder": "+55 (11) 99999-9999",
            "required": False
        }
    }
    
    PROJECT_FIELDS = {
        "name": {
            "label": "Project Name*",
            "placeholder": "e.g., Website Redesign",
            "required": True
        },
        "project_key": {
            "label": "Project Key*",
            "placeholder": "e.g., web_redesign",
            "required": True
        },
        "description": {
            "label": "Description",
            "placeholder": "Project description...",
            "required": False
        }
    }


# Cache Configuration
class CacheConfig:
    """Cache configuration constants."""
    # TTL (Time To Live) values in seconds
    EPICS_TTL = 300  # 5 minutes
    TASKS_TTL = 300  # 5 minutes
    TIMER_SESSIONS_TTL = 60  # 1 minute
    USER_STATS_TTL = 600  # 10 minutes
    ACHIEVEMENTS_TTL = 3600  # 1 hour
    
    # Cache key patterns
    EPICS_PATTERN = "db_query:get_epics:"
    TASKS_PATTERN = "db_query:get_tasks:"
    TIMER_PATTERN = "db_query:get_timer_sessions:"


# Filter Options
class FilterOptions:
    """Opções de filtro com *fallbacks* seguros para enums ausentes."""

    ALL_OPTION = "all"

    @staticmethod
    def _values_or_statusvalues(enum_like) -> List[str]:
        """Usa get_all_values() se existir; caso contrário, usa StatusValues."""
        try:
            return enum_like.get_all_values()  # type: ignore[attr-defined]
        except Exception:
            return StatusValues.get_all_values()

    # Mantém a semântica: se enums específicos existirem, usa; senão, fallback.
    STATUS_FILTERS = {
        "tasks":   [ALL_OPTION] + _values_or_statusvalues.__func__(StatusValues),
        "epics":   [ALL_OPTION] + _values_or_statusvalues.__func__(StatusValues),
        "clients": [ALL_OPTION] + _values_or_statusvalues.__func__(StatusValues),
        "projects":[ALL_OPTION] + _values_or_statusvalues.__func__(StatusValues),
    }

    TIER_FILTERS = [ALL_OPTION] + ClientTiers.get_all_values()
    SIZE_FILTERS = [ALL_OPTION] + CompanySizes.get_all_values()
    TDD_PHASE_FILTERS = [ALL_OPTION] + TDDPhases.get_all_values()


# Validation Rules
class ValidationRules:
    """Data validation rules."""
    
    # String length limits
    MAX_NAME_LENGTH = 100
    MAX_DESCRIPTION_LENGTH = 1000
    MAX_EMAIL_LENGTH = 255
    MAX_PHONE_LENGTH = 20
    MIN_KEY_LENGTH = 3
    MAX_KEY_LENGTH = 50
    
    # Numeric limits
    MIN_PRIORITY = 1
    MAX_PRIORITY = 3
    MIN_HOURLY_RATE = 0.0
    MAX_HOURLY_RATE = 10000.0
    MIN_DURATION_MINUTES = 1
    MAX_DURATION_MINUTES = 480  # 8 hours
    
    # Regex patterns
    EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    PHONE_PATTERN = r'^[\+]?[1-9][\d]{0,15}$'
    KEY_PATTERN = r'^[a-zA-Z][a-zA-Z0-9_]*$'


# ──────────────────────────────────────────────────────────────────────────────
# Aliases para compatibilidade com importações existentes no pacote:
#   - GeneralStatus → StatusValues
#   - TDDPhase      → TDDPhases
#   - ClientTier    → ClientTiers
#   - CompanySize   → CompanySizes
# Obs.: Aliases para TaskStatus/EpicStatus/ProjectStatus não são criados aqui
# por falta de definição original; filtros usam fallback seguro acima.
# ──────────────────────────────────────────────────────────────────────────────
GeneralStatus = StatusValues
TDDPhase = TDDPhases
ClientTier = ClientTiers
CompanySize = CompanySizes

__all__ = [
    'StatusValues', 'GeneralStatus',
    'TDDPhases', 'TDDPhase',
    'ClientTiers', 'ClientTier',
    'CompanySizes', 'CompanySize',
    'ErrorMessages',
    'FormFields', 'CacheConfig', 'FilterOptions', 'ValidationRules'
]