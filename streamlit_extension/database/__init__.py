"""Camada de acesso a dados para a extensão Streamlit.

Fase 1: apenas delegação ao `DatabaseManager` existente.
Fase 2: migrar lógicas pesadas dos managers para módulos locais menores.
"""

__version__ = "0.1.0"

from .connection import (
    get_connection,
    release_connection,
    transaction,
    execute,
    set_database_manager as set_dbm,
)
from .health import (
    check_health,
    get_query_stats,
    optimize,
    create_backup,
    restore_backup,
)
from .queries import (
    list_epics,
    list_all_epics,
    list_tasks,
    list_all_tasks,
    list_timer_sessions,
    get_user_stats,
    get_achievements,
)
from .schema import create_schema_if_needed
from .seed import seed_initial_data
# Auth imports
from streamlit_extension.auth.middleware import require_auth, require_admin
from streamlit_extension.auth.user_model import UserRole


__all__ = [
    "get_connection",
    "release_connection",
    "transaction",
    "execute",
    "set_dbm",
    "check_health",
    "get_query_stats",
    "optimize",
    "create_backup",
    "restore_backup",
    "list_epics",
    "list_all_epics",
    "list_tasks",
    "list_all_tasks",
    "list_timer_sessions",
    "get_user_stats",
    "get_achievements",
    "create_schema_if_needed",
    "seed_initial_data",
]

