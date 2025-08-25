from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Any, Dict, Optional

import sqlite3

# Modular imports for database health operations
from .connection import get_connection_context, execute_cached_query

# Modular (fallbacks late-bound para evitar hard deps)
# from streamlit_extension.database import connection as db_connection
# from streamlit_extension.database.health import check_health as modular_check_health
# from streamlit_extension.database import optimize as modular_optimize

logger = logging.getLogger(__name__)

# Removed legacy DatabaseManager dependencies


# ============================================================================
# Singleton do DatabaseManager (com injeção/reset para testes)
# ============================================================================
def set_database_manager(dbm: Optional[Any]) -> None:
    """
    Legacy compatibility function - no longer needed with modular architecture.
    """
    # This function is kept for API compatibility but does nothing
    logger.debug("set_database_manager called - no-op in modular architecture")


def get_database_manager() -> Any:
    """Legacy compatibility function - returns None in modular architecture."""
    logger.warning("get_database_manager is deprecated - use modular database functions instead")
    return None


# Removed database_singleton dependency - using direct modular implementation


# ============================================================================
# Health / Stats / Optimize – com fallback para API modular
# ============================================================================
def check_health() -> Dict[str, Any]:
    """
    Health-check do banco usando conexão direta modular.
    """
    try:
        with get_connection_context() as conn:
            # Test basic connectivity
            cursor = conn.execute("SELECT 1")
            basic_test = cursor.fetchone()
            
            if not basic_test or basic_test[0] != 1:
                return {"status": "error", "error": "basic_connectivity_failed"}
            
            # Get database statistics
            stats = {}
            pragmas = ["page_count", "page_size", "freelist_count", "cache_size", "schema_version"]
            
            for pragma in pragmas:
                try:
                    cursor = conn.execute(f"PRAGMA {pragma}")
                    result = cursor.fetchone()
                    stats[pragma] = int(result[0]) if result and result[0] is not None else 0
                except Exception as e:
                    logger.debug(f"Failed to get {pragma}: {e}")
                    stats[pragma] = None
            
            # Calculate approximate database size
            if stats.get("page_count") and stats.get("page_size"):
                stats["approx_db_size_bytes"] = stats["page_count"] * stats["page_size"]
            
            return {
                "status": "healthy",
                "engine": "sqlite", 
                "stats": stats,
                "connection_pool": "optimized"
            }
            
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return {"status": "error", "error": str(e)}


def get_query_stats() -> Dict[str, Any]:
    """
    Estatísticas de queries usando conexão direta modular.
    """
    try:
        with get_connection_context() as conn:
            cur = conn.cursor()
            stats = {}
            
            # Get basic database statistics
            pragmas = ["page_count", "page_size", "freelist_count", "cache_size", "schema_version",
                      "journal_mode", "synchronous", "temp_store", "auto_vacuum"]
            
            for pragma in pragmas:
                try:
                    cur.execute(f"PRAGMA {pragma}")
                    row = cur.fetchone()
                    if pragma in ["page_count", "page_size", "freelist_count", "cache_size", "schema_version"]:
                        stats[pragma] = int(row[0]) if row and row[0] is not None else 0
                    else:
                        stats[pragma] = row[0] if row else None
                except Exception as e:
                    logger.debug(f"Failed to get {pragma}: {e}")
                    stats[pragma] = None
            
            # Calculate approximate database size
            if stats.get("page_count") and stats.get("page_size"):
                stats["approx_db_size_bytes"] = stats["page_count"] * stats["page_size"]
                stats["approx_db_size_mb"] = round(stats["approx_db_size_bytes"] / (1024 * 1024), 2)
            
            # Get table count
            try:
                cur.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
                result = cur.fetchone()
                stats["table_count"] = int(result[0]) if result else 0
            except Exception:
                stats["table_count"] = None
            
            return {
                "status": "ok", 
                "engine": "sqlite", 
                "connection_type": "modular_optimized",
                "stats": stats
            }
            
    except Exception as e:
        logger.error(f"Query stats failed: {e}", exc_info=True)
        return {"status": "error", "error": str(e)}


def optimize() -> Dict[str, Any]:
    """
    Executa rotinas de otimização usando conexão direta modular (VACUUM/ANALYZE/etc.).
    """
    try:
        actions: list[str] = []
        
        # Step 1: ANALYZE with limit to avoid long-running queries
        with get_connection_context() as conn:
            conn.execute("PRAGMA analysis_limit=400")
            actions.append("PRAGMA analysis_limit=400")
            conn.execute("ANALYZE")
            actions.append("ANALYZE")
        
        # Step 2: VACUUM (requires separate connection without active transaction)
        with get_connection_context() as conn:
            conn.execute("VACUUM")
            actions.append("VACUUM")
        
        # Step 3: Update statistics and check integrity
        with get_connection_context() as conn:
            # Quick integrity check
            cursor = conn.execute("PRAGMA quick_check(1)")
            integrity_result = cursor.fetchone()
            integrity_ok = integrity_result and integrity_result[0] == "ok"
            
            # Optimize WAL checkpoint
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            actions.append("PRAGMA wal_checkpoint(TRUNCATE)")
        
        return {
            "status": "ok", 
            "via": "modular_direct", 
            "actions": actions,
            "integrity_check": "ok" if integrity_ok else "warning"
        }
        
    except Exception as e:
        logger.error(f"Database optimization failed: {e}", exc_info=True)
        return {"status": "error", "error": str(e)}


# ============================================================================
# Backup / Restore – preferir manager; fallback: SQLite Backup API
# ============================================================================
def create_backup(path: str) -> str:
    """
    Cria backup usando SQLite Backup API modular.
    - Se 'path' aponta para diretório, gera nome com timestamp.
    - Garante diretório existente.
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

    try:
        # Use SQLite Backup API directly with modular connection
        with get_connection_context() as live_conn:
            # Create backup connection
            with sqlite3.connect(str(p)) as backup_conn:
                # Copy content from live_conn to backup_conn
                live_conn.backup(backup_conn, pages=1000)  # Copy in chunks for better performance
        
        logger.info(f"Database backup created successfully: {p}")
        return str(p)
        
    except Exception as e:
        logger.error(f"Database backup failed: {e}", exc_info=True)
        raise RuntimeError(f"Failed to create backup: {e}") from e


def restore_backup(path: str) -> str:
    """
    Restaura backup usando SQLite Backup API modular.
    Copia do arquivo de backup para a database ativa.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Backup não encontrado: {p}")

    try:
        # Use SQLite Backup API directly with modular connection  
        with get_connection_context() as live_conn:
            # Open source backup file
            with sqlite3.connect(str(p)) as src_conn:
                # Copy from backup file to live database
                # Note: src.backup(dest) copies FROM src TO dest
                src_conn.backup(live_conn, pages=1000)  # Restore in chunks for better performance
        
        logger.info(f"Database restored successfully from: {p}")
        return str(p)
        
    except Exception as e:
        logger.error(f"Database restore failed: {e}", exc_info=True)
        raise RuntimeError(f"Failed to restore backup: {e}") from e


# ============================================================================
# Utils
# ============================================================================
def _safe_timestamp() -> str:
    # YYYYMMDD_HHMMSS para nomes de arquivo
    from datetime import datetime
    return datetime.utcnow().strftime("%Y%m%d_%H%M%S")