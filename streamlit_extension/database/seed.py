from __future__ import annotations

from typing import Optional, Protocol, runtime_checkable

# Legacy import - keeping for hybrid compatibility
from streamlit_extension.utils.database import DatabaseManager  # Legacy compatibility

_DBM_INSTANCE: DatabaseManager | None = None  # type: ignore


@runtime_checkable
class _DBProto(Protocol):
    def seed_initial_data(self, kind: Optional[str] = None) -> int: ...


def set_database_manager(dbm: DatabaseManager) -> None:
    """Helper para injetar um ``DatabaseManager`` (ex.: testes/mocks)."""

    global _DBM_INSTANCE
    _DBM_INSTANCE = dbm  # type: ignore


# SEMANTIC DEDUPLICATION: Use centralized singleton instead of duplicate implementation
from .database_singleton import get_database_manager as _db
# Auth imports
from streamlit_extension.auth.middleware import require_auth, require_admin
from streamlit_extension.auth.user_model import UserRole


def seed_initial_data(kind: Optional[str] = None) -> int:
    """Insere dados de seed; retorna nº aproximado de registros afetados."""

    db = _db()
    if hasattr(db, "seed_initial_data"):
        val = db.seed_initial_data(kind=kind)  # type: ignore[attr-defined]
        return int(val or 0)
    # fallback previsível
    return 0