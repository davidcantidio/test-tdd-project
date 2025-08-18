from __future__ import annotations

import threading
import logging
from typing import Optional, Protocol, runtime_checkable

# Legado
from streamlit_extension.utils.database import DatabaseManager  # type: ignore

logger = logging.getLogger(__name__)

_DBM_INSTANCE: Optional[DatabaseManager] = None  # type: ignore
_DBM_LOCK = threading.Lock()


@runtime_checkable
class _SchemaCreator(Protocol):
    def create_schema_if_needed(self, *, verbose: bool = False) -> None: ...


def set_database_manager(dbm: Optional[DatabaseManager]) -> None:
    """
    Injeta uma instância de ``DatabaseManager`` (útil para testes) ou reseta quando None.

    Args:
        dbm: Instância a ser utilizada como singleton; se None, limpa o singleton.
    """
    global _DBM_INSTANCE
    with _DBM_LOCK:
        if dbm is None:
            logger.debug("Resetting DatabaseManager singleton to None")
            _DBM_INSTANCE = None
        else:
            if not isinstance(dbm, DatabaseManager):  # type: ignore[arg-type]
                raise TypeError("dbm must be an instance of DatabaseManager")
            _DBM_INSTANCE = dbm
            logger.debug("Injected custom DatabaseManager singleton")


def get_database_manager() -> DatabaseManager:
    """Retorna a instância singleton atual do DatabaseManager (criando sob demanda)."""
    return _db()


def _db() -> DatabaseManager:
    """
    Thread-safe singleton para DatabaseManager (double-checked locking).
    """
    global _DBM_INSTANCE
    if _DBM_INSTANCE is not None:
        return _DBM_INSTANCE

    with _DBM_LOCK:
        if _DBM_INSTANCE is None:
            logger.debug("Creating default DatabaseManager singleton")
            _DBM_INSTANCE = DatabaseManager()
        return _DBM_INSTANCE


def create_schema_if_needed(verbose: bool = False) -> None:
    """
    Ponto central de DDL (schema do framework).

    Estratégia:
      1) Se o DatabaseManager legado expõe `create_schema_if_needed`, delega para ele.
      2) Caso contrário, tenta a API modular (`streamlit_extension.database.create_schema_if_needed`).
      3) Se ambas indisponíveis, registra aviso (sem lançar exceção para não quebrar bootstrap).
    """
    db = _db()

    # Primeiro: tentar no legado, se disponível
    if isinstance(db, _SchemaCreator) or hasattr(db, "create_schema_if_needed"):
        try:
            if verbose:
                logger.info("Creating/upgrading schema via legacy DatabaseManager...")
            # type: ignore[attr-defined]
            db.create_schema_if_needed(verbose=verbose)
            if verbose:
                logger.info("Schema created/verified via legacy DatabaseManager.")
            return
        except Exception as e:
            logger.warning("Legacy create_schema_if_needed failed: %s", e, exc_info=verbose)

    # Fallback: tentar a API modular
    try:
        from streamlit_extension.database import create_schema_if_needed as modular_create  # type: ignore

        if verbose:
            logger.info("Creating/upgrading schema via modular API...")
        modular_create()  # modular não requer 'verbose' por padrão
        if verbose:
            logger.info("Schema created/verified via modular API.")
        return
    except Exception as e:
        logger.warning("Modular create_schema_if_needed unavailable or failed: %s", e, exc_info=verbose)

    # Último recurso: não faz nada (apenas loga)
    logger.error(
        "No schema creation path succeeded. Ensure either the legacy DatabaseManager "
        "or the modular database API provides a schema creation routine."
    )
