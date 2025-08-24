"""
\U0001f527 SQL Query Builder - Type-Safe Database Operations

Replaces ad-hoc SQL strings with structured query building:
- Fluent interface for query construction
- SQL injection prevention
- Type safety
- Query optimization
- Debug logging
- Performance metrics
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Sequence, Tuple
import re
from streamlit_extension.auth.middleware import require_auth, require_admin
from streamlit_extension.auth.user_model import UserRole


class QueryBuilder:
    # Delegation to QueryBuilderValidation
    def __init__(self):
        self._querybuildervalidation = QueryBuilderValidation()
    # Delegation to QueryBuilderErrorhandling
    def __init__(self):
        self._querybuildererrorhandling = QueryBuilderErrorhandling()
    # Delegation to QueryBuilderFormatting
    def __init__(self):
        self._querybuilderformatting = QueryBuilderFormatting()
    # Delegation to QueryBuilderDataaccess
    def __init__(self):
        self._querybuilderdataaccess = QueryBuilderDataaccess()
    # Delegation to QueryBuilderCalculation
    def __init__(self):
        self._querybuildercalculation = QueryBuilderCalculation()
    """Fluent interface SQL query builder."""

    def __init__(self, table_name: str) -> None:
        """Initialize query builder for specific table."""
        self.table = table_name
        self.query_type: str | None = None
        self.columns: List[str] = []
        self.conditions: List[str] = []
        self.joins: List[str] = []
        self._order_by: List[str] = []
        self._group_by: List[str] = []
        self._having: List[str] = []
        self.limit_value: int | None = None
        self.offset_value: int | None = None
        self.values: Dict[str, Any] = {}
        self.parameters: List[Any] = []
        self._identifier_re = re.compile(r"^[A-Za-z_][A-Za-z0-9_\.]*$")

    # ------------------------- helpers -------------------------
    def _safe_ident(self, ident: str) -> str:
        """Valida identificadores simples (tabela/coluna/direção)."""
        if not self._identifier_re.fullmatch(ident):
            raise ValueError(f"Unsafe SQL identifier: {ident!r}")
        return ident

    def _safe_direction(self, direction: str) -> str:
        d = direction.upper()
        if d not in {"ASC", "DESC"}:
            raise ValueError("Order direction must be ASC or DESC")
        return d

    # ------------------------------------------------------------------
    # Core query construction methods
    # ------------------------------------------------------------------
    def select(self, *columns: str) -> "QueryBuilder":
        """Add SELECT columns."""
        self.query_type = "SELECT"
        if columns:
            self.columns.extend(self._safe_ident(c) for c in columns)
        else:
            self.columns.clear()
        return self

    def where(self, condition: str, *params: Any) -> "QueryBuilder":
        """Add WHERE condition with parameters."""
        self.conditions.append(condition)
        self.parameters.extend(params)
        return self

    def join(self, table: str, on_condition: str) -> "QueryBuilder":
        """Add INNER JOIN."""
        self.joins.append(f"INNER JOIN {table} ON {on_condition}")
        return self

    def left_join(self, table: str, on_condition: str) -> "QueryBuilder":
        """Add LEFT JOIN."""
        self.joins.append(f"LEFT JOIN {table} ON {on_condition}")
        return self

    def group_by(self, *columns: str) -> "QueryBuilder":
        """Add GROUP BY clause."""
        self._group_by.extend(columns)
        return self

    def having(self, condition: str, *params: Any) -> "QueryBuilder":
        """Add HAVING clause."""
        self._having.append(condition)
        self.parameters.extend(params)
        return self

    def order_by(self, column: str, direction: str = "ASC") -> "QueryBuilder":
        """Add ORDER BY clause."""
        self._order_by.append(f"{self._safe_ident(column)} {self._safe_direction(direction)}")
        return self

    def limit(self, count: int) -> "QueryBuilder":
        """Add LIMIT clause."""
        self.limit_value = count
        return self

    def offset(self, count: int) -> "QueryBuilder":
        """Add OFFSET clause."""
        self.offset_value = count
        return self

    # ------------------------------------------------------------------
    # Data manipulation operations
    # ------------------------------------------------------------------
    def insert(self, **values: Any) -> "QueryBuilder":
        """Build INSERT query."""
        self.query_type = "INSERT"
        self.values = values
        return self

    def update(self, **values: Any) -> "QueryBuilder":
        """Build UPDATE query."""
        self.query_type = "UPDATE"
        self.values = values
        return self

    def delete(self) -> "QueryBuilder":
        """Build DELETE query."""
        self.query_type = "DELETE"
        return self

    # ------------------------------------------------------------------
    # Build helpers
    # ------------------------------------------------------------------
    def build(self) -> Tuple[str, Tuple[Any, ...]]:
        """Build final SQL query with parameters."""
        if self.query_type == "SELECT":
            return self._build_select()
        if self.query_type == "INSERT":
            return self._build_insert()
        if self.query_type == "UPDATE":
            return self._build_update()
        if self.query_type == "DELETE":
            return self._build_delete()
        raise ValueError("No query type specified")

    # Estado mutável pode vazar entre builds; oferecemos reset explícito
    def reset(self) -> "QueryBuilder":
        """Limpa estado interno para construção de novo comando."""
        self.query_type = None
        self.columns.clear()
        self.conditions.clear()
        self.joins.clear()
        self._order_by.clear()
        self._group_by.clear()
        self._having.clear()
        self.limit_value = None
        self.offset_value = None
        self.values.clear()
        self.parameters.clear()
        return self

    # Internal builders -------------------------------------------------
    def _build_select(self) -> Tuple[str, Tuple[Any, ...]]:
        """Build SELECT query."""
        columns = ", ".join(self.columns) if self.columns else "*"
        query = f"SELECT {columns} FROM {self.table}"

        if self.joins:
            query += " " + " ".join(self.joins)

        if self.conditions:
            query += " WHERE " + " AND ".join(self.conditions)

        if self._group_by:
            query += " GROUP BY " + ", ".join(self._group_by)

        if self._having:
            query += " HAVING " + " AND ".join(self._having)

        if self._order_by:
            query += " ORDER BY " + ", ".join(self._order_by)

        if self.limit_value is not None:
            query += f" LIMIT {self.limit_value}"

        if self.offset_value is not None:
            query += f" OFFSET {self.offset_value}"

        return query, tuple(self.parameters)

    def _build_insert(self) -> Tuple[str, Tuple[Any, ...]]:
        """Build INSERT query."""
        if not self.values:
            raise ValueError("No values provided for INSERT")
        columns = ", ".join(self.values.keys())
        placeholders = ", ".join(["?"] * len(self.values))
        query = f"INSERT INTO {self.table} ({columns}) VALUES ({placeholders})"
        params = tuple(self.values.values())
        return query, params

    def _build_update(self) -> Tuple[str, Tuple[Any, ...]]:
        """Build UPDATE query."""
        if not self.values:
            raise ValueError("No values provided for UPDATE")
        set_clause = ", ".join(f"{col} = ?" for col in self.values.keys())
        query = f"UPDATE {self.table} SET {set_clause}"
        params: List[Any] = list(self.values.values())

        if self.conditions:
            query += " WHERE " + " AND ".join(self.conditions)
            params.extend(self.parameters)

        return query, tuple(params)

    def _build_delete(self) -> Tuple[str, Tuple[Any, ...]]:
        """Build DELETE query."""
        query = f"DELETE FROM {self.table}"
        if self.conditions:
            query += " WHERE " + " AND ".join(self.conditions)
        return query, tuple(self.parameters)


# ----------------------------------------------------------------------
# Specialized builders
# ----------------------------------------------------------------------


class ProjectQueryBuilder(QueryBuilder):
    """Specialized query builder for projects."""

    def __init__(self) -> None:
        super().__init__("framework_projects")


    def active_only(self) -> "ProjectQueryBuilder":
        """Filter only active projects."""
        return self.where("status = ?", "active")

    def with_epic_stats(self) -> "ProjectQueryBuilder":
        """Include epic statistics."""
        return (
            self.left_join(
                "framework_epics e", "framework_projects.id = e.project_id"
            )
            .select(
                "framework_projects.*",
                "COUNT(e.id) as epic_count",
                "SUM(CASE WHEN e.status = 'completed' THEN 1 ELSE 0 END) as completed_epics",
            )
            .group_by("framework_projects.id")
        )


class EpicQueryBuilder(QueryBuilder):
    """Specialized query builder for epics."""

    def __init__(self) -> None:
        super().__init__("framework_epics")

    def for_project(self, project_id: int) -> "EpicQueryBuilder":
        """Filter epics for specific project."""
        return self.where("project_id = ?", project_id)

    def by_status(self, status: str) -> "EpicQueryBuilder":
        """Filter by status."""
        return self.where("status = ?", status)

    def with_task_stats(self) -> "EpicQueryBuilder":
        """Include task statistics."""
        return (
            self.left_join(
                "framework_tasks t", "framework_epics.id = t.epic_id"
            )
            .select(
                "framework_epics.*",
                "COUNT(t.id) as task_count",
                "SUM(CASE WHEN t.status = 'completed' THEN 1 ELSE 0 END) as completed_tasks",
            )
            .group_by("framework_epics.id")
        )


class TaskQueryBuilder(QueryBuilder):
    """Specialized query builder for tasks."""

    def __init__(self) -> None:
        super().__init__("framework_tasks")

    def for_epic(self, epic_id: int) -> "TaskQueryBuilder":
        """Filter tasks for specific epic."""
        return self.where("epic_id = ?", epic_id)

    def by_status(self, status: str) -> "TaskQueryBuilder":
        """Filter by status."""
        return self.where("status = ?", status)

    def by_tdd_phase(self, phase: str) -> "TaskQueryBuilder":
        """Filter by TDD phase."""
        return self.where("tdd_phase = ?", phase)

    def with_epic_info(self) -> "TaskQueryBuilder":
        """Include epic information."""
        return (
            self.left_join(
                "framework_epics e", "framework_tasks.epic_id = e.id"
            )
            .select(
                "framework_tasks.*",
                "e.name as epic_name",
                "e.project_id as project_id",
            )
        )