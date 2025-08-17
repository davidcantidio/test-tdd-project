from __future__ import annotations

from typing import Optional, Protocol, runtime_checkable

from streamlit_extension.utils.database import DatabaseManager  # type: ignore

_DBM_INSTANCE: DatabaseManager | None = None  # type: ignore


@runtime_checkable
class _DBProto(Protocol):
    def seed_initial_data(self, kind: Optional[str] = None) -> int: ...


def set_database_manager(dbm: DatabaseManager) -> None:
    """Helper para injetar um ``DatabaseManager`` (ex.: testes/mocks)."""

    global _DBM_INSTANCE
    _DBM_INSTANCE = dbm  # type: ignore


def _db() -> DatabaseManager:
    global _DBM_INSTANCE  # type: ignore
    try:
        return _DBM_INSTANCE  # type: ignore
    except NameError:
        _DBM_INSTANCE = DatabaseManager()  # type: ignore
        return _DBM_INSTANCE


def seed_initial_data(kind: Optional[str] = None) -> int:
    """Insere dados de seed; retorna nº aproximado de registros afetados."""

    db = _db()
    if hasattr(db, "seed_initial_data"):
        val = db.seed_initial_data(kind=kind)  # type: ignore[attr-defined]
        return int(val or 0)
    # fallback previsível
    return 0

