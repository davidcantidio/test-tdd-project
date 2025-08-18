from __future__ import annotations

import atexit
import os
import sqlite3
import threading
import time
from collections import OrderedDict, deque
from contextlib import contextmanager
from typing import Any, Dict, Iterable, Iterator, Optional, Tuple

# Ajuste o import conforme a localização real do DatabaseManager
from streamlit_extension.utils.database import DatabaseManager  # type: ignore

# =============================================================================
# Config & Utils
# =============================================================================

_DBM_INSTANCE: Optional[DatabaseManager] = None  # type: ignore
_DBM_LOCK = threading.Lock()

DEFAULT_DB_FILENAME = "framework.db"
ENV_DB_PATH = "FRAMEWORK_DB"

def _resolve_db_path() -> str:
    """
    Resolve o caminho do banco. Ordem:
    1) Variável de ambiente FRAMEWORK_DB (pode ser caminho absoluto)
    2) Arquivo 'framework.db' no diretório atual
    """
    env = os.environ.get(ENV_DB_PATH)
    if env:
        return env
    return os.path.join(os.getcwd(), DEFAULT_DB_FILENAME)


def _configure_sqlite_connection(conn: sqlite3.Connection) -> None:
    """
    Configura a conexão para melhor concorrência e ergonomia.
    """
    conn.row_factory = sqlite3.Row
    # Aumenta tolerância a locks (segundos)
    conn.execute("PRAGMA busy_timeout = 5000;")
    # WAL melhora concorrência de leitura
    conn.execute("PRAGMA journal_mode = WAL;")
    # Sincronização mais segura por padrão (pode ser ajustado conforme ambiente)
    conn.execute("PRAGMA synchronous = NORMAL;")
    # Foreign keys ON
    conn.execute("PRAGMA foreign_keys = ON;")


def _new_sqlite_connection() -> sqlite3.Connection:
    """
    Cria uma nova conexão SQLite com configurações padrão do módulo.
    """
    conn = sqlite3.connect(
        _resolve_db_path(),
        detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
        # Segurança: cada thread tem sua própria conexão; check_same_thread=True é adequado.
        check_same_thread=True,
    )
    _configure_sqlite_connection(conn)
    return conn


# =============================================================================
# DatabaseManager (Singleton Delegation)
# =============================================================================

def set_database_manager(dbm: DatabaseManager) -> None:
    """Permite injetar um ``DatabaseManager`` (ex.: testes)."""
    global _DBM_INSTANCE
    _DBM_INSTANCE = dbm  # type: ignore


def _db() -> DatabaseManager:
    """
    Thread-safe singleton para DatabaseManager (double-checked locking).
    """
    global _DBM_INSTANCE
    if _DBM_INSTANCE is not None:
        return _DBM_INSTANCE

    with _DBM_LOCK:
        if _DBM_INSTANCE is None:
            _DBM_INSTANCE = DatabaseManager()
        return _DBM_INSTANCE


def get_connection() -> Any:
    """Obtém uma conexão do manager atual."""
    return _db().get_connection()


def release_connection(conn: Any) -> None:
    """Libera uma conexão obtida via ``get_connection()``."""
    _db().release_connection(conn)


@contextmanager
def transaction() -> Iterator[Any]:
    """Delegação de transação para o manager atual."""
    with _db().transaction() as tx:
        yield tx


@contextmanager
def get_connection_context() -> Iterator[sqlite3.Connection]:
    """
    Context manager para obter conexão direta ao SQLite do framework.
    Útil para ferramentas ou scripts utilitários.
    """
    conn = _new_sqlite_connection()
    try:
        yield conn
    finally:
        conn.close()


def _is_select(sql: str) -> bool:
    return sql.lstrip().upper().startswith("SELECT")


def execute(sql: str, params: Optional[Iterable[Any]] = None) -> Any:
    """
    Execução genérica de SQL, delegada ao manager.
    - Invalida o cache global quando detectar uma operação não-SELECT.
    """
    result = _db().execute_query(sql, tuple(params or ()))
    if not _is_select(sql):
        _optimized_pool.clear_cache()
    return result


# =============================================================================
# Optimized Connection Pool + Query Cache
# =============================================================================

class OptimizedConnectionPool:
    """
    Pool de conexões de alta performance, thread-safe, com:
    - Reuso por thread_id (compatível com check_same_thread=True do SQLite)
    - Limite de conexões com evicção LRU
    - Limpeza por timeout de inatividade (TTL)
    - Cache LRU de resultados SELECT com TTL
    - Métricas de operação
    """

    def __init__(
        self,
        max_connections: int = 10,
        connection_timeout: int = 300,
        query_cache_capacity: int = 256,
    ) -> None:
        self.max_connections = max_connections
        self.connection_timeout = connection_timeout

        # Pool: thread_id -> info
        self._pool: Dict[int, Dict[str, Any]] = {}
        self._pool_lock = threading.RLock()

        # LRU para acompanhar ordem de uso de threads (para evicção por limite)
        self._lru_threads: deque[int] = deque()

        # Cache LRU para SELECTs
        self._cache_lock = threading.RLock()
        self._query_cache: "OrderedDict[str, Dict[str, Any]]" = OrderedDict()
        self._query_cache_capacity = query_cache_capacity

        # Métricas
        self._metrics_lock = threading.RLock()
        self._metrics: Dict[str, Any] = {
            "connections_created": 0,
            "connections_reused": 0,
            "connections_closed": 0,
            "cache_hits": 0,
            "cache_misses": 0,
        }

        self._last_cleanup = time.time()
        atexit.register(self._close_all)

    # ---------- Pool de Conexões ----------

    def _lru_touch(self, thread_id: int) -> None:
        # move thread_id para o final (mais recentemente usado)
        try:
            self._lru_threads.remove(thread_id)
        except ValueError:
            pass
        self._lru_threads.append(thread_id)

    def _evict_if_needed(self) -> None:
        # Evict LRU enquanto exceder max_connections
        while len(self._pool) > self.max_connections and self._lru_threads:
            victim_tid = self._lru_threads.popleft()
            info = self._pool.pop(victim_tid, None)
            if info:
                try:
                    info["connection"].close()
                except Exception:
                    pass
                with self._metrics_lock:
                    self._metrics["connections_closed"] += 1

    def _cleanup_old_connections(self) -> None:
        """Fecha conexões não usadas por além do TTL."""
        current_time = time.time()
        with self._pool_lock:
            stale_tids: list[int] = []
            for tid, info in self._pool.items():
                if current_time - info["last_used"] > self.connection_timeout:
                    try:
                        info["connection"].close()
                    except Exception:
                        pass
                    stale_tids.append(tid)

            for tid in stale_tids:
                self._pool.pop(tid, None)
                try:
                    self._lru_threads.remove(tid)
                except ValueError:
                    pass
                with self._metrics_lock:
                    self._metrics["connections_closed"] += 1

        self._last_cleanup = current_time

    @contextmanager
    def get_optimized_connection(self) -> Iterator[sqlite3.Connection]:
        """
        Fornece uma conexão otimizada para o thread atual.
        - Reuso por thread_id
        - Evicção LRU se exceder o limite
        - Cleanup periódico por TTL
        - Rollback automático em exceção com transação aberta
        """
        tid = threading.get_ident()
        do_cleanup = False

        with self._pool_lock:
            info = self._pool.get(tid)
            if info:
                conn = info["connection"]
                info["last_used"] = time.time()
                self._lru_touch(tid)
                with self._metrics_lock:
                    self._metrics["connections_reused"] += 1
            else:
                conn = _new_sqlite_connection()
                now = time.time()
                self._pool[tid] = {
                    "connection": conn,
                    "created_at": now,
                    "last_used": now,
                }
                self._lru_touch(tid)
                with self._metrics_lock:
                    self._metrics["connections_created"] += 1

            # Evicção por excesso
            self._evict_if_needed()
            # Cleanup periódico (a cada 60s)
            if time.time() - self._last_cleanup > 60:
                do_cleanup = True

        if do_cleanup:
            self._cleanup_old_connections()

        try:
            yield conn
        except Exception:
            # Se houver transação aberta, realiza rollback por segurança
            try:
                if conn.in_transaction:
                    conn.rollback()
            except Exception:
                pass
            # Conexão problemática? Retira do pool deste thread
            with self._pool_lock:
                self._pool.pop(tid, None)
                try:
                    self._lru_threads.remove(tid)
                except ValueError:
                    pass
            raise
        finally:
            # Marca último uso
            with self._pool_lock:
                if tid in self._pool:
                    self._pool[tid]["last_used"] = time.time()
                    self._lru_touch(tid)

    def _close_all(self) -> None:
        """Fecha todas as conexões do pool (atexit)."""
        with self._pool_lock:
            for tid, info in list(self._pool.items()):
                try:
                    info["connection"].close()
                except Exception:
                    pass
                with self._metrics_lock:
                    self._metrics["connections_closed"] += 1
            self._pool.clear()
            self._lru_threads.clear()

    # ---------- Cache de Consultas (SELECT) ----------

    def _make_cache_key(self, sql: str, params: Optional[Tuple[Any, ...]]) -> str:
        safe_params = tuple(params or ())
        return f"{sql}|{safe_params!r}"

    def clear_cache(self) -> None:
        with self._cache_lock:
            self._query_cache.clear()

    def execute_cached(
        self,
        sql: str,
        params: Optional[Iterable[Any]] = None,
        cache_ttl: int = 60,
    ) -> list[dict]:
        """
        Executa SELECT com cache LRU controlado por TTL.
        - Apenas SELECT é cacheado.
        - Resultados são convertidos para lista de dicts.
        """
        if not _is_select(sql):
            # Não cachear; executar direto com conexão do pool
            with self.get_optimized_connection() as conn:
                cur = conn.execute(sql, tuple(params or ()))
                if cur.description:
                    cols = [c[0] for c in cur.description]
                    return [dict(zip(cols, row)) for row in cur.fetchall()]
                return []

        now = time.time()
        key = self._make_cache_key(sql, tuple(params or ()))

        with self._cache_lock:
            if key in self._query_cache:
                item = self._query_cache[key]
                if now - item["ts"] < cache_ttl:
                    # hit
                    self._query_cache.move_to_end(key)
                    with self._metrics_lock:
                        self._metrics["cache_hits"] += 1
                    return item["data"]
                # expirado
                del self._query_cache[key]

        # miss
        with self._metrics_lock:
            self._metrics["cache_misses"] += 1

        with self.get_optimized_connection() as conn:
            cur = conn.execute(sql, tuple(params or ()))
            if cur.description:
                cols = [c[0] for c in cur.description]
                data = [dict(zip(cols, row)) for row in cur.fetchall()]
            else:
                data = []

        with self._cache_lock:
            self._query_cache[key] = {"data": data, "ts": now}
            # Evict LRU se necessário
            while len(self._query_cache) > self._query_cache_capacity:
                self._query_cache.popitem(last=False)

        return data

    # ---------- Métricas ----------

    def get_performance_metrics(self) -> Dict[str, Any]:
        with self._pool_lock, self._cache_lock, self._metrics_lock:
            total_cache = self._metrics["cache_hits"] + self._metrics["cache_misses"]
            hit_rate = (self._metrics["cache_hits"] / total_cache * 100) if total_cache else 0.0
            return {
                **self._metrics,
                "active_connections": len(self._pool),
                "lru_size": len(self._lru_threads),
                "cache_entries": len(self._query_cache),
                "cache_hit_rate": round(hit_rate, 2),
                "db_path": _resolve_db_path(),
            }


# Instância global do pool otimizado
_optimized_pool = OptimizedConnectionPool()


# =============================================================================
# Facade Helpers
# =============================================================================

def get_optimized_connection() -> Iterator[sqlite3.Connection]:
    """Atalho para obter conexão do pool (context manager)."""
    return _optimized_pool.get_optimized_connection()


def execute_cached_query(
    sql: str,
    params: Optional[Iterable[Any]] = None,
    cache_ttl: int = 60,
) -> list[dict]:
    """Executa SELECT com cache por TTL."""
    return _optimized_pool.execute_cached(sql, params, cache_ttl)


def invalidate_cache() -> None:
    """Invalida todo o cache de consultas."""
    _optimized_pool.clear_cache()


def get_connection_metrics() -> Dict[str, Any]:
    """Retorna métricas de performance do pool e cache."""
    return _optimized_pool.get_performance_metrics()
