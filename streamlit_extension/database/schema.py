from __future__ import annotations
from typing import Optional
from streamlit_extension.utils.database import DatabaseManager  # type: ignore

def _db() -> DatabaseManager:
    global _DBM_INSTANCE  # type: ignore
    try:
        return _DBM_INSTANCE  # type: ignore
    except NameError:
        _DBM_INSTANCE = DatabaseManager()  # type: ignore
        return _DBM_INSTANCE

def create_schema_if_needed(verbose: bool = False) -> None:
    """
    Fase 1: só delega. Na fase 2, movemos a criação/DDL pra cá de fato.
    """
    # Se o DatabaseManager tiver um método específico para bootstrap/migrations,
    # chame-o aqui. Caso não tenha, mantenha essa função como ponto central
    # para DDLs novas.
    if hasattr(_db(), "create_schema_if_needed"):
        _db().create_schema_if_needed(verbose=verbose)  # type: ignore