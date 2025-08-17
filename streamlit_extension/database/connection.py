from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterable, Iterator, Optional

# Ajuste o import conforme a localização real do DatabaseManager
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


def get_connection():
    """Obtém uma conexão do manager atual."""

    return _db().get_connection()


def release_connection(conn) -> None:
    """Libera uma conexão obtida via ``get_connection()``."""

    return _db().release_connection(conn)


@contextmanager
def transaction() -> Iterator[Any]:
    """Delegação de transação para o manager atual."""

    with _db().transaction() as tx:
        yield tx


def execute(sql: str, params: Optional[Iterable[Any]] = None) -> Any:
    """Execução genérica de SQL, delegada ao manager."""

    return _db().execute_query(sql, params or ())

