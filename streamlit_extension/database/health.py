from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Any, Dict, Optional

import sqlite3

# Legado
from streamlit_extension.utils.database import DatabaseManager  # type: ignore

# Modular (fallbacks late-bound para evitar hard deps)
# from streamlit_extension.database import connection as db_connection
# from streamlit_extension.database.health import check_health as modular_check_health
# from streamlit_extension.database import optimize as modular_optimize

logger = logging.getLogger(__name__)

_DBM_INSTANCE: Optional[DatabaseManager] = None  # type: ignore
_DBM_LOCK = threading.Lock()


# ============================================================================
# Singleton do DatabaseManager (com injeção/reset para testes)
# ============================================================================
def set_database_manager(dbm: Optional[DatabaseManager]) -> None:
    """
    Injeta uma instância de DatabaseManager (útil para testes) ou reseta quando None.
    """
    global _DBM_INSTANCE
    with _DBM_LOCK:
        _DBM_INSTANCE = dbm
        logger.debug("DatabaseManager singleton %s", "reset" if dbm is None else "injected")


def get_database_manager() -> DatabaseManager:
    """Exponibiliza a instância atual (cria sob demanda)."""
    return _db()


def _db() -> DatabaseManager:
    """
    Thread-safe singleton pattern para DatabaseManager (double-checked locking).
    """
    global _DBM_INSTANCE
    if _DBM_INSTANCE is not None:
        return _DBM_INSTANCE

    with _DBM_LOCK:
        if _DBM_INSTANCE is None:
            logger.debug("Creating default DatabaseManager singleton")
            _DBM_INSTANCE = DatabaseManager()
        return _DBM_INSTANCE


# ============================================================================
# Health / Stats / Optimize – com fallback para API modular
# ============================================================================
def check_health() -> Dict[str, Any]:
    """
    Health-check do banco.
    Preferência: legado -> modular -> erro estruturado.
    """
    # 1) Tentar legado
    try:
        return _db().check_database_health()
    except Exception as e:
        logger.debug("Legacy health check unavailable/failed: %s", e)

    # 2) Fallback modular
    try:
        from streamlit_extension.database.health import check_health as modular_check_health  # type: ignore
        return modular_check_health()
    except Exception as e:
        logger.warning("Modular health check unavailable/failed: %s", e)

    # 3) Último recurso: retornar erro estruturado
    return {"status": "error", "error": "health_check_unavailable"}


def get_query_stats() -> Dict[str, Any]:
    """
    Estatísticas de queries conforme implementado no manager.
    Fallback: PRAGMAs básicos (page_count, page_size, freelist_count, cache_size).
    """
    # 1) Tentar legado
    try:
        return _db().get_query_statistics()
    except Exception as e:
        logger.debug("Legacy get_query_statistics unavailable/failed: %s", e)

    # 2) Fallback modular via PRAGMA
    try:
        from streamlit_extension.database import connection as db_connection  # type: ignore
        with db_connection.get_connection_context() as conn:
            cur = conn.cursor()
            stats = {}
            for name in ("page_count", "page_size", "freelist_count", "cache_size", "schema_version"):
                try:
                    cur.execute(f"PRAGMA {name};")
                    row = cur.fetchone()
                    stats[name] = int(row[0]) if row and row[0] is not None else None
                except Exception:
                    stats[name] = None
            # tamanho aproximado do arquivo (bytes)
            if stats.get("page_count") and stats.get("page_size"):
                stats["approx_db_size_bytes"] = stats["page_count"] * stats["page_size"]
            return {"status": "ok", "engine": "sqlite", "stats": stats}
    except Exception as e:
        logger.warning("Fallback query stats failed: %s", e)

    return {"status": "error", "error": "query_stats_unavailable"}


def optimize() -> Dict[str, Any]:
    """
    Executa rotinas de otimização (VACUUM/ANALYZE/etc.).
    Preferência: manager. Fallback: modular + PRAGMAs padrão.
    """
    # 1) Tentar legado
    try:
        return _db().optimize_database()
    except Exception as e:
        logger.debug("Legacy optimize unavailable/failed: %s", e)

    # 2) Tentar modular helper explícito
    try:
        from streamlit_extension.database import optimize as modular_optimize  # type: ignore
        return modular_optimize() or {"status": "ok", "via": "modular_optimize"}
    except Exception as e:
        logger.debug("Modular optimize helper unavailable: %s", e)

    # 3) Fallback: comandos diretos
    try:
        from streamlit_extension.database import connection as db_connection  # type: ignore
        actions: list[str] = []
        with db_connection.get_connection_context() as conn:
            conn.execute("PRAGMA analysis_limit=400;")
            actions.append("PRAGMA analysis_limit=400")
            conn.execute("ANALYZE;")
            actions.append("ANALYZE")
            # VACUUM exige conexão sem transação ativa
        # VACUUM fora do 'with' para garantir fechamento e reabertura rápida
        with db_connection.get_connection_context() as conn2:
            conn2.execute("VACUUM;")
            actions.append("VACUUM")
        return {"status": "ok", "via": "fallback", "actions": actions}
    except Exception as e:
        logger.error("Optimize fallback failed: %s", e, exc_info=True)
        return {"status": "error", "error": str(e)}


# ============================================================================
# Backup / Restore – preferir manager; fallback: SQLite Backup API
# ============================================================================
def create_backup(path: str) -> str:
    """
    Cria backup no caminho informado.
    - Se 'path' aponta para diretório, gera nome com timestamp.
    - Garante diretório existente.
    - Preferência: método do manager; fallback: SQLite Backup API.
    """
    p = Path(path)
    if p.suffix == "" or p.is_dir():
        # Diretório ou caminho sem extensão -> gerar nome
        p.mkdir(parents=True, exist_ok=True)
        fname = f"framework_backup_{_safe_timestamp()}.db"
        p = p / fname
    else:
        if p.parent:
            p.parent.mkdir(parents=True, exist_ok=True)

    # 1) Tentar legado
    try:
        out = _db().create_backup(str(p))
        return str(out or p)
    except Exception as e:
        logger.debug("Legacy create_backup unavailable/failed: %s", e)

    # 2) Fallback: SQLite Backup API via conexão modular
    try:
        from streamlit_extension.database import connection as db_connection  # type: ignore
        with db_connection.get_connection_context() as live_conn:
            # Conexão destino (arquivo backup)
            with sqlite3.connect(str(p)) as backup_conn:
                # Copia conteúdo do live_conn para backup_conn
                live_conn.backup(backup_conn)
        return str(p)
    except Exception as e:
        logger.error("Backup fallback failed: %s", e, exc_info=True)
        raise


def restore_backup(path: str) -> str:
    """
    Restaura backup a partir de um arquivo existente.
    Preferência: método do manager; fallback: SQLite Backup API (copia do arquivo para a DB ativa).
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Backup não encontrado: {p}")

    # 1) Tentar legado
    try:
        out = _db().restore_backup(str(p))
        return str(out or p)
    except Exception as e:
        logger.debug("Legacy restore_backup unavailable/failed: %s", e)

    # 2) Fallback: SQLite Backup API (backup -> live)
    try:
        from streamlit_extension.database import connection as db_connection  # type: ignore
        # Destino: conexão atual (live)
        with db_connection.get_connection_context() as live_conn:
            # Origem: arquivo de backup
            with sqlite3.connect(str(p)) as src_conn:
                # Copia do src (arquivo) -> live (conexão ativa)
                src_conn.backup(live_conn)
        return str(p)
    except Exception as e:
        logger.error("Restore fallback failed: %s", e, exc_info=True)
        raise


# ============================================================================
# Utils
# ============================================================================
def _safe_timestamp() -> str:
    # YYYYMMDD_HHMMSS para nomes de arquivo
    from datetime import datetime
    return datetime.utcnow().strftime("%Y%m%d_%H%M%S")
