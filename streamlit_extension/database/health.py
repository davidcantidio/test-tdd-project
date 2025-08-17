from __future__ import annotations
from typing import Any, Dict
from streamlit_extension.utils.database import DatabaseManager  # type: ignore

def _db() -> DatabaseManager:
    global _DBM_INSTANCE  # type: ignore
    try:
        return _DBM_INSTANCE  # type: ignore
    except NameError:
        _DBM_INSTANCE = DatabaseManager()  # type: ignore
        return _DBM_INSTANCE

def check_health() -> Dict[str, Any]:
    """Wrapper para o health-check do manager."""
    return _db().check_database_health()

def get_query_stats() -> Dict[str, Any]:
    return _db().get_query_statistics()

def optimize() -> Dict[str, Any]:
    return _db().optimize_database()

def create_backup(path: str) -> str:
    return _db().create_backup(path)

def restore_backup(path: str) -> str:
    return _db().restore_backup(path)