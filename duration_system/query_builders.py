#!/usr/bin/env python3
"""
Secure Query Builder System
Replaces ad-hoc SQL strings with parameterized, secure query builders.
"""

from __future__ import annotations

from typing import Dict, List, Any, Optional, Union, Tuple, Set
from enum import Enum
from dataclasses import dataclass
import re


class QueryType(Enum):
    """Query operation types."""
    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


class JoinType(Enum):
    """SQL join types."""
    INNER = "INNER JOIN"
    LEFT = "LEFT JOIN"
    RIGHT = "RIGHT JOIN"
    FULL = "FULL OUTER JOIN"


@dataclass
class QueryCondition:
    """Represents a WHERE condition."""
    field: str
    operator: str  # =, !=, >, <, >=, <=, LIKE, IN, NOT IN
    value: Any
    logical_op: str = "AND"  # AND, OR

    def to_sql(self) -> Tuple[str, Any]:
        """Convert condition to SQL with parameter."""
        op = self.operator.upper()
        if op in {"IN", "NOT IN"}:
            seq = list(self.value) if isinstance(self.value, (list, tuple, set)) else []
            if not seq:
                # Empty IN: nunca casa; Empty NOT IN: sempre casa
                return ("1=0", []) if op == "IN" else ("1=1", [])
            placeholders = ",".join("?" for _ in seq)
            clause = f"{self.field} {'NOT IN' if op == 'NOT IN' else 'IN'} ({placeholders})"
            return clause, list(seq)
        else:
            return f"{self.field} {self.operator} ?", [self.value]


@dataclass
class QueryJoin:
    """Represents a table join."""
    table: str
    join_type: JoinType
    on_condition: str


class SecureQueryBuilder:
    """Secure SQL query builder with parameter binding and validation."""

    allowed_operators = {"=", "!=", ">", "<", ">=", "<=", "LIKE", "IN", "NOT IN"}

    def __init__(self, table: str, allowed_fields: Optional[Set[str]] = None):
        """Initialize query builder for specific table."""
        self.table = table
        self.query_type: Optional[QueryType] = None
        self.select_fields: List[str] = []
        self.conditions: List[QueryCondition] = []
        self.joins: List[QueryJoin] = []
        self.order_by_fields: List[str] = []
        self.group_by_fields: List[str] = []
        self.limit_value: Optional[int] = None
        self.offset_value: Optional[int] = None
        self.insert_data: Dict[str, Any] = {}
        self.update_data: Dict[str, Any] = {}
        self._allowed_fields = allowed_fields

    # ------------------------------------------------------------------
    # Helper validation methods
    def _validate_field(self, field: str) -> None:
        if self._allowed_fields is not None and field not in self._allowed_fields:
            raise ValueError(f"Field {field} not allowed")
        # Basic regex validation to avoid injection through field names
        if not re.match(r"^[A-Za-z0-9_\.]+$", field):
            raise ValueError(f"Invalid field name: {field}")

    def _validate_operator(self, operator: str) -> None:
        if operator not in self.allowed_operators:
            raise ValueError(f"Operator {operator} not allowed")

    def _validate_on_condition(self, on_condition: str) -> None:
        """Validate simple ON condition pattern like 'a.b = c.d'."""
        if not re.match(r"^[A-Za-z0-9_\.]+\s*=\s*[A-Za-z0-9_\.]+$", on_condition):
            raise ValueError(f"Invalid join condition: {on_condition}")

    # ------------------------------------------------------------------
    # Query construction methods
    def select(self, *fields: str) -> "SecureQueryBuilder":
        """Add SELECT fields."""
        self.query_type = QueryType.SELECT
        if fields:
            for field in fields:
                self._validate_field(field)
            self.select_fields.extend(fields)
        else:
            self.select_fields = ["*"]
        return self

    def insert(self, data: Dict[str, Any]) -> "SecureQueryBuilder":
        """Set INSERT data."""
        self.query_type = QueryType.INSERT
        self.insert_data = data
        return self

    def update(self, data: Dict[str, Any]) -> "SecureQueryBuilder":
        """Set UPDATE data."""
        self.query_type = QueryType.UPDATE
        self.update_data = data
        return self

    def delete(self) -> "SecureQueryBuilder":
        """Set DELETE operation."""
        self.query_type = QueryType.DELETE
        return self

    def where(
        self,
        field: str,
        operator: str,
        value: Any,
        logical_op: str = "AND",
    ) -> "SecureQueryBuilder":
        """Add WHERE condition with validation."""
        self._validate_field(field)
        self._validate_operator(operator)
        condition = QueryCondition(field, operator, value, logical_op)
        self.conditions.append(condition)
        return self

    def where_in(self, field: str, values: List[Any]) -> "SecureQueryBuilder":
        """Add WHERE IN condition."""
        return self.where(field, "IN", values)

    def where_like(self, field: str, pattern: str) -> "SecureQueryBuilder":
        """Add WHERE LIKE condition."""
        return self.where(field, "LIKE", pattern)

    def join(
        self,
        table: str,
        on_condition: str,
        join_type: JoinType = JoinType.INNER,
    ) -> "SecureQueryBuilder":
        """Add table join."""
        self._validate_field(table)
        self._validate_on_condition(on_condition)
        self.joins.append(QueryJoin(table, join_type, on_condition))
        return self

    def left_join(self, table: str, on_condition: str) -> "SecureQueryBuilder":
        """Add LEFT JOIN."""
        return self.join(table, on_condition, JoinType.LEFT)

    def order_by(self, field: str, direction: str = "ASC") -> "SecureQueryBuilder":
        """Add ORDER BY clause."""
        self._validate_field(field)
        direction_upper = direction.upper()
        if direction_upper not in {"ASC", "DESC"}:
            raise ValueError(f"Invalid ORDER BY direction: {direction}")
        self.order_by_fields.append(f"{field} {direction_upper}")
        return self

    def group_by(self, field: str) -> "SecureQueryBuilder":
        """Add GROUP BY clause."""
        self._validate_field(field)
        self.group_by_fields.append(field)
        return self

    def limit(self, count: int) -> "SecureQueryBuilder":
        """Add LIMIT clause."""
        if not isinstance(count, int) or count < 0:
            raise ValueError("LIMIT must be a non-negative integer")
        self.limit_value = count
        return self

    def offset(self, count: int) -> "SecureQueryBuilder":
        """Add OFFSET clause."""
        if not isinstance(count, int) or count < 0:
            raise ValueError("OFFSET must be a non-negative integer")
        self.offset_value = count
        return self

    def build(self) -> Tuple[str, List[Any]]:
        """Build final SQL query with parameters and complexity checks."""
        if len(self.joins) > 5:
            raise ValueError("Too many joins in query")
        if len(self.conditions) > 20:
            raise ValueError("Too many conditions in query")

        if self.query_type == QueryType.SELECT:
            return self._build_select()
        if self.query_type == QueryType.INSERT:
            return self._build_insert()
        if self.query_type == QueryType.UPDATE:
            return self._build_update()
        if self.query_type == QueryType.DELETE:
            return self._build_delete()
        raise ValueError("Query type not set")

    def _build_select(self) -> Tuple[str, List[Any]]:
        """Build SELECT query."""
        query_parts = [f"SELECT {', '.join(self.select_fields)}"]
        query_parts.append(f"FROM {self.table}")
        params: List[Any] = []

        for join in self.joins:
            query_parts.append(f"{join.join_type.value} {join.table} ON {join.on_condition}")

        if self.conditions:
            where_parts: List[str] = []
            for i, condition in enumerate(self.conditions):
                sql_part, condition_params = condition.to_sql()
                if i > 0:
                    where_parts.append(condition.logical_op)
                where_parts.append(sql_part)
                params.extend(
                    condition_params if isinstance(condition_params, list) else [condition_params]
                )
            query_parts.append("WHERE " + " ".join(where_parts))

        if self.group_by_fields:
            query_parts.append(f"GROUP BY {', '.join(self.group_by_fields)}")

        if self.order_by_fields:
            query_parts.append(f"ORDER BY {', '.join(self.order_by_fields)}")

        if self.limit_value is not None:
            query_parts.append(f"LIMIT {self.limit_value}")
            if self.offset_value is not None:
                query_parts.append(f"OFFSET {self.offset_value}")

        return " ".join(query_parts), params

    def _build_insert(self) -> Tuple[str, List[Any]]:
        """Build INSERT query."""
        fields = list(self.insert_data.keys())
        for f in fields:
            self._validate_field(f)
        placeholders = ",".join("?" for _ in fields)
        query = f"INSERT INTO {self.table} ({', '.join(fields)}) VALUES ({placeholders})"
        params = list(self.insert_data.values())
        return query, params

    def _build_update(self) -> Tuple[str, List[Any]]:
        """Build UPDATE query."""
        for f in self.update_data.keys():
            self._validate_field(f)
        set_parts = [f"{field} = ?" for field in self.update_data.keys()]
        query_parts = [f"UPDATE {self.table}", f"SET {', '.join(set_parts)}"]
        params = list(self.update_data.values())

        if self.conditions:
            where_parts: List[str] = []
            for i, condition in enumerate(self.conditions):
                sql_part, condition_params = condition.to_sql()
                if i > 0:
                    where_parts.append(condition.logical_op)
                where_parts.append(sql_part)
                params.extend(
                    condition_params if isinstance(condition_params, list) else [condition_params]
                )
            query_parts.append("WHERE " + " ".join(where_parts))

        return " ".join(query_parts), params

    def _build_delete(self) -> Tuple[str, List[Any]]:
        """Build DELETE query."""
        query_parts = [f"DELETE FROM {self.table}"]
        params: List[Any] = []

        if self.conditions:
            where_parts: List[str] = []
            for i, condition in enumerate(self.conditions):
                sql_part, condition_params = condition.to_sql()
                if i > 0:
                    where_parts.append(condition.logical_op)
                where_parts.append(sql_part)
                params.extend(
                    condition_params if isinstance(condition_params, list) else [condition_params]
                )
            query_parts.append("WHERE " + " ".join(where_parts))

        return " ".join(query_parts), params


class EpicQueryBuilder(SecureQueryBuilder):
    """Specialized query builder for epics with common operations."""

    def __init__(self):
        super().__init__("framework_epics")

    def with_client_info(self) -> "EpicQueryBuilder":
        """Join with client information."""
        self.left_join(
            "framework_clients",
            "framework_epics.client_id = framework_clients.id",
        )
        return self

    def with_project_info(self) -> "EpicQueryBuilder":
        """Join with project information."""
        self.left_join(
            "framework_projects",
            "framework_epics.project_id = framework_projects.id",
        )
        return self

    def active_only(self) -> "EpicQueryBuilder":
        """Filter to active epics only."""
        self.where("status", "!=", "archived")
        return self

    def by_client(self, client_id: int) -> "EpicQueryBuilder":
        """Filter by client ID."""
        self.where("client_id", "=", client_id)
        return self

    def with_points_range(self, min_points: int, max_points: int) -> "EpicQueryBuilder":
        """Filter by points range."""
        self.where("points_value", ">=", min_points)
        self.where("points_value", "<=", max_points)
        return self


class TaskQueryBuilder(SecureQueryBuilder):
    """Specialized query builder for tasks."""

    def __init__(self):
        super().__init__("framework_tasks")

    def with_epic_info(self) -> "TaskQueryBuilder":
        """Join with epic information."""
        self.left_join(
            "framework_epics",
            "framework_tasks.epic_id = framework_epics.id",
        )
        return self

    def by_tdd_phase(self, phase: str) -> "TaskQueryBuilder":
        """Filter by TDD phase."""
        self.where("tdd_phase", "=", phase)
        return self

    def by_status(self, status: str) -> "TaskQueryBuilder":
        """Filter by task status."""
        self.where("status", "=", status)
        return self

    def recent_tasks(self, days: int = 7) -> "TaskQueryBuilder":
        """Filter to recent tasks."""
        self.where("created_at", ">=", f"datetime('now', '-{days} days')")
        return self


# Factory functions for convenience
def query_epics() -> EpicQueryBuilder:
    """Create epic query builder."""
    return EpicQueryBuilder()


def query_tasks() -> TaskQueryBuilder:
    """Create task query builder."""
    return TaskQueryBuilder()


def query_table(table_name: str) -> SecureQueryBuilder:
    """Create generic query builder for any table."""
    return SecureQueryBuilder(table_name)


__all__ = [
    "SecureQueryBuilder",
    "EpicQueryBuilder",
    "TaskQueryBuilder",
    "QueryType",
    "JoinType",
    "QueryCondition",
    "query_epics",
    "query_tasks",
    "query_table",
]
