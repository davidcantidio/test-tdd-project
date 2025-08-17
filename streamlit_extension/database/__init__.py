"""
Pacote de DB, fase 1: finas camadas que delegam ao DatabaseManager existente.
Na fase 2, vamos mover os métodos para cá e emagrecer o arquivo gigante.
"""
from .connection import get_connection, release_connection, transaction, execute
from .health import check_health, get_query_stats, optimize, create_backup, restore_backup
from .queries import (
    list_epics, list_all_epics, list_tasks, list_all_tasks,
    list_timer_sessions, get_user_stats, get_achievements,
)
from .schema import create_schema_if_needed
from .seed import seed_initial_data

__all__ = [
    "get_connection", "release_connection", "transaction", "execute",
    "check_health", "get_query_stats", "optimize", "create_backup", "restore_backup",
    "list_epics", "list_all_epics", "list_tasks", "list_all_tasks",
    "list_timer_sessions", "get_user_stats", "get_achievements",
    "create_schema_if_needed", "seed_initial_data",
]