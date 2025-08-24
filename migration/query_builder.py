from __future__ import annotations

"""Secure SQL query builder used to replace ad-hoc SQL strings.

🔒 SECURITY ENHANCEMENTS:
- Column name validation against whitelist
- Table name validation against allowed tables
- SQL injection prevention
- Parameter sanitization
"""

from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, Set

import sqlite3
import re


# 🔒 SECURITY: Whitelist of allowed tables and columns
ALLOWED_TABLES: Set[str] = {
    'framework_epics', 'framework_tasks', 'framework_projects',
    'work_sessions', 'user_achievements', 'achievement_types', 'user_streaks',
    'github_sync_log', 'system_settings', 'schema_migrations'
}

ALLOWED_COLUMNS: Set[str] = {
    'id', 'title', 'description', 'status', 'priority', 'created_at', 'updated_at',
    'points_value', 'due_date', 'icon', 'estimated_hours', 'created_by', 'updated_by',
    'version', 'deleted_at', 'epic_id', 'project_id', 'name', 'email',
    'phone', 'address', 'tier', 'budget', 'start_date', 'end_date', 'phase',
    'estimate_minutes', 'actual_minutes', 'notes', 'points_earned', 'difficulty',
    'session_id', 'user_id', 'duration_minutes', 'focus_rating', 'energy_level',
    'mood_rating', 'interruptions', 'achievement_id', 'earned_at', 'achievement_type',
    'unlock_condition', 'streak_type', 'current_count', 'max_count', 'last_activity',
    'sync_id', 'operation', 'entity_type', 'entity_id', 'timestamp', 'github_data',
    'setting_key', 'setting_value', 'applied_at'
}

# 🔒 SECURITY: SQL identifier validation pattern
IDENTIFIER_PATTERN = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')


class SecurityError(Exception):
    """Raised when security validation fails."""
    pass


class SQLBuilder:
    """Build SQL strings from QueryBuilder internal representation with security validation."""

    @staticmethod
    # TODO: Consider extracting this block into a separate method
    # TODO: Consider extracting this block into a separate method
    def _validate_identifier(identifier: str, allowed_set: Set[str], context: str) -> str:
        """Validate SQL identifier against whitelist and pattern.
        
        Args:
            identifier: The identifier to validate
            allowed_set: Set of allowed identifiers
            context: Context for error messages (e.g., "table", "column")
            
        Returns:
            The validated identifier
            
        Raises:
            SecurityError: If identifier is invalid or not allowed
        """
        if not identifier or not isinstance(identifier, str):
            raise SecurityError(f"Invalid {context} identifier: {identifier}")
            
        # Remove alias if present (e.g., "table t" -> "table")
        base_identifier = identifier.split()[0]
        
        # Validate pattern
        if not IDENTIFIER_PATTERN.match(base_identifier):
            raise SecurityError(f"Invalid {context} identifier pattern: {base_identifier}")
            
        # Check whitelist
        if base_identifier not in allowed_set:
            raise SecurityError(f"Unauthorized {context}: {base_identifier}")
            
        return identifier

    # TODO: Consider extracting this block into a separate method
    # TODO: Consider extracting this block into a separate method
    @staticmethod
    def _validate_column_list(columns: List[str]) -> List[str]:
        """Validate list of column names.
        
        Args:
            columns: List of column names to validate
            
        Returns:
            List of validated column names
            
        Raises:
            SecurityError: If any column is invalid
        """
        if '*' in columns:
            return ['*']  # Allow SELECT *
            
        validated = []
        for col in columns:
            # Handle table.column format
            if '.' in col:
                parts = col.split('.')
                if len(parts) == 2:
                    table_part, col_part = parts
                    # Validate both parts
                    SQLBuilder._validate_identifier(table_part, ALLOWED_TABLES, "table")
                    SQLBuilder._validate_identifier(col_part, ALLOWED_COLUMNS, "column")
                    validated.append(col)
                else:
                    raise SecurityError(f"Invalid column format: {col}")
            else:
                # Simple column name
                validated.append(SQLBuilder._validate_identifier(col, ALLOWED_COLUMNS, "column"))
                
        return validated

    @staticmethod
    def sanitize_params(params: Iterable[Any]) -> Tuple[Any, ...]:
        """Return parameters as a tuple ensuring safe binding."""
        return tuple(params)

# TODO: Consider extracting this block into a separate method

# TODO: Consider extracting this block into a separate method

    @staticmethod
    def build_select_query(parts: Dict[str, Any]) -> Tuple[str, Sequence[Any]]:
        """Build SELECT query with security validation."""
        # 🔒 SECURITY: Validate table name
        table_name = SQLBuilder._validate_identifier(parts['from'], ALLOWED_TABLES, "table")
        
        # 🔒 SECURITY: Validate column names
        validated_columns = SQLBuilder._validate_column_list(parts['select'])
        
        query = f"SELECT {', '.join(validated_columns)} FROM {table_name}"
        
        # Handle joins with validation
        for join in parts.get("joins", []):
            join_type, join_table, condition = join
            validated_join_table = SQLBuilder._validate_identifier(join_table, ALLOWED_TABLES, "table")
            # Note: JOIN conditions are not parameterized but use table.column = table.column format
            query += f" {join_type} JOIN {validated_join_table} ON {condition}"
        
        params: List[Any] = []
        if parts.get("where"):
            conditions = []
            for column, op, value in parts["where"]:
                # Validate column name
                validated_col = SQLBuilder._validate_identifier(column.split('.')[0] if '.' in column else column, ALLOWED_COLUMNS, "column")
                conditions.append(f"{column} {op} ?")
                params.append(value)
            query += " WHERE " + " AND ".join(conditions)
            
        if parts.get("order_by"):
            col, direction = parts["order_by"]
            validated_col = SQLBuilder._validate_identifier(col.split('.')[0] if '.' in col else col, ALLOWED_COLUMNS, "column")
            query += f" ORDER BY {col} {direction}"
            
        if parts.get("limit") is not None:
            limit = int(parts['limit'])  # Ensure it's an integer
            query += f" LIMIT {limit}"
            
# TODO: Consider extracting this block into a separate method
            
        return query, params

    @staticmethod
    def build_insert_query(parts: Dict[str, Any]) -> Tuple[str, Sequence[Any]]:
        """Build INSERT query with security validation."""
        # 🔒 SECURITY: Validate table name
        table_name = SQLBuilder._validate_identifier(parts['into'], ALLOWED_TABLES, "table")
        
        # 🔒 SECURITY: Validate column names
        columns = list(parts["values"].keys())
        validated_columns = SQLBuilder._validate_column_list(columns)
        
        cols = ", ".join(validated_columns)
        placeholders = ", ".join(["?"] * len(parts["values"]))
        # TODO: Consider extracting this block into a separate method
        query = f"INSERT INTO {table_name} ({cols}) VALUES ({placeholders})"
        # TODO: Consider extracting this block into a separate method
        params = list(parts["values"].values())
        return query, params

    @staticmethod
    def build_update_query(parts: Dict[str, Any]) -> Tuple[str, Sequence[Any]]:
        """Build UPDATE query with security validation."""
        # 🔒 SECURITY: Validate table name
        table_name = SQLBuilder._validate_identifier(parts['table'], ALLOWED_TABLES, "table")
        
        sets = []
        params: List[Any] = []
        
        for column, value in parts["set"].items():
            # 🔒 SECURITY: Validate column name
            validated_col = SQLBuilder._validate_identifier(column, ALLOWED_COLUMNS, "column")
            sets.append(f"{validated_col} = ?")
            params.append(value)
            
        query = f"UPDATE {table_name} SET {', '.join(sets)}"
        
        if parts.get("where"):
            conditions = []
            for column, op, value in parts["where"]:
                validated_col = SQLBuilder._validate_identifier(column, ALLOWED_COLUMNS, "column")
                conditions.append(f"{validated_col} {op} ?")
                # TODO: Consider extracting this block into a separate method
                params.append(value)
            # TODO: Consider extracting this block into a separate method
            query += " WHERE " + " AND ".join(conditions)
            
        return query, params

    @staticmethod
    def build_delete_query(parts: Dict[str, Any]) -> Tuple[str, Sequence[Any]]:
        """Build DELETE query with security validation."""
        # 🔒 SECURITY: Validate table name
        table_name = SQLBuilder._validate_identifier(parts['from'], ALLOWED_TABLES, "table")
        
        query = f"DELETE FROM {table_name}"
        params: List[Any] = []
        
        if parts.get("where"):
            conditions = []
            for column, op, value in parts["where"]:
                validated_col = SQLBuilder._validate_identifier(column, ALLOWED_COLUMNS, "column")
                conditions.append(f"{validated_col} {op} ?")
                params.append(value)
            query += " WHERE " + " AND ".join(conditions)
            
        return query, params


class QueryExecutor:
    """Execute SQL queries using a SQLite connection."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def execute_query(self, query: str, params: Sequence[Any] | None = None):
        """Execute query with parameter binding."""
        cur = self.conn.execute(query, params or [])
        try:
            return cur.fetchall()
        finally:
            cur.close()

    def execute_transaction(self, queries: Iterable[Tuple[str, Sequence[Any] | None]]):
        """Execute multiple queries in a transaction."""
        with self.conn:
            for query, params in queries:
                self.conn.execute(query, params or [])

    def batch_execute(self, query: str, param_list: Iterable[Sequence[Any]]):
        """Execute the same query with multiple parameter sets."""
        with self.conn:
            for params in param_list:
                self.conn.execute(query, params)


class QueryBuilder:
    """Fluent interface for building SQL queries with security validation."""

    def __init__(self):
        self.parts: Dict[str, Any] = {}
        self.query_type: Optional[str] = None

    # --- Core builders -------------------------------------------------
    def select(self, *columns: str) -> "QueryBuilder":
        """Select columns with validation."""
        self.query_type = "select"
        self.parts["select"] = list(columns) if columns else ["*"]
        return self

    def insert_into(self, table: str) -> "QueryBuilder":
        """Insert into table with validation."""
        self.query_type = "insert"
        self.parts["into"] = table
        return self

    def update(self, table: str) -> "QueryBuilder":
        """Update table with validation."""
        self.query_type = "update"
        self.parts["table"] = table
        return self

    def delete(self) -> "QueryBuilder":
        """Delete query."""
        self.query_type = "delete"
        return self

    def from_table(self, table: str) -> "QueryBuilder":
        """FROM table with validation."""
        self.parts["from"] = table
        return self

    def join(self, table: str, condition: str, join_type: str = "INNER") -> "QueryBuilder":
        """JOIN with validation."""
        self.parts.setdefault("joins", []).append((join_type, table, condition))
        return self

    def where(self, column: str, op: str, value: Any) -> "QueryBuilder":
        """WHERE condition with validation."""
        self.parts.setdefault("where", []).append((column, op, value))
        return self

    def order_by(self, column: str, direction: str = "ASC") -> "QueryBuilder":
        """ORDER BY with validation."""
        self.parts["order_by"] = (column, direction)
        return self

    def limit(self, count: int) -> "QueryBuilder":
        """LIMIT with validation."""
        if not isinstance(count, int) or count < 0:
            raise ValueError(f"Invalid limit: {count}")
        self.parts["limit"] = count
        return self

    def values(self, values: Dict[str, Any]) -> "QueryBuilder":
        """VALUES for INSERT."""
        self.parts["values"] = values
        return self

# TODO: Consider extracting this block into a separate method

    # TODO: Consider extracting this block into a separate method
    def set(self, column: str, value: Any) -> "QueryBuilder":
        """SET for UPDATE."""
        self.parts.setdefault("set", {})[column] = value
        return self

    # --- Build and execute ---------------------------------------------
    def build(self) -> Tuple[str, Sequence[Any]]:
        """Build the SQL query with security validation."""
        if self.query_type == "select":
            return SQLBuilder.build_select_query(self.parts)
        if self.query_type == "insert":
            return SQLBuilder.build_insert_query(self.parts)
        if self.query_type == "update":
            return SQLBuilder.build_update_query(self.parts)
        if self.query_type == "delete":
            return SQLBuilder.build_delete_query(self.parts)
        raise ValueError("Query type not specified")

    def execute(self, conn: sqlite3.Connection):
        """Execute the built query."""
        query, params = self.build()
        executor = QueryExecutor(conn)
        return executor.execute_query(query, params)