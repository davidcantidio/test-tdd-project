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

def seed_initial_data(kind: Optional[str] = None) -> int:
    """
    Insere dados de seed. Fase 1: delega; fase 2: implementar aqui.
    Retorna número de registros afetados (aprox).
    """
    if hasattr(_db(), "seed_initial_data"):
        return int(_db().seed_initial_data(kind=kind) or 0)  # type: ignore
    return 0