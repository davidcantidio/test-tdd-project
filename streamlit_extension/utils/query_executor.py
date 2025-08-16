"""
\u26a1 Query Executor - Safe Database Operations

Executes queries built by QueryBuilder with:
- Parameter binding
- Connection management
- Transaction support
- Error handling
- Performance logging
"""

from __future__ import annotations

import logging
import time
from typing import Iterable, List, Tuple, Any

try:  # SQLAlchemy optional
    from sqlalchemy import text
    from sqlalchemy.engine import Connection
    SQLALCHEMY_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency
    text = None  # type: ignore
    Connection = None  # type: ignore
    SQLALCHEMY_AVAILABLE = False

from .query_builder import QueryBuilder

logger = logging.getLogger(__name__)


class QueryExecutor:
    """Executes database queries safely."""

    def __init__(self, db_manager) -> None:
        """Initialize with database manager."""
        self.db_manager = db_manager

    # ------------------------------------------------------------------
    def execute_query(self, query_builder: QueryBuilder) -> Any:
        """Execute query built by QueryBuilder."""
        query, params = query_builder.build()
        start = time.perf_counter()
        with self.db_manager.get_connection("framework") as conn:
            result = self._execute(conn, query_builder.query_type, query, params)
        duration = (time.perf_counter() - start) * 1000
        logger.debug("Executed query in %.2f ms: %s", duration, query)
        return result

    def execute_select(self, query_builder: QueryBuilder) -> List[Tuple[Any, ...]]:
        """Execute SELECT query and return results."""
        return self.execute_query(query_builder)

    def execute_insert(self, query_builder: QueryBuilder) -> Any:
        """Execute INSERT query and return new ID."""
        return self.execute_query(query_builder)

    def execute_update(self, query_builder: QueryBuilder) -> int:
        """Execute UPDATE query and return affected rows."""
        return self.execute_query(query_builder)

    def execute_delete(self, query_builder: QueryBuilder) -> int:
        """Execute DELETE query and return affected rows."""
        return self.execute_query(query_builder)

    def execute_transaction(self, query_builders: Iterable[QueryBuilder]) -> None:
        """Execute multiple queries in transaction."""
        with self.db_manager.get_connection("framework") as conn:
            try:
                for qb in query_builders:
                    query, params = qb.build()
                    self._execute(conn, qb.query_type, query, params)
                if hasattr(conn, "commit"):
                    conn.commit()
            except Exception:
                if hasattr(conn, "rollback"):
                    conn.rollback()
                raise

    # ------------------------------------------------------------------
    def _execute(self, conn, query_type: str | None, query: str, params: Tuple[Any, ...]):
        """Execute a query on the given connection."""
        if SQLALCHEMY_AVAILABLE and isinstance(conn, Connection):  # pragma: no cover
            result = conn.execute(text(query), params)
            if query_type == "SELECT":
                return result.fetchall()
            if query_type == "INSERT":
                return result.lastrowid if hasattr(result, "lastrowid") else None
            return result.rowcount
        else:
            cursor = conn.execute(query, params)
            if query_type == "SELECT":
                return cursor.fetchall()
            if query_type == "INSERT":
                if hasattr(conn, "commit"):
                    conn.commit()
                return cursor.lastrowid
            if query_type in {"UPDATE", "DELETE"}:
                if hasattr(conn, "commit"):
                    conn.commit()
                return cursor.rowcount
            return cursor
