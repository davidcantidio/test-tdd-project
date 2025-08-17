from __future__ import annotations

from streamlit_extension.utils.database import DatabaseManager  # type: ignore

_DBM_INSTANCE: DatabaseManager | None = None  # type: ignore


def set_database_manager(dbm: DatabaseManager) -> None:
    """Permite injetar um ``DatabaseManager`` (ex.: testes)."""

    global _DBM_INSTANCE
    _DBM_INSTANCE = dbm  # type: ignore


def _db() -> DatabaseManager:
    global _DBM_INSTANCE  # type: ignore
    try:
        return _DBM_INSTANCE  # type: ignore
    except NameError:
        _DBM_INSTANCE = DatabaseManager()  # type: ignore
        return _DBM_INSTANCE


def create_schema_if_needed(verbose: bool = False) -> None:
    """
    Ponto central de DDL.
    Fase 1: delega para o manager (se existir).
    """

    db = _db()
    if hasattr(db, "create_schema_if_needed"):
        db.create_schema_if_needed(verbose=verbose)  # type: ignore[attr-defined]

