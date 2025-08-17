from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from streamlit_extension.utils.database import DatabaseManager  # type: ignore

_DBM_INSTANCE: DatabaseManager | None = None  # type: ignore


def _db() -> DatabaseManager:
    global _DBM_INSTANCE  # type: ignore
    try:
        return _DBM_INSTANCE  # type: ignore
    except NameError:
        _DBM_INSTANCE = DatabaseManager()  # type: ignore
        return _DBM_INSTANCE


def check_health() -> Dict[str, Any]:
    """Health-check do banco via manager."""

    return _db().check_database_health()


def get_query_stats() -> Dict[str, Any]:
    """Estatísticas de queries conforme implementado no manager."""

    return _db().get_query_statistics()


def optimize() -> Dict[str, Any]:
    """Executa rotinas de otimização do banco (VACUUM/ANALYZE/etc.)."""

    return _db().optimize_database()


def create_backup(path: str) -> str:
    """Cria backup no caminho informado. Garante diretório existente."""

    p = Path(path)
    if p.parent and not p.parent.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
    return _db().create_backup(str(p))


def restore_backup(path: str) -> str:
    """Restaura backup a partir de um arquivo existente."""

    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Backup não encontrado: {p}")
    return _db().restore_backup(str(p))

