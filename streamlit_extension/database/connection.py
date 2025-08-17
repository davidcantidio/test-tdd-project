from __future__ import annotations
from contextlib import contextmanager
from typing import Any, Iterable, Optional, Tuple

# Ajuste este import conforme a localização do seu arquivo gigante:
# DatabaseManager está em streamlit_extension/utils/database.py
from streamlit_extension.utils.database import DatabaseManager  # type: ignore

def _db() -> DatabaseManager:
    # Estratégia simples: uma instância "global-ish".
    # Se você já tem um factory/singleton, troque aqui.
    # type: ignore para evitar mypy chato neste passo.
    global _DBM_INSTANCE  # type: ignore
    try:
        return _DBM_INSTANCE  # type: ignore
    except NameError:
        _DBM_INSTANCE = DatabaseManager()  # type: ignore
        return _DBM_INSTANCE

def get_connection():
    return _db().get_connection()

def release_connection(conn) -> None:
    return _db().release_connection(conn)

@contextmanager
def transaction():
    # Usa a transação do manager atual
    with _db().transaction() as tx:
        yield tx

def execute(sql: str, params: Optional[Iterable[Any]] = None):
    """Execute genérico, delegando ao manager."""
    return _db().execute_query(sql, params or ())